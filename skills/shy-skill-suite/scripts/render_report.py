#!/usr/bin/env python3
"""把一次 iteration 的评测结果与复审 findings 渲染成**单文件自包含** HTML 报告。

读取 `<iteration-dir>/benchmark.json`（可选）、`eval-*/{eval_metadata.json,
with_skill|baseline/grading.json,timing.json}`（可选）、`findings.json`（可选，
schema 见 `references/reviewing-skills.md`），用 `assets/report-template.html`
渲染出内嵌数据、无服务器、无外部资源的 `report.html`。

用法:
    python render_report.py <iteration-dir> [--skill-name <name>] [--findings <findings.json>] [--out report.html]
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from skill_utils import force_utf8_stdio, read_text, write_text

EVAL_DIR_RE = re.compile(r"^eval-(\d+)")
RUN_ALIASES: dict[str, list[str]] = {
    "with_skill": ["with_skill", "with-skill", "with"],
    "baseline": ["baseline", "without_skill", "without-skill", "old_skill", "old"],
}


def load_json(path: Path) -> dict[str, Any] | None:
    """读 JSON；缺失或损坏返回 None（报告允许部分数据）。"""
    try:
        return json.loads(read_text(path))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _pass_rate(grading: dict[str, Any]) -> float:
    if "pass_rate" in grading:
        return float(grading.get("pass_rate") or 0.0)
    return float((grading.get("summary") or {}).get("pass_rate") or 0.0)


def _assertions(grading: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for a in grading.get("assertions") or []:
        out.append({
            "name": a.get("name") or a.get("text") or "",
            "passed": a.get("passed"),
            "evidence": a.get("evidence", ""),
        })
    return out


def _run_data(eval_dir: Path, run_type: str) -> dict[str, Any] | None:
    for alias in RUN_ALIASES[run_type]:
        d = eval_dir / alias
        if not d.is_dir():
            continue
        grading = load_json(d / "grading.json")
        if grading is None:
            return None
        timing = load_json(d / "timing.json") or {}
        return {
            "pass_rate": _pass_rate(grading),
            "total_tokens": int(timing.get("total_tokens") or 0),
            "duration_seconds": float(
                timing.get("total_duration_seconds") or timing.get("duration_seconds") or 0.0
            ),
            "assertions": _assertions(grading),
        }
    return None


def scan_evals(itdir: Path) -> list[dict[str, Any]]:
    """扫描 eval-* 目录，取 eval_metadata + with_skill/baseline 的 grading/timing。"""
    evals: list[dict[str, Any]] = []
    dirs = [p for p in itdir.iterdir() if p.is_dir() and EVAL_DIR_RE.match(p.name)]
    dirs.sort(key=lambda p: int(EVAL_DIR_RE.match(p.name).group(1)))  # type: ignore[union-attr]
    for d in dirs:
        meta = load_json(d / "eval_metadata.json") or {}
        evals.append({
            "eval_id": int(EVAL_DIR_RE.match(d.name).group(1)),  # type: ignore[union-attr]
            "eval_name": meta.get("eval_name", d.name),
            "prompt": meta.get("prompt", ""),
            "should_trigger": meta.get("should_trigger"),
            "with_skill": _run_data(d, "with_skill"),
            "baseline": _run_data(d, "baseline"),
        })
    return evals


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def summarize(evals: list[dict[str, Any]]) -> dict[str, Any]:
    """无 benchmark.json 时，从扫描到的 eval 现算一份摘要。"""
    def bucket(run: str) -> dict[str, float]:
        present = [e[run] for e in evals if e.get(run)]
        pr = [e["pass_rate"] for e in present]
        tok = [e["total_tokens"] for e in present if e["total_tokens"] > 0]
        dur = [e["duration_seconds"] for e in present if e["duration_seconds"] > 0]
        return {"pass_rate": _mean(pr), "avg_tokens": _mean(tok), "avg_duration_seconds": _mean(dur)}

    w, b = bucket("with_skill"), bucket("baseline")
    if b["pass_rate"] > 0:
        improvement = round(w["pass_rate"] / b["pass_rate"], 2)
    elif w["pass_rate"] > 0:
        improvement = 999.99
    else:
        improvement = 1.0
    return {
        "with_skill": w,
        "baseline": b,
        "improvement_ratio": improvement,
        "token_ratio": round(w["avg_tokens"] / b["avg_tokens"], 2) if b["avg_tokens"] > 0 else 1.0,
        "time_ratio": round(w["avg_duration_seconds"] / b["avg_duration_seconds"], 2)
        if b["avg_duration_seconds"] > 0 else 1.0,
    }


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _pct(x: Any) -> str:
    return f"{float(x or 0):.0%}"


def _num(x: Any) -> str:
    return f"{float(x or 0):,.0f}"


def _sec(x: Any) -> str:
    return f"{float(x or 0):.1f}s"


def render_benchmark(bench: dict[str, Any] | None, evals: list[dict[str, Any]]) -> str:
    if not bench and not evals:
        return '<section><h2>评测</h2><p class="muted">无评测数据</p></section>'

    summary = (bench or {}).get("summary") if bench else None
    if not summary:
        summary = summarize(evals)
    w = summary.get("with_skill") or {}
    b = summary.get("baseline") or {}

    rows = [
        ("通过率", _pct(w.get("pass_rate")), _pct(b.get("pass_rate")), f"{summary.get('improvement_ratio', 1.0)}x"),
        ("平均 token", _num(w.get("avg_tokens")), _num(b.get("avg_tokens")), f"{summary.get('token_ratio', 1.0)}x"),
        ("平均耗时", _sec(w.get("avg_duration_seconds")), _sec(b.get("avg_duration_seconds")),
         f"{summary.get('time_ratio', 1.0)}x"),
    ]
    out = ['<section><h2>评测（with_skill vs baseline）</h2>']
    out.append('<table><thead><tr><th>指标</th><th class="num">With Skill</th>'
               '<th class="num">Baseline</th><th class="num">With/Baseline</th></tr></thead><tbody>')
    for name, a, c, r in rows:
        out.append(f'<tr><td>{esc(name)}</td><td class="num">{esc(a)}</td>'
                   f'<td class="num">{esc(c)}</td><td class="num">{esc(r)}</td></tr>')
    out.append("</tbody></table>")

    per_eval = (bench or {}).get("per_eval") if bench else None
    out.append('<h3 style="font-size:14px;margin:18px 0 8px">逐 eval</h3>')
    out.append('<table><thead><tr><th>Eval</th><th>Prompt</th>'
               '<th class="num">With</th><th class="num">Baseline</th></tr></thead><tbody>')
    if per_eval:
        for e in per_eval:
            out.append(
                f'<tr><td>{esc(e.get("eval_name"))}</td><td></td>'
                f'<td class="num">{_pct((e.get("with_skill") or {}).get("pass_rate"))}</td>'
                f'<td class="num">{_pct((e.get("baseline") or {}).get("pass_rate"))}</td></tr>'
            )
    else:
        for e in evals:
            out.append(
                f'<tr><td>{esc(e.get("eval_name"))}</td><td>{esc(e.get("prompt"))}</td>'
                f'<td class="num">{_pct((e.get("with_skill") or {}).get("pass_rate"))}</td>'
                f'<td class="num">{_pct((e.get("baseline") or {}).get("pass_rate"))}</td></tr>'
            )
    out.append("</tbody></table></section>")
    return "\n".join(out)


def render_finding(f: dict[str, Any]) -> str:
    head = []
    if f.get("axis"):
        head.append(f'<span class="badge">{esc(f["axis"])}</span>')
    if f.get("priority"):
        head.append(f'<span class="prio {esc(str(f["priority"]).lower())}">{esc(f["priority"])}</span>')
    if f.get("location"):
        head.append(f' <span class="loc">{esc(f["location"])}</span>')
    if f.get("verified") is False:
        head.append(' <span class="unverified">待验证</span>')

    fields = (
        ("问题", "problem"), ("影响", "impact"), ("建议", "suggestion"),
        ("预期", "expected"), ("证伪", "falsification"), ("证据", "evidence"),
    )
    dl = "".join(f"<dt>{esc(label)}</dt><dd>{esc(f.get(key))}</dd>" for label, key in fields if f.get(key))
    return f'<div class="finding"><div>{"".join(head)}</div>' + (f"<dl>{dl}</dl>" if dl else "") + "</div>"


def render_findings(findings: dict[str, Any] | None) -> str:
    if not findings:
        return '<section><h2>复审意见</h2><p class="muted">无复审数据</p></section>'
    out = ["<section><h2>复审意见</h2>"]
    if findings.get("verdict"):
        out.append(f'<p>结论：<span class="verdict">{esc(findings["verdict"])}</span></p>')
    s = findings.get("summary") or {}
    if s:
        out.append(f'<p class="muted">候选 {esc(s.get("candidates", "-"))} · '
                   f'通过 {esc(s.get("passed", "-"))} · 被证伪 {esc(s.get("falsified", "-"))}</p>')
    items = findings.get("findings") or []
    for prio in ("P0", "P1", "P2"):
        group = [f for f in items if str(f.get("priority", "")).upper() == prio]
        if not group:
            continue
        out.append(f'<h3 style="font-size:14px;margin:18px 0 6px">'
                   f'<span class="prio {prio.lower()}">{prio}</span>（{len(group)}）</h3>')
        out.extend(render_finding(f) for f in group)
    rest = [f for f in items if str(f.get("priority", "")).upper() not in ("P0", "P1", "P2")]
    out.extend(render_finding(f) for f in rest)
    out.append("</section>")
    return "\n".join(out)


def build_html(data: dict[str, Any], template: str) -> str:
    title = f"评估报告 · {data['skill_name']}"
    meta = f"iteration {data['iteration']} · 生成于 {data['generated_at']}"
    out = template.replace("{{TITLE}}", esc(title)).replace("{{META}}", esc(meta))
    out = out.replace("<!--BENCHMARK-->", render_benchmark(data.get("benchmark"), data.get("evals") or []))
    out = out.replace("<!--FINDINGS-->", render_findings(data.get("findings")))
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out = out.replace("/*__EMBEDDED_DATA__*/", f"const DATA = {payload};")
    return out


def open_report(path: Path) -> bool:
    """用默认浏览器打开报告；无显示环境不抛错，返回是否成功。"""
    try:
        return webbrowser.open(path.as_uri())
    except Exception:
        return False


def _fallback_skill_name(itdir: Path) -> str:
    """目录名兜底：`iteration-N` 时取父目录名（去 `-workspace`），否则取自身。"""
    if re.match(r"^iteration-\d+$", itdir.name):
        return itdir.parent.name.replace("-workspace", "")
    return itdir.name.replace("-workspace", "")


def render(
    iteration_dir: str,
    skill_name: str | None = None,
    findings_path: str | None = None,
    out_path: str | None = None,
) -> dict[str, Any]:
    itdir = Path(iteration_dir).resolve()
    if not itdir.is_dir():
        return {"status": "error", "error": f"不是目录: {iteration_dir}"}

    template_path = Path(__file__).resolve().parent.parent / "assets" / "report-template.html"
    if not template_path.is_file():
        return {"status": "error", "error": f"模板缺失: {template_path}"}

    if findings_path:
        fp = Path(findings_path)
        if not fp.is_file():
            return {"status": "error", "error": f"findings 不存在: {fp}"}
    else:
        fp = itdir / "findings.json"

    benchmark = load_json(itdir / "benchmark.json")
    findings = load_json(fp) if fp.is_file() else None
    evals = scan_evals(itdir)
    if not benchmark and not findings and not evals:
        return {"status": "error",
                "error": f"无可渲染数据（无 benchmark.json / findings.json / eval-*）: {itdir}"}

    if not skill_name:
        skill_name = ((benchmark or {}).get("skill_name")
                      or (findings or {}).get("skill")
                      or _fallback_skill_name(itdir))
    match = re.search(r"iteration-(\d+)", itdir.name)
    iteration = int(match.group(1)) if match else int((benchmark or {}).get("iteration") or 1)

    data = {
        "skill_name": skill_name,
        "iteration": iteration,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "benchmark": benchmark,
        "findings": findings,
        "evals": evals,
    }
    destination = Path(out_path) if out_path else (itdir / "report.html")
    write_text(destination, build_html(data, read_text(template_path)))
    return {
        "status": "success",
        "report": str(destination),
        "evals": len(evals),
        "findings": len((findings or {}).get("findings") or []),
        "has_benchmark": bool(benchmark),
    }


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="把一次 iteration 的评测结果与复审 findings 渲染成单文件自包含 HTML 报告。",
        epilog=(
            "示例:\n"
            "  python render_report.py my-skill-workspace/iteration-1\n"
            "  python render_report.py my-skill-workspace/iteration-1 --skill-name my-skill -o report.html\n"
            "  python render_report.py my-skill-workspace/iteration-1 --no-open\n"
            "\n"
            "默认生成后自动用浏览器打开报告；用 --no-open 关闭（无显示环境不报错）。\n"
            "\n"
            "退出码:\n"
            "  0  成功（已写出 HTML）\n"
            "  1  工作区 / 模板 / findings 缺失，或无可渲染数据\n"
            "  2  参数错误\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", help="iteration-N 工作区目录")
    parser.add_argument("--skill-name", help="技能名（缺省从 benchmark / findings / 目录名推断）")
    parser.add_argument("--findings", help="findings.json 路径（缺省 <dir>/findings.json）")
    parser.add_argument("--out", "-o", help="输出 HTML 路径（缺省 <dir>/report.html）")
    parser.add_argument("--no-open", action="store_true", help="生成后不自动打开浏览器（默认会自动打开）")
    args = parser.parse_args()

    result = render(args.path, args.skill_name, args.findings, args.out)
    if result.get("status") == "success" and not args.no_open:
        result["opened"] = open_report(Path(result["report"]))
    stream = sys.stderr if result.get("status") == "error" else sys.stdout
    print(json.dumps(result, indent=2, ensure_ascii=False), file=stream)
    return 1 if result.get("status") == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
