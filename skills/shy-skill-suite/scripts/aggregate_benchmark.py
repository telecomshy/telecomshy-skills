#!/usr/bin/env python3
"""把一个 iteration 工作区的评测结果聚合成 benchmark 报告。

读取 ``iteration-N/eval-*/{with_skill,baseline}/`` 下的 ``grading.json`` 与
``timing.json``，产出 ``benchmark.json`` 与 ``benchmark.md``，含通过率、token、耗时，
以及 with_skill 相对 baseline 的 improvement_ratio、token_ratio、time_ratio 与方差。
比率一律是 ``with_skill / baseline``：> 1 表示带技能**多花**（token / 耗时）或**更高**（通过率）。
可选读 ``<iteration>/analyzer_notes.json``（analyzer 的结论），并入 ``benchmark.json.notes``。

用法:
    python aggregate_benchmark.py <iteration-N 目录> --skill-name my-skill [--previous <上一轮目录>] [--notes <analyzer_notes.json>]

run 目录名兼容：with_skill / with-skill / with，baseline / without_skill / without-skill / old_skill；
也支持带序号的多轮试验：with_skill_0、baseline_0、……
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from skill_utils import force_utf8_stdio, read_text, write_text

RUN_TYPE_ALIASES: dict[str, list[str]] = {
    "with_skill": ["with_skill", "with-skill", "with"],
    "baseline": ["baseline", "without_skill", "without-skill", "old_skill", "old"],
}


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(read_text(path))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load_notes(path: Path) -> list[str]:
    """读 analyzer 的 notes：支持 ``{"notes": [...]}`` 或裸数组；缺失/损坏返回 []。"""
    data = load_json(path)
    if isinstance(data, dict):
        notes = data.get("notes") or []
    elif isinstance(data, list):
        notes = data
    else:
        return []
    if not isinstance(notes, list):
        return []
    return [str(n).strip() for n in notes if str(n).strip()]


def discover_eval_dirs(iteration_path: Path) -> list[Path]:
    return sorted(
        (e for e in iteration_path.iterdir() if e.is_dir() and re.match(r"^eval-\d+", e.name)),
        key=lambda p: int(re.match(r"^eval-(\d+)", p.name).group(1)),  # type: ignore[union-attr]
    )


def _duration_seconds(timing: dict[str, Any]) -> float:
    if "total_duration_seconds" in timing:
        return float(timing.get("total_duration_seconds") or 0.0)
    if "duration_seconds" in timing:
        return float(timing.get("duration_seconds") or 0.0)
    if "duration_ms" in timing:
        return float(timing.get("duration_ms") or 0) / 1000.0
    return 0.0


def _pass_rate(grading: dict[str, Any]) -> float:
    if "pass_rate" in grading:
        return float(grading.get("pass_rate") or 0.0)
    summary = grading.get("summary") or {}
    return float(summary.get("pass_rate") or 0.0)


def collect_run_data(run_path: Path) -> dict[str, Any] | None:
    if not run_path.is_dir():
        return None
    grading = load_json(run_path / "grading.json")
    if not grading:
        return None
    timing = load_json(run_path / "timing.json") or {}
    return {
        "pass_rate": _pass_rate(grading),
        "total_tokens": int(timing.get("total_tokens") or 0),
        "duration_seconds": _duration_seconds(timing),
    }


def collect_trial_data(eval_dir: Path, run_type: str) -> list[dict[str, Any]]:
    trials: list[dict[str, Any]] = []
    for alias in RUN_TYPE_ALIASES.get(run_type, [run_type]):
        data = collect_run_data(eval_dir / alias)
        if data:
            trials.append(data)
        for i in range(20):
            numbered = collect_run_data(eval_dir / f"{alias}_{i}")
            if numbered:
                trials.append(numbered)
    return trials


def calculate_stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    n = len(values)
    mean = sum(values) / n
    std = (sum((x - mean) ** 2 for x in values) / (n - 1)) ** 0.5 if n > 1 else 0.0
    return {
        "mean": round(mean, 4),
        "std": round(std, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def aggregate_benchmark(
    iteration_path: str,
    skill_name: str,
    previous_path: str | None = None,
    notes_path: str | None = None,
) -> dict[str, Any]:
    path = Path(iteration_path).resolve()
    if not path.is_dir():
        return {"error": f"Not a directory: {iteration_path}"}

    eval_dirs = discover_eval_dirs(path)
    if not eval_dirs:
        return {"error": f"No eval-* directories found in {path}"}

    match = re.search(r"iteration-(\d+)", path.name)
    iteration = int(match.group(1)) if match else 1

    per_eval: list[dict[str, Any]] = []
    buckets: dict[str, dict[str, list[float]]] = {
        "with_skill": {"pass": [], "tokens": [], "dur": []},
        "baseline": {"pass": [], "tokens": [], "dur": []},
    }

    for eval_dir in eval_dirs:
        metadata = load_json(eval_dir / "eval_metadata.json") or {}
        eval_name = metadata.get("eval_name", eval_dir.name)
        entry: dict[str, Any] = {
            "eval_id": int(re.match(r"^eval-(\d+)", eval_dir.name).group(1)),  # type: ignore[union-attr]
            "eval_name": eval_name,
        }
        for run_type in ("with_skill", "baseline"):
            trials = collect_trial_data(eval_dir, run_type)
            passes = [t["pass_rate"] for t in trials]
            tokens = [t["total_tokens"] for t in trials if t["total_tokens"] > 0]
            durations = [t["duration_seconds"] for t in trials if t["duration_seconds"] > 0]
            if not trials:
                continue
            entry[run_type] = {
                "pass_rate": calculate_stats(passes)["mean"],
                "pass_rate_std": calculate_stats(passes)["std"],
                "avg_tokens": calculate_stats(tokens)["mean"] if tokens else 0,
                "avg_duration_seconds": calculate_stats(durations)["mean"] if durations else 0,
                "trials": len(trials),
            }
            buckets[run_type]["pass"].extend(passes)
            buckets[run_type]["tokens"].extend(tokens)
            buckets[run_type]["dur"].extend(durations)
        per_eval.append(entry)

    with_stats = calculate_stats(buckets["with_skill"]["pass"])
    base_stats = calculate_stats(buckets["baseline"]["pass"])
    with_tokens = calculate_stats(buckets["with_skill"]["tokens"])["mean"]
    base_tokens = calculate_stats(buckets["baseline"]["tokens"])["mean"]
    with_dur = calculate_stats(buckets["with_skill"]["dur"])["mean"]
    base_dur = calculate_stats(buckets["baseline"]["dur"])["mean"]

    if base_stats["mean"] > 0:
        improvement_ratio = round(with_stats["mean"] / base_stats["mean"], 2)
    elif with_stats["mean"] > 0:
        improvement_ratio = 999.99
    else:
        improvement_ratio = 1.0

    benchmark: dict[str, Any] = {
        "skill_name": skill_name,
        "iteration": iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_evals": len(per_eval),
            "with_skill": {
                "pass_rate": with_stats["mean"],
                "pass_rate_std": with_stats["std"],
                "avg_tokens": with_tokens,
                "avg_duration_seconds": with_dur,
            },
            "baseline": {
                "pass_rate": base_stats["mean"],
                "pass_rate_std": base_stats["std"],
                "avg_tokens": base_tokens,
                "avg_duration_seconds": base_dur,
            },
            "improvement_ratio": improvement_ratio,
            "token_ratio": round(with_tokens / base_tokens, 2) if base_tokens > 0 else 1.0,
            "time_ratio": round(with_dur / base_dur, 2) if base_dur > 0 else 1.0,
        },
        "per_eval": per_eval,
    }

    notes = load_notes(Path(notes_path) if notes_path else path / "analyzer_notes.json")
    if notes:
        benchmark["notes"] = notes

    if previous_path:
        prev = load_json(Path(previous_path) / "benchmark.json")
        if prev:
            prev_with = (prev.get("summary") or {}).get("with_skill", {})
            benchmark["comparison"] = {
                "previous_iteration": prev.get("iteration", 0),
                "pass_rate_delta": round(with_stats["mean"] - prev_with.get("pass_rate", 0), 4),
                "token_delta": round(with_tokens - prev_with.get("avg_tokens", 0), 2),
                "duration_delta": round(with_dur - prev_with.get("avg_duration_seconds", 0), 2),
            }

    write_text(path / "benchmark.json", json.dumps(benchmark, indent=2, ensure_ascii=False))

    md = [
        f"# Benchmark Report: {skill_name}",
        "",
        f"- Iteration: {iteration}",
        f"- Timestamp: {benchmark['timestamp']}",
        f"- Total evals: {len(per_eval)}",
        "",
        "## Summary",
        "",
        "| Metric | With Skill | Baseline | With/Baseline |",
        "| --- | --- | --- | --- |",
        f"| Pass Rate | {with_stats['mean']:.0%} (std {with_stats['std']:.2f}) "
        f"| {base_stats['mean']:.0%} (std {base_stats['std']:.2f}) | {improvement_ratio}x |",
        f"| Avg Tokens | {with_tokens:,.0f} | {base_tokens:,.0f} | "
        f"{benchmark['summary']['token_ratio']}x |",
        f"| Avg Time | {with_dur:.1f}s | {base_dur:.1f}s | "
        f"{benchmark['summary']['time_ratio']}x |",
        "",
        "## Per-Eval",
        "",
        "| Eval | With Skill | Baseline |",
        "| --- | --- | --- |",
    ]
    for e in per_eval:
        md.append(
            f"| {e['eval_name']} | {e.get('with_skill', {}).get('pass_rate', 0):.0%} "
            f"| {e.get('baseline', {}).get('pass_rate', 0):.0%} |"
        )
    if notes:
        md += ["", "## Analyzer Notes", ""] + [f"- {n}" for n in notes]
    write_text(path / "benchmark.md", "\n".join(md) + "\n")

    return {
        "status": "success",
        "benchmark_json": str(path / "benchmark.json"),
        "benchmark_md": str(path / "benchmark.md"),
        "summary": benchmark["summary"],
        "notes": len(notes),
    }


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="把一个 iteration 工作区的评测结果聚合成 benchmark.json / benchmark.md（含 with_skill vs baseline 的比率与方差）。",
        epilog=(
            "示例:\n"
            "  python aggregate_benchmark.py my-skill-workspace/iteration-1 --skill-name my-skill\n"
            "  python aggregate_benchmark.py my-skill-workspace/iteration-1 --skill-name my-skill --previous my-skill-workspace/iteration-0\n"
            "\n"
            "退出码:\n"
            "  0  成功\n"
            "  1  路径不是目录 / 未发现 eval-* 目录\n"
            "  2  参数错误\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", help="Path to an iteration-N workspace directory")
    parser.add_argument("--skill-name", required=True, help="Name of the skill being benchmarked")
    parser.add_argument("--previous", "-p", help="Path to previous iteration directory for comparison")
    parser.add_argument("--notes", help="analyzer_notes.json 路径（缺省 <iteration>/analyzer_notes.json）")
    args = parser.parse_args()

    result = aggregate_benchmark(args.path, args.skill_name, args.previous, args.notes)
    stream = sys.stderr if "error" in result else sys.stdout
    print(json.dumps(result, indent=2, ensure_ascii=False), file=stream)
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
