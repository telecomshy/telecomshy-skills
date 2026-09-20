#!/usr/bin/env python3
"""优化技能 description 的触发准确率。

把评测集按 should_trigger 分层切成 train / held-out test，给当前 description 打分，
并给出改进建议。**选优按 test 分**（防过拟合）。

真实触发判定有两种模式：
    --runner heuristic   离线关键词/汉字二元组重叠启发式（默认，无需 agent）
    --runner opencode|teleagent|cmd   真跑 agent，用 agent_runner 检测技能是否被触发

脚本本身不重写 description（那需要 LLM）。循环由 agent 驱动：
提出新 description → 用 ``--description`` 评估 → 比较 test 分 → 保留更高者。

**每条查询默认跑 ``--trials 3`` 次、按触发率 ≥ 0.5 判"是否触发"**——真跑 agent 时单次判定有抖动，
单跑会把噪声当结论（heuristic 无随机性，强制 1 次）。

用法:
    python optimize_description.py <skill_dir> --eval-set evals/evals.json
    python optimize_description.py <skill_dir> --eval-set evals/evals.json --runner opencode --detect my-skill --trials 3
    python optimize_description.py <skill_dir> --eval-set evals/evals.json --description "候选描述" --previous reports/desc-opt.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from agent_runner import resolve_command, run_prompt
from skill_utils import force_utf8_stdio, load_skill, merge_evidence, read_text, write_text

_ASCII_WORD = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
_CJK_CHAR = re.compile(r"[\u3400-\u9fff]")


def split_eval_set(
    evals: list[dict[str, Any]],
    train_ratio: float = 0.6,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """按 should_trigger 分层切分 train/test；样本足够时尽量让两边都有正负例。"""
    rng = random.Random(seed)
    positives = [e for e in evals if e.get("should_trigger", True)]
    negatives = [e for e in evals if not e.get("should_trigger", True)]
    rng.shuffle(positives)
    rng.shuffle(negatives)

    def split(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        idx = max(1, int(len(items) * train_ratio)) if items else 0
        return items[:idx], items[idx:]

    train_p, test_p = split(positives)
    train_n, test_n = split(negatives)
    return train_p + train_n, test_p + test_n


def _tokens(text: str) -> set[str]:
    text = (text or "").lower()
    words = set(_ASCII_WORD.findall(text))
    chars = _CJK_CHAR.findall(text)
    bigrams = {chars[i] + chars[i + 1] for i in range(len(chars) - 1)}
    return words | bigrams


def heuristic_predict(description: str, prompt: str, threshold: float = 0.15) -> bool:
    prompt_tokens = _tokens(prompt)
    if not prompt_tokens:
        return False
    overlap = _tokens(description) & prompt_tokens
    return (len(overlap) / len(prompt_tokens)) > threshold


def build_predictor(
    description: str,
    runner: str,
    cmd: str | None,
    detect: str | None,
    cwd: str | None,
    timeout: int,
    isolate_cwd: bool = False,
    detect_mode: str = "auto",
) -> tuple[Callable[[str], bool | None], str]:
    """返回 (predict_fn, mode)；predict_fn 返回 True/False，或 None 表示无法判定。

    ``isolate_cwd``：每次运行都在 ``cwd`` 下新建一个空目录并跑完即删——
    agent 会写文件，共享目录会被历次运行污染，让后跑的用例结果失真。
    """
    if runner != "heuristic" and resolve_command(runner, cmd):
        def predict(prompt: str) -> bool | None:
            run_cwd = cwd
            tmp_dir: str | None = None
            if isolate_cwd and cwd:
                tmp_dir = tempfile.mkdtemp(prefix="run-", dir=cwd)
                run_cwd = tmp_dir
            try:
                result = run_prompt(
                    prompt, runner=runner, cmd=cmd,
                    detect_pattern=detect, cwd=run_cwd, timeout=timeout,
                    detect_mode=detect_mode,
                )
                return result.get("triggered")
            finally:
                if tmp_dir:
                    shutil.rmtree(tmp_dir, ignore_errors=True)

        return predict, f"agent:{runner}"

    def predict(prompt: str) -> bool | None:
        return heuristic_predict(description, prompt)

    return predict, "heuristic"


def score(
    description: str,
    eval_set: list[dict[str, Any]],
    predict: Callable[[str], bool | None],
    split: str = "",
    trials: int = 1,
    workers: int = 1,
    verbose: bool = False,
) -> dict[str, Any]:
    """每条查询跑 ``trials`` 次，按触发率 ≥ 0.5 判"是否触发"。

    真跑 agent 时单次判定有抖动（同一 description 换一次跑，误触发的题会变），
    故规范要求**每条 ≥3 次取多数**；heuristic 无随机性，``trials`` 由上层强制为 1。
    ``workers > 1`` 时并发跑各 (查询, trial)——每次预测一个独立子进程，互不共享状态。
    """
    n = max(1, trials)
    jobs = [(i, t, item.get("prompt", "")) for i, item in enumerate(eval_set) for t in range(n)]
    outcomes: dict[tuple[int, int], bool | None] = {}

    def _run(i: int, t: int, prompt: str) -> tuple[tuple[int, int], bool | None]:
        try:
            return (i, t), predict(prompt)
        except Exception:  # noqa: BLE001 - 单次失败按"未判定"计
            return (i, t), None

    if workers > 1 and len(jobs) > 1:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(_run, i, t, p) for i, t, p in jobs]
            for fut in as_completed(futures):
                key, value = fut.result()
                outcomes[key] = value
                if verbose:
                    item = eval_set[key[0]]
                    print(f"[{split or 'eval'}] done #{item.get('eval_id')} "
                          f"trial {key[1] + 1}/{n}", file=sys.stderr)
    else:
        for i, t, p in jobs:
            key, value = _run(i, t, p)
            outcomes[key] = value
            if verbose:
                item = eval_set[i]
                print(f"[{split or 'eval'}] done #{item.get('eval_id')} "
                      f"trial {t + 1}/{n}", file=sys.stderr)

    details: list[dict[str, Any]] = []
    correct = 0
    for i, item in enumerate(eval_set):
        should = bool(item.get("should_trigger", True))
        hits = 0
        decided = 0
        for t in range(n):
            p = outcomes.get((i, t))
            if p is None:
                continue
            decided += 1
            if p:
                hits += 1
        if decided == 0:
            rate: float | None = None
            predicted: bool | None = None
        else:
            rate = round(hits / decided, 4)
            predicted = rate >= 0.5
        is_correct = predicted is not None and predicted == should
        if is_correct:
            correct += 1
        details.append({
            "eval_id": item.get("eval_id", 0),
            "prompt": item.get("prompt", ""),
            "should_trigger": should,
            "predicted_trigger": predicted,
            "trigger_rate": rate,
            "trials": decided,
            "correct": is_correct,
            "split": split,
        })
    total = len(eval_set)
    tp = sum(1 for d in details if d["should_trigger"] and d["predicted_trigger"] is True)
    fp = sum(1 for d in details if not d["should_trigger"] and d["predicted_trigger"] is True)
    fn = sum(1 for d in details if d["should_trigger"] and d["predicted_trigger"] is not True)
    tn = sum(1 for d in details if not d["should_trigger"] and d["predicted_trigger"] is not True)
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    accuracy = (tp + tn) / total if total else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "score": round(correct / total, 4) if total else 0.0,
        "correct": correct,
        "total": total,
        "metrics": {
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "accuracy": round(accuracy, 4),
            "f1": round(f1, 4),
        },
        "details": details,
    }


def suggest_improvements(failures: list[dict[str, Any]], description: str) -> list[str]:
    false_negatives = [f for f in failures if f["should_trigger"] and not f["predicted_trigger"]]
    false_positives = [f for f in failures if not f["should_trigger"] and f["predicted_trigger"]]
    suggestions: list[str] = []

    if false_negatives:
        desc_tokens = _tokens(description)
        missing: set[str] = set()
        for fn in false_negatives:
            missing |= {t for t in _tokens(fn["prompt"]) - desc_tokens if len(t) > 1}
        if missing:
            suggestions.append("补充触发词以覆盖漏触发：" + "、".join(sorted(missing)[:10]))
        suggestions.append(f"{len(false_negatives)} 条本应触发的查询被漏掉")
    if false_positives:
        suggestions.append(f"{len(false_positives)} 条不该触发的查询被命中——收窄 description 的适用范围")
    return suggestions


def optimize(
    skill_dir: str,
    eval_set_path: str,
    runner: str = "heuristic",
    cmd: str | None = None,
    detect: str | None = None,
    description_override: str | None = None,
    previous_path: str | None = None,
    seed: int = 42,
    cwd: str | None = None,
    timeout: int = 120,
    trials: int = 3,
    isolate_cwd: bool = False,
    workers: int = 1,
    verbose: bool = False,
    detect_mode: str = "auto",
) -> dict[str, Any]:
    path = Path(skill_dir).resolve()
    frontmatter, _body, errors = load_skill(path)
    if frontmatter is None:
        return {"error": "; ".join(errors) or "Could not parse SKILL.md frontmatter"}

    eval_data = json.loads(read_text(eval_set_path))
    all_evals = eval_data.get("evals", [])
    if not all_evals:
        return {"error": "Eval set is empty"}

    original = str(frontmatter.get("description", ""))
    candidate = description_override if description_override is not None else original
    if runner != "heuristic" and candidate.strip() != original.strip():
        return {
            "error": (
                "agent 模式不读取 --description：技能由客户端加载，候选描述不会生效。"
                "请先把候选描述部署到 SKILL.md（或临时替换）再跑，或改用 --runner heuristic。"
            )
        }

    train_set, test_set = split_eval_set(all_evals, seed=seed)
    predict, mode = build_predictor(candidate, runner, cmd, detect, cwd, timeout,
                                    isolate_cwd, detect_mode)

    if runner == "heuristic":
        trials = 1  # heuristic 无随机性，重复无意义

    train_result = score(candidate, train_set, predict, "train", trials=trials,
                         workers=workers, verbose=verbose)
    test_result = score(candidate, test_set, predict, "test", trials=trials,
                        workers=workers, verbose=verbose)

    train_failures = [d for d in train_result["details"] if not d["correct"]]
    test_failures = [d for d in test_result["details"] if not d["correct"]]
    # 改进建议只用 train 的失败：用 test 的失败去改措辞 = 把描述过拟合到测试句子上。
    suggestions = suggest_improvements(train_failures, candidate)

    best_description = candidate
    best_test_score = test_result["score"]
    if previous_path and Path(previous_path).is_file():
        prev = json.loads(read_text(previous_path))
        if prev.get("best_test_score", -1) > best_test_score:
            best_description = prev.get("best_description", candidate)
            best_test_score = prev.get("best_test_score", best_test_score)

    return {
        "status": "success",
        "skill_name": frontmatter.get("name", "unknown"),
        "mode": mode,
        "trials": trials,
        "original_description": original,
        "candidate_description": candidate,
        "train_set_size": len(train_set),
        "test_set_size": len(test_set),
        "train": {k: train_result[k] for k in ("score", "correct", "total", "metrics", "details")},
        "test": {k: test_result[k] for k in ("score", "correct", "total", "metrics", "details")},
        "train_failure_count": len(train_failures),
        "test_failure_count": len(test_failures),
        "failure_count": len(train_failures) + len(test_failures),
        "failures": train_failures + test_failures,
        "suggestions": suggestions,
        "best_description": best_description,
        "best_test_score": best_test_score,
        "recommendation": (
            "用 suggestions 改进 description，再用 --description 评估候选，"
            "按 test 分选优（勿按 train 分，防过拟合）。"
        ),
    }


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="按 train/held-out test 给技能 description 的触发准确率打分并给改进建议（选优按 test 分，防过拟合）。",
        epilog=(
            "示例:\n"
            "  python optimize_description.py skills/my-skill --eval-set evals/evals.json\n"
            "  python optimize_description.py skills/my-skill --eval-set evals/evals.json --runner opencode --detect my-skill\n"
            '  python optimize_description.py skills/my-skill --eval-set evals/evals.json --description "候选描述" --previous reports/desc-opt.json\n'
            "\n"
            "退出码:\n"
            "  0  成功\n"
            "  1  技能路径 / 评测集无效，或结果为 error\n"
            "  2  参数错误\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", help="Path to skill directory containing SKILL.md")
    parser.add_argument("--eval-set", required=True, help="Path to trigger eval set JSON")
    parser.add_argument("--runner", default="heuristic",
                        choices=["heuristic", "opencode", "teleagent", "cmd"],
                        help="How to judge triggering (default: heuristic)")
    parser.add_argument("--cmd", help="Command template for runner=cmd/teleagent")
    parser.add_argument("--detect", help="Substring/regex marking skill activation (default: skill name)")
    parser.add_argument("--description", help="候选描述（仅 heuristic 生效；agent 模式请先部署到 SKILL.md）")
    parser.add_argument("--previous", help="Previous report JSON; keeps the higher test score")
    parser.add_argument("--seed", type=int, default=42, help="Train/test split seed (default: 42)")
    parser.add_argument("--cwd", help="Working directory for agent runs")
    parser.add_argument("--timeout", type=int, default=120, help="Per-run timeout seconds (default: 120)")
    parser.add_argument("--trials", type=int, default=3,
                        help="每条查询跑 N 次、按触发率 ≥ 0.5 判触发（默认 3；heuristic 强制 1）")
    parser.add_argument("--workers", type=int, default=4,
                        help="并发 worker 数（默认 4；1=串行。每次预测一个独立子进程）")
    parser.add_argument("--verbose", action="store_true", help="逐条进度打到 stderr")
    parser.add_argument("--detect-mode", default="auto", choices=["auto", "substring", "skill-line"],
                        help='检测方式：auto（opencode→skill-line）/ substring / skill-line（锚定 Skill "名" 行）')
    parser.add_argument("--isolate-cwd", action="store_true",
                        help="每次运行在 --cwd 下新建空目录、跑完即删（防跨轮污染；需 --cwd 指向临时目录）")
    parser.add_argument("--evidence-ws", help="iteration 目录；给定则跑完写触发轴证据到 <dir>/evidence.json")
    parser.add_argument("--model", help="所用模型 ID（写触发轴证据时记录）")
    parser.add_argument("--out", "-o", help="Write the full report JSON to this path")
    args = parser.parse_args()

    if not Path(args.path).is_dir():
        print(json.dumps({"error": f"Not a directory: {args.path}"}, ensure_ascii=False), file=sys.stderr)
        return 1
    if not Path(args.eval_set).is_file():
        print(json.dumps({"error": f"Eval set not found: {args.eval_set}"}, ensure_ascii=False), file=sys.stderr)
        return 1

    detect = args.detect
    if detect is None and args.runner != "heuristic":
        fm, _b, _e = load_skill(args.path)
        detect = str((fm or {}).get("name", Path(args.path).name))

    result = optimize(
        args.path, args.eval_set,
        runner=args.runner, cmd=args.cmd, detect=detect,
        description_override=args.description, previous_path=args.previous,
        seed=args.seed, cwd=args.cwd, timeout=args.timeout, trials=args.trials,
        isolate_cwd=args.isolate_cwd, workers=args.workers, verbose=args.verbose,
        detect_mode=args.detect_mode,
    )
    if args.out and "error" not in result:
        write_text(args.out, json.dumps(result, indent=2, ensure_ascii=False))
    if args.evidence_ws and "error" not in result:
        merge_evidence(args.evidence_ws, args.path, ("trigger",),
                       model=args.model, skill_name=result.get("skill_name"))
    stream = sys.stderr if "error" in result else sys.stdout
    print(json.dumps(result, indent=2, ensure_ascii=False), file=stream)
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
