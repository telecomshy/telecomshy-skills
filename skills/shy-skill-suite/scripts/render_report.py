#!/usr/bin/env python3
"""把一次 iteration 的评测结果与复审 findings 渲染成**单文件自包含** HTML 报告。

读取 `<iteration-dir>/benchmark.json`（可选）、`eval-*/{eval_metadata.json,
with_skill|baseline/grading.json,timing.json}`（可选）、`findings.json`（可选，
schema 见 `references/reviewing-skills.md`），用 `assets/report-template.html`
渲染出内嵌数据、无服务器、无外部资源的 `report.html`。

用法:
    python render_report.py <iteration-dir> [--skill-name <name>] [--findings <findings.json>] [--out report.html] [--serve]
"""

from __future__ import annotations

import argparse
import html
import json
import os
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
    out.append("</tbody></table>")

    notes = (bench or {}).get("notes") if bench else None
    if notes:
        out.append('<h3 style="font-size:14px;margin:18px 0 8px">Analyzer Notes</h3>')
        out.append("<ul>" + "".join(f"<li>{esc(n)}</li>" for n in notes) + "</ul>")

    out.append("</section>")
    return "\n".join(out)


def render_finding(f: dict[str, Any], fid: str, triage: bool = False) -> str:
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
        ("存在问题", "problem"), ("白话解释", "plain"), ("修改建议", "suggestion"),
    )
    dl = "".join(f"<dt>{esc(label)}</dt><dd>{esc(f.get(key))}</dd>" for label, key in fields if f.get(key))
    block = ""
    if triage:
        block = (
            f'<div class="triage" data-fid="{esc(fid)}" data-location="{esc(f.get("location", ""))}">'
            "<strong>分拣：</strong>"
            f'<label><input type="radio" name="tri-{esc(fid)}" value="立即修" checked> 立即修</label>'
            f'<label><input type="radio" name="tri-{esc(fid)}" value="以后修"> 以后修</label>'
            f'<label><input type="radio" name="tri-{esc(fid)}" value="丢弃"> 丢弃</label>'
            '<input class="note" type="text" placeholder="备注（可选）">'
            "</div>"
        )
    return (f'<div class="finding"><div>{"".join(head)}</div>'
            + (f"<dl>{dl}</dl>" if dl else "") + block + "</div>")


def render_findings(findings: dict[str, Any] | None, triage: bool = False) -> str:
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
    seq = [0]

    def next_fid() -> str:
        seq[0] += 1
        return f"F{seq[0]}"

    def render_group(group: list[dict[str, Any]]) -> None:
        """优先级内再按轴分组（Step 8「分轴报告、不合并」）。"""
        axes: list[str] = []
        for item in group:
            axis = str(item.get("axis") or "").strip()
            if axis and axis not in axes:
                axes.append(axis)
        if any(not str(item.get("axis") or "").strip() for item in group):
            axes.append("")
        for axis in axes:
            sub = [item for item in group if str(item.get("axis") or "").strip() == axis]
            if axis:
                out.append(f'<h4 style="font-size:13px;margin:12px 0 4px;color:var(--muted)">'
                           f'{esc(axis)}</h4>')
            out.extend(render_finding(item, next_fid(), triage) for item in sub)

    for prio in ("P0", "P1", "P2"):
        group = [f for f in items if str(f.get("priority", "")).upper() == prio]
        if not group:
            continue
        out.append(f'<h3 style="font-size:14px;margin:18px 0 6px">'
                   f'<span class="prio {prio.lower()}">{prio}</span>（{len(group)}）</h3>')
        render_group(group)
    rest = [f for f in items if str(f.get("priority", "")).upper() not in ("P0", "P1", "P2")]
    render_group(rest)
    out.append("</section>")
    return "\n".join(out)


def build_html(data: dict[str, Any], template: str, triage_endpoint: str = "") -> str:
    title = f"评估报告 · {data['skill_name']}"
    meta = f"iteration {data['iteration']} · 生成于 {data['generated_at']}"
    out = template.replace("{{TITLE}}", esc(title)).replace("{{META}}", esc(meta))
    # 占位符替换**先于**任何渲染内容插入：finding 文本里的 `{{...}}` 字面量不得被换成按钮 / 端点。
    if triage_endpoint:
        actions = ('<button id="btnSubmit" type="button">提交给 agent</button>'
                   '<span id="triageStatus">请逐条确认后提交（默认：立即修）</span>')
    else:
        actions = '<span class="muted">只读版（归档）；分拣请用 --serve 打开</span>'
    out = out.replace("{{TRIAGE_ENDPOINT}}", json.dumps(triage_endpoint))
    out = out.replace("{{TRIAGE_ACTIONS}}", actions)
    out = out.replace("<!--BENCHMARK-->", render_benchmark(data.get("benchmark"), data.get("evals") or []))
    out = out.replace("<!--FINDINGS-->",
                      render_findings(data.get("findings"), triage=bool(triage_endpoint)))
    # 内嵌数据不含过程字段（falsification / evidence）：报告可被转发 / 归档。
    embed = dict(data)
    findings_block = embed.get("findings")
    if isinstance(findings_block, dict) and isinstance(findings_block.get("findings"), list):
        embed["findings"] = dict(findings_block)
        embed["findings"]["findings"] = [
            {k: v for k, v in item.items() if k not in ("falsification", "evidence")}
            for item in findings_block["findings"]
        ]
    # 载荷最后注入：数据里即便含 `{{...}}` 字面量，也不会再被模板替换命中。
    payload = json.dumps(embed, ensure_ascii=False).replace("</", "<\\/")
    out = out.replace("/*__EMBEDDED_DATA__*/", f"const DATA = {payload};")
    return out


_OPEN_DISABLE_ENV = ("SHY_NO_OPEN", "CI", "NO_BROWSER")


def open_disabled_reason() -> str | None:
    """环境变量是否禁用自动打开；返回命中的变量名，否则 None。

    报告是复审的**终局**产物；子 agent / 自动化测试跑本脚本时必须静默，
    否则会中途弹浏览器打断用户。设任一变量为真值即可关闭。
    """
    for name in _OPEN_DISABLE_ENV:
        value = os.environ.get(name, "").strip().lower()
        if value and value not in ("0", "false", "no"):
            return name
    return None


def open_report(path: Path) -> bool:
    """用默认浏览器打开报告；无显示环境不抛错，返回是否成功。"""
    try:
        return webbrowser.open(path.as_uri())
    except Exception:
        return False


def open_url(url: str) -> bool:
    """用默认浏览器打开 URL；无显示环境不抛错，返回是否成功。"""
    try:
        return webbrowser.open(url)
    except Exception:
        return False


def serve_report(
    result: dict[str, Any],
    data: dict[str, Any],
    template: str,
    timeout: int,
    port: int,
    no_open: bool,
) -> dict[str, Any]:
    """起本地临时服务：页面勾选 POST /triage → 写 triage.json 后退出。

    只绑 127.0.0.1，URL 带一次性 token；超时未提交则以 timed_out 返回，
    静态 report.html 仍在（只读归档）。
    """
    import http.server
    import secrets
    import threading
    from urllib.parse import parse_qs, urlparse

    token = secrets.token_urlsafe(16)
    html = build_html(data, template, f"/triage?t={token}")
    triage_path = Path(result["report"]).resolve().parent / "triage.json"
    state = {"submitted": False, "choices": 0}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args: Any) -> None:  # noqa: D102 - 静默访问日志
            return

        def _send(self, code: int, body: bytes = b"",
                  ctype: str = "text/plain; charset=utf-8") -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if urlparse(self.path).path not in ("/", "/report.html"):
                return self._send(404, b"not found")
            self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != "/triage" or parse_qs(parsed.query).get("t", [""])[0] != token:
                return self._send(403, b"forbidden")
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > 64 * 1024:
                return self._send(413, b"bad size")
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return self._send(400, b"bad json")
            if not isinstance(body.get("triage"), list):
                return self._send(400, b"missing triage")
            write_text(triage_path, json.dumps(body, indent=2, ensure_ascii=False))
            state["submitted"] = True
            state["choices"] = len(body["triage"])
            self._send(200, b'{"status":"ok"}', "application/json; charset=utf-8")
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    try:
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as exc:
        return {"serve": False, "serve_error": f"端口不可用: {exc}"}

    url = f"http://127.0.0.1:{httpd.server_address[1]}/"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    opened = False if no_open else open_url(url)
    thread.join(timeout)
    timed_out = thread.is_alive()
    if timed_out:
        httpd.shutdown()
        thread.join(2)
    httpd.server_close()
    return {
        "serve": True,
        "serve_url": url,
        "opened": opened,
        "submitted": state["submitted"],
        "choices": state["choices"],
        "triage": str(triage_path) if state["submitted"] else None,
        "timed_out": False if state["submitted"] else timed_out,
    }


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
    template = read_text(template_path)
    write_text(destination, build_html(data, template))
    return {
        "status": "success",
        "report": str(destination),
        "evals": len(evals),
        "findings": len((findings or {}).get("findings") or []),
        "has_benchmark": bool(benchmark),
        "_data": data,
        "_template": template,
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
            "  python render_report.py my-skill-workspace/iteration-1 --serve   # 页面提交分拣，写 triage.json 后退出\n"
            "\n"
            "默认生成后自动用浏览器打开报告；关闭方式（任一即可）：--no-open，\n"
            "或设环境变量 SHY_NO_OPEN / CI / NO_BROWSER 为真值。\n"
            "无显示环境不报错，仍写出 HTML。\n"
            "--serve 只绑 127.0.0.1 + 一次性 token，等用户点「提交给 agent」或超时；\n"
            "默认（无 --serve）是静态单文件、无服务器。\n"
            "\n"
            "报告是复审的终局产物：**只在复审 Step 8 生成一次**；复审中途（含子 agent\n"
            "测试渲染）必须关闭自动打开，否则会中途弹浏览器打断用户。\n"
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
    parser.add_argument("--serve", action="store_true",
                        help="起本地临时服务并打开；页面点「提交给 agent」写 triage.json 后退出（默认静态、无服务器）")
    parser.add_argument("--serve-timeout", type=int, default=1800, help="--serve 等待提交的秒数（默认 1800）")
    parser.add_argument("--serve-port", type=int, default=0, help="--serve 监听端口（默认 0=随机）")
    args = parser.parse_args()

    result = render(args.path, args.skill_name, args.findings, args.out)
    data = result.pop("_data", None)
    template = result.pop("_template", None)
    has_findings = bool(((data or {}).get("findings") or {}).get("findings"))
    if result.get("status") == "success":
        if args.serve and not has_findings:
            result["serve_skipped"] = "无 findings 可分拣，直接出只读报告"
        if args.serve and has_findings and data is not None and template is not None:
            result.update(serve_report(result, data, template,
                                       args.serve_timeout, args.serve_port, args.no_open))
        else:
            skip = "--no-open" if args.no_open else open_disabled_reason()
            if skip:
                result["opened"] = False
                result["open_skipped"] = skip
            else:
                result["opened"] = open_report(Path(result["report"]))
    stream = sys.stderr if result.get("status") == "error" else sys.stdout
    print(json.dumps(result, indent=2, ensure_ascii=False), file=stream)
    return 1 if result.get("status") == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
