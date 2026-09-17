#!/usr/bin/env python3
"""优化技能 description 的触发准确率。

把评测集按 should_trigger 分层切成 train / held-out test，给当前 description 打分，
并给出改进建议。**选优按 test 分**（防过拟合）。

真实触发判定有两种模式：
    --runner heuristic   离线关键词/汉字二元组重叠启发式（默认，无需 agent）
    --runner opencode|teleagent|cmd   真跑 agent，用 agent_runner 检测技能是否被触发

脚本本身不重写 description（那需要 LLM）。循环由 agent 驱动：
提出新 description → 用 ``--description`` 评估 → 比较 test 分 → 保留更高者。

用法:
    python optimize_description.py <skill_dir> --eval-set evals/evals.json
    python optimize_description.py <skill_dir> --eval-set evals/evals.json --runner opencode --detect my-skill
    python optimize_description.py <skill_dir> --eval-set evals/evals.json --description "候选描述" --previous reports/desc-opt.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Any, Callable

from agent_runner import resolve_command, run_prompt
from skill_utils import force_utf8_stdio, load_skill, read_text, write_text

_ASCII_WORD = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
_CJK_CHAR = re.compile(r"[\u3400-\u9fff]")


def split_eval_set(
    evals: list[dict[str, Any]],
    train_ratio: float = 0.6,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """按 should_trigger 分层切分 train/test，保证两边都有正负例。"""
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
) -> tuple[Callable[[str], bool | None], str]:
    """返回 (predict_fn, mode)；predict_fn 返回 True/False，或 None 表示无法判定。"""
    if runner != "heuristic" and resolve_command(runner, cmd):
        def predict(prompt: str) -> bool | None:
            result = run_prompt(
                prompt, runner=runner, cmd=cmd,
                detect_pattern=detect, cwd=cwd, timeout=timeout,
            )
            return result.get("triggered")

        return predict, f"agent:{runner}"

    def predict(prompt: str) -> bool | None:
        return heuristic_predict(description, prompt)

    return predict, "heuristic"


def score(
    description: str,
    eval_set: list[dict[str, Any]],
    predict: Callable[[str], bool | None],
    split: str = "",
) -> dict[str, Any]:
    details: list[dict[str, Any]] = []
    correct = 0
    for item in eval_set:
        should = bool(item.get("should_trigger", True))
        predicted = predict(item.get("prompt", ""))
        is_correct = predicted is not None and predicted == should
        if is_correct:
            correct += 1
        details.append({
            "eval_id": item.get("eval_id", 0),
            "prompt": item.get("prompt", ""),
            "should_trigger": should,
            "predicted_trigger": predicted,
            "correct": is_correct,
            "split": split,
        })
    total = len(eval_set)
    return {
        "score": round(correct / total, 4) if total else 0.0,
        "correct": correct,
        "total": total,
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

    train_set, test_set = split_eval_set(all_evals, seed=seed)
    predict, mode = build_predictor(candidate, runner, cmd, detect, cwd, timeout)

    train_result = score(candidate, train_set, predict, "train")
    test_result = score(candidate, test_set, predict, "test")

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
        "original_description": original,
        "candidate_description": candidate,
        "train_set_size": len(train_set),
        "test_set_size": len(test_set),
        "train": {k: train_result[k] for k in ("score", "correct", "total")},
        "test": {k: test_result[k] for k in ("score", "correct", "total")},
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
    parser.add_argument("--description", help="Evaluate this candidate description instead of the current one")
    parser.add_argument("--previous", help="Previous report JSON; keeps the higher test score")
    parser.add_argument("--seed", type=int, default=42, help="Train/test split seed (default: 42)")
    parser.add_argument("--cwd", help="Working directory for agent runs")
    parser.add_argument("--timeout", type=int, default=120, help="Per-run timeout seconds (default: 120)")
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
        seed=args.seed, cwd=args.cwd, timeout=args.timeout,
    )
    if args.out and "error" not in result:
        write_text(args.out, json.dumps(result, indent=2, ensure_ascii=False))
    stream = sys.stderr if "error" in result else sys.stdout
    print(json.dumps(result, indent=2, ensure_ascii=False), file=stream)
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
