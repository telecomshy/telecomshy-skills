#!/usr/bin/env python3
"""行为轴 · 有效性对照运行器（with_skill vs baseline）。

每条用例 × trials 次，每次在**本批唯一隔离根**下的独立空目录里跑一次 prompt；
输出写入 `<ws>/eval-<id>/<arm>_<t>/`：

    outputs/response.txt     去掉 ANSI 的完整输出
    outputs/workspace/       运行目录里的产物快照（文件数 / 体积有上限）
    timing.json              耗时 / 返回码 / 加载的技能 / 越界取材证据

隔离与防污染（REQ-0069）：

- 每批在系统临时目录新建**唯一根**（默认跑完删除，``--keep`` 保留）；所有运行目录都在
  其下——杜绝"上一轮遗留被这一轮读到"。
- ``--skills-dir`` + ``--disable-skills a,b``：整批期间把列出的技能临时移出技能目录、
  ``finally`` 恢复。baseline 臂应同时屏蔽目标技能与易抢答的其他技能（如
  skill-creator / writing-for-agents）。
- 逐 run 扫描输出，把污染变成**可见字段**：``loaded_skills``（``Skill "名"`` 加载行）、
  ``contamination{foreign_reads, other_skills_loaded, target_loaded, ancestor_scans}``
  （运行目录之外的读取、非目标技能、是否加载目标技能、是否上溯扫过父目录）。
  污染不静默，交复审判读。

命令模板与 ``agent_runner.py`` 同语义：按 argv 切分、**不经 shell**，``{prompt}``
始终作为单个参数注入。

用法:
    python run_effectiveness.py --arm baseline --cases evals/effectiveness.json \
      --ws <workspace>/iteration-N --model <provider>/<id> \
      --skills-dir "<用户技能目录>" --disable-skills shy-skill-suite,skill-creator
    python run_effectiveness.py --arm with_skill --cases evals/effectiveness.json \
      --ws <workspace>/iteration-N --model <provider>/<id>

退出码:
    0  全部运行返回码 0 且无错误
    1  有运行超时 / 非 0 返回码（产出仍已落盘，可判读）
    2  参数错误
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from agent_runner import build_argv
from skill_utils import force_utf8_stdio, merge_evidence

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
SKILL_LOAD_RE = re.compile(r'Skill\s+"([^"]+)"')
READ_RE = re.compile(r"Read\s+([^\s\"']+)")

MAX_FILES = 300
MAX_BYTES = 15 * 1024 * 1024


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def loaded_skills(text: str) -> list[str]:
    out: list[str] = []
    for name in SKILL_LOAD_RE.findall(text):
        if name not in out:
            out.append(name)
    return out


def _norm(path: str) -> str:
    return path.replace("\\", "/").rstrip(".,;:。，；）)】]")


def scan_contamination(text: str, cwd: Path, detect_skill: str, loaded: list[str]) -> dict:
    """把"运行目录之外的取材"变成可见字段（不判定，只记录）。"""
    cwd_n = _norm(str(cwd)).lower()
    ancestor = _norm(str(cwd.parent.parent)).lower()
    foreign: list[str] = []
    ancestor_scans = 0
    for line in text.splitlines():
        if ancestor and ancestor in _norm(line).lower():
            ancestor_scans += 1
        for raw in READ_RE.findall(line):
            p = _norm(raw)
            if p.startswith(("http://", "https://")):
                continue
            if len(p) < 3 or ("/" not in p and ":" not in p):
                continue
            if not _norm(p).lower().startswith(cwd_n) and p not in foreign:
                foreign.append(p)
    others = [s for s in loaded if s != detect_skill]
    return {
        "foreign_reads": foreign[:8],
        "other_skills_loaded": others,
        "target_loaded": detect_skill in loaded,
        "ancestor_scans": ancestor_scans,
    }


def copy_workspace(src: Path, dst: Path) -> tuple[int, bool]:
    """复制运行目录快照；超过文件数 / 体积上限则截断并如实标注。"""
    shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True, exist_ok=True)
    files = 0
    size = 0
    truncated = False
    for p in sorted(src.rglob("*")):
        if p.is_dir() or ".git" in p.parts or "__pycache__" in p.parts or "node_modules" in p.parts:
            continue
        if files >= MAX_FILES or size >= MAX_BYTES:
            truncated = True
            break
        rel = p.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = p.read_bytes()
        except OSError:
            continue
        target.write_bytes(data)
        files += 1
        size += len(data)
    return files, truncated


def disable_skills(skills_dir: Path, names: list[str]) -> list[tuple[Path, Path]]:
    moved: list[tuple[Path, Path]] = []
    for name in names:
        src = skills_dir / name
        if src.is_dir():
            dst = skills_dir.parent / f".{name}.disabled-{uuid.uuid4().hex[:8]}"
            shutil.move(str(src), str(dst))
            moved.append((src, dst))
    return moved


def restore_skills(moved: list[tuple[Path, Path]]) -> None:
    for src, dst in moved:
        if dst.exists() and not src.exists():
            shutil.move(str(dst), str(src))


def run_one(template: str, prompt: str, cwd: Path, timeout: int) -> tuple[str, float, int | None, str | None]:
    argv = build_argv(template, prompt)
    t0 = time.time()
    try:
        proc = subprocess.run(
            argv, cwd=str(cwd), stdin=subprocess.DEVNULL, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout, shell=False,
        )
        return strip_ansi((proc.stdout or "") + "\n" + (proc.stderr or "")), \
            time.time() - t0, proc.returncode, None
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", "replace")
        return strip_ansi(partial), time.time() - t0, None, f"timeout after {timeout}s"
    except OSError as exc:
        return "", time.time() - t0, None, f"could not run command: {exc}"


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(
        description="行为轴 · 有效性对照运行器：每批唯一隔离根 + 可屏蔽技能 + 污染扫描。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            '  python run_effectiveness.py --arm baseline --cases evals/effectiveness.json \\\n'
            '    --ws <workspace>/iteration-N --model <provider>/<id> \\\n'
            '    --skills-dir "<技能目录>" --disable-skills shy-skill-suite,skill-creator\n'
            "\n"
            "退出码:\n  0  全部运行成功\n  1  有超时 / 非 0 返回码\n  2  参数错误\n"
        ),
    )
    ap.add_argument("--arm", required=True, choices=["with_skill", "baseline"], help="臂名（写入运行目录名）")
    ap.add_argument("--cases", required=True, help="用例集 JSON（schema 同 evals/effectiveness.json）")
    ap.add_argument("--ws", required=True, help="工作区 iteration 目录（输出写这里）")
    ap.add_argument("--trials", type=int, default=3, help="每条用例跑几次（默认 3）")
    ap.add_argument("--workers", type=int, default=3, help="并发数（默认 3）")
    ap.add_argument("--cmd", help='命令模板（含 {prompt}）；缺省用 --model 拼 opencode run')
    ap.add_argument("--model", help="缺省命令模板用的模型 ID，如 deepseek/deepseek-flash")
    ap.add_argument("--timeout", type=int, default=300, help="单次超时秒数（默认 300）")
    ap.add_argument("--cwd-base", help="隔离根目录（缺省：系统临时目录下新建唯一根）")
    ap.add_argument("--keep", action="store_true",
                    help="保留自动创建的隔离根（缺省跑完删除；--cwd-base 给定的一律保留、由调用方管理）")
    ap.add_argument("--detect-skill", help="目标技能名（缺省取用例集 skill_name）")
    ap.add_argument("--skills-dir", help="技能目录（配合 --disable-skills）")
    ap.add_argument("--disable-skills", help="整批期间临时移出的技能名（逗号分隔）")
    ap.add_argument("--skill-dir", help="被评测技能的目录；给定则跑完写有效性轴证据到 <ws>/evidence.json")
    args = ap.parse_args()

    if not args.cmd and not args.model:
        print("需要 --cmd 或 --model 之一", file=sys.stderr)
        return 2
    template = args.cmd or f'opencode run --model {args.model} "{{prompt}}"'

    try:
        data = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    except OSError:
        print(f"用例集不存在：{args.cases}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"用例集解析失败：{exc}", file=sys.stderr)
        return 2
    cases = data.get("cases") or []
    if not cases:
        print(f"用例集为空：{args.cases}", file=sys.stderr)
        return 2
    detect_skill = args.detect_skill or data.get("skill_name") or ""
    ws = Path(args.ws).resolve()

    if args.cwd_base:
        cwd_root = Path(args.cwd_base).resolve()
        cwd_root.mkdir(parents=True, exist_ok=True)
        fresh_root = False
    else:
        cwd_root = Path(tempfile.mkdtemp(prefix="shy-eff-"))
        fresh_root = True

    moved: list[tuple[Path, Path]] = []
    if args.disable_skills and args.skills_dir:
        moved = disable_skills(Path(args.skills_dir), [
            s.strip() for s in args.disable_skills.split(",") if s.strip()])
    elif args.disable_skills:
        print("--disable-skills 需要同时给 --skills-dir", file=sys.stderr)
        return 2

    runs: list[dict] = []
    errors = 0

    def work(case: dict, trial: int) -> dict:
        run_dir = ws / f"eval-{case['eval_id']}" / f"{args.arm}_{trial}"
        (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
        cwd = cwd_root / f"{args.arm}-{case['eval_id']}-{trial}"
        shutil.rmtree(cwd, ignore_errors=True)
        cwd.mkdir(parents=True)
        text, dur, rc, err = run_one(template, case["prompt"], cwd, args.timeout)
        (run_dir / "outputs" / "response.txt").write_text(text, encoding="utf-8")
        loaded = loaded_skills(text)
        contam = scan_contamination(text, cwd, detect_skill, loaded)
        files, truncated = copy_workspace(cwd, run_dir / "outputs" / "workspace")
        timing = {
            "total_tokens": 0,
            "total_duration_seconds": round(dur, 2),
            "returncode": rc,
            "error": err,
            "loaded_skills": loaded,
            "contamination": contam,
            "workspace_files": files,
            "workspace_truncated": truncated,
        }
        (run_dir / "timing.json").write_text(
            json.dumps(timing, ensure_ascii=False, indent=2), encoding="utf-8")
        shutil.rmtree(cwd, ignore_errors=True)
        return {
            "eval": case["eval_name"], "run": f"{args.arm}_{trial}",
            "duration": round(dur, 2), "returncode": rc, "error": err,
            "loaded_skills": loaded, "contaminated": bool(
                contam["foreign_reads"] or contam["other_skills_loaded"]
                or (args.arm == "baseline" and contam["target_loaded"])),
        }

    try:
        jobs = [(c, t) for c in cases for t in range(args.trials)]
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
            futs = [ex.submit(work, c, t) for c, t in jobs]
            for fut in as_completed(futs):
                r = fut.result()
                runs.append(r)
                if r["error"] or r["returncode"] not in (0,):
                    errors += 1
                print(f"{r['eval']} {r['run']}: {r['duration']}s rc={r['returncode']} "
                      f"err={r['error']} loaded={r['loaded_skills']} contaminated={r['contaminated']}",
                      file=sys.stderr)
    finally:
        restore_skills(moved)
        if fresh_root and not args.keep:
            shutil.rmtree(cwd_root, ignore_errors=True)

    evidence_path = None
    if args.skill_dir:
        evidence_path = merge_evidence(ws, args.skill_dir, ("effectiveness",),
                                       model=args.model, skill_name=detect_skill or None)

    kept = bool(args.keep or not fresh_root)
    print(json.dumps({
        "status": "success" if errors == 0 else "partial",
        "arm": args.arm, "runs": len(runs), "errors": errors,
        "cwd_root": str(cwd_root), "cwd_root_kept": kept,
        "disabled_skills": [str(s) for s, _ in moved],
        "ws": str(ws),
        "evidence": str(evidence_path) if evidence_path else None,
    }, ensure_ascii=False, indent=2))
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
