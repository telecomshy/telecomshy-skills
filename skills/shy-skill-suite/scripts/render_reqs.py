#!/usr/bin/env python3
"""单技能 REQ 报告：把某个技能的 REQ 渲染成**单文件自包含** HTML。

直接读 `docs/<skill>/requirements/REQ-*.md` 的 frontmatter（id / title / kind /
status / created / updated / iteration / blocked_by）与 `## 问题与目标` 首段，
按 `kind → status → REQ` 三级结构渲染：

- 一级 **kind**：白话标签 + 计数，默认展开；固定顺序 feature → fix → refactor →
  docs → hygiene → unspecified。
- 二级 **status**：白话标签 + 计数，默认折叠。
- 三级 **REQ**：每条一行 `REQ-NNNN + title`（title 即白话说明，inline 可见）；
  点开看详情（元数据 + `## 问题与目标` 首段）。

不再依赖任何预生成的 JSON 视图，也不做能力视图。**不复用** `render_report.py`
（那是复审报告，schema 不同）。

用法:
    python render_reqs.py --root . --skill <skill> [--kind <kind>] [--out <path>] [--no-open]

退出码:
    0  成功（已写出 HTML）
    1  技能不存在 / 无 REQ / root 非法 / 写出失败
    2  参数错误（缺 --skill 等）
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

from skill_utils import (
    KIND_LABELS,
    KIND_ORDER,
    STATUS_LABELS,
    STATUS_ORDER,
    force_utf8_stdio,
    kind_label,
    parse_frontmatter,
    read_text,
    status_label,
    write_text,
)
from track_requirements import as_list

_OPEN_DISABLE_ENV = ("SHY_NO_OPEN", "CI", "NO_BROWSER")
OBJECTIVE_RE = re.compile(r"^##\s+问题与目标\s*$(.*?)(?=^##\s|\Z)", re.S | re.M)

CSS = """
  :root { --fg:#1f2328; --muted:#6a737d; --line:#e1e4e8; --bg:#fff; --soft:#f6f8fa;
          --accent:#1f6feb; --kind:#1f6feb; --status:#8250df; --req:#1a7f37; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--fg);
         font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC","Microsoft YaHei",sans-serif; }
  header, main, footer { max-width: 960px; margin: 0 auto; padding: 0 20px; }
  .topbar { position: sticky; top: 0; z-index: 2; background: var(--soft);
            border-bottom: 1px solid var(--line); padding: 10px 20px; display: flex;
            gap: 16px; flex-wrap: wrap; align-items: baseline; }
  .topbar strong { font-size: 15px; }
  .topbar .stat { color: var(--muted); font-size: 13px; }
  header { padding-top: 28px; padding-bottom: 8px; }
  header h1 { margin: 0 0 4px; font-size: 22px; }
  header .meta { margin: 0; color: var(--muted); font-size: 13px; }
  main { padding-bottom: 40px; }
  details { border:1px solid var(--line); border-radius:8px; margin:8px 0; padding:2px 14px; }
  details.kind { border-left:4px solid var(--kind); }
  details.status { border-left:4px solid var(--status); margin-left:14px; background:var(--soft); }
  details.req { border-left:4px solid var(--req); margin-left:28px; }
  summary { cursor:pointer; font-weight:600; padding:8px 0; }
  details.status > summary { font-weight:500; }
  details.req > summary { font-weight:400; }
  summary .count { color:var(--muted); font-weight:400; font-size:13px; margin-left:6px; }
  details.req > summary code { background:var(--soft); padding:1px 6px; border-radius:4px; font-size:12.5px; }
  .meta { color:var(--muted); font-size:13px; margin:4px 0 6px; }
  .bg { margin:6px 0 12px; }
  .muted { color:var(--muted); }
  footer { margin: 40px auto; color: var(--muted); font-size: 12px; }
"""


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def first_paragraph(body: str) -> str:
    """取 `## 问题与目标` 的第一段（背景）；缺失返回空串。"""
    match = OBJECTIVE_RE.search(body or "")
    if not match:
        return ""
    block = match.group(1).strip()
    if not block:
        return ""
    para = block.split("\n\n", 1)[0]
    return " ".join(line.strip() for line in para.splitlines() if line.strip())


def load_reqs(root: Path, skill: str) -> tuple[list[dict[str, Any]], str | None]:
    """读单技能的 REQ 文件；返回 (reqs, error)。技能目录缺失 / 无 REQ → error。"""
    req_dir = root / "docs" / skill / "requirements"
    if not req_dir.is_dir():
        return [], f"技能不存在或缺少需求目录：{req_dir}"
    reqs: list[dict[str, Any]] = []
    for path in sorted(req_dir.glob("REQ-*.md")):
        frontmatter, body, _errors = parse_frontmatter(read_text(path))
        if frontmatter is None:
            continue
        rid = str(frontmatter.get("id") or "").strip()
        if not rid:
            continue
        reqs.append({
            "id": rid,
            "title": str(frontmatter.get("title") or "").strip(),
            "kind": str(frontmatter.get("kind") or "").strip() or "unspecified",
            "status": str(frontmatter.get("status") or "").strip() or "draft",
            "created": str(frontmatter.get("created") or "").strip(),
            "updated": str(frontmatter.get("updated") or "").strip(),
            "iteration": str(frontmatter.get("iteration") or "").strip(),
            "blocked_by": as_list(frontmatter.get("blocked_by")),
            "background": first_paragraph(body),
        })
    if not reqs:
        return [], f"没有找到任何 REQ：{req_dir}"
    return reqs, None


def ordered_kinds(kinds: set[str]) -> list[str]:
    known = [k for k in KIND_ORDER if k in kinds]
    extra = sorted(k for k in kinds if k not in KIND_ORDER)
    return known + extra


def ordered_statuses(statuses: set[str]) -> list[str]:
    known = [s for s in STATUS_ORDER if s in statuses]
    extra = sorted(s for s in statuses if s not in STATUS_ORDER)
    return known + extra


def render_req(req: dict[str, Any]) -> str:
    deps = "、".join(req["blocked_by"]) if req["blocked_by"] else "无"
    meta = " · ".join([
        f"类型：{esc(kind_label(req['kind']))}",
        f"状态：{esc(status_label(req['status']))}",
        f"生成日期：{esc(req['created'] or '—')}",
        f"更新日期：{esc(req['updated'] or '—')}",
        f"轮次：{esc(req['iteration'] or '—')}",
        f"依赖：{esc(deps)}",
    ])
    if req["background"]:
        body = f'<p class="bg">{esc(req["background"])}</p>'
    else:
        body = '<p class="muted">（缺「问题与目标」背景）</p>'
    return (
        f'<details class="req"><summary><code>{esc(req["id"])}</code> '
        f'{esc(req["title"])}</summary><div class="meta">{meta}</div>{body}</details>'
    )


def render_kind(kind: str, by_status: dict[str, list[dict[str, Any]]]) -> str:
    total = sum(len(items) for items in by_status.values())
    parts = [
        f'<details open class="kind"><summary>{esc(kind_label(kind))}'
        f'<span class="count">{total}</span></summary>'
    ]
    for status in ordered_statuses(set(by_status)):
        items = by_status[status]
        parts.append(
            f'<details class="status"><summary>{esc(status_label(status))}'
            f'<span class="count">{len(items)}</span></summary>'
        )
        parts.extend(render_req(req) for req in items)
        parts.append("</details>")
    parts.append("</details>")
    return "".join(parts)


def group_by_kind_status(reqs: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for req in reqs:
        grouped.setdefault(req["kind"], {}).setdefault(req["status"], []).append(req)
    return grouped


def build_html(skill: str, reqs: list[dict[str, Any]], generated_at: str) -> str:
    grouped = group_by_kind_status(reqs)
    counts = " · ".join(
        f"{kind_label(kind)} {sum(len(v) for v in grouped[kind].values())}"
        for kind in ordered_kinds(set(grouped))
    )
    topbar = (
        '<div class="topbar">'
        f'<strong>{esc(skill)} · REQ 报告</strong>'
        f'<span class="stat">共 {len(reqs)} 条</span>'
        f'<span class="stat">{esc(counts)}</span>'
        "</div>"
    )
    if grouped:
        sections = "".join(render_kind(kind, grouped[kind]) for kind in ordered_kinds(set(grouped)))
    else:
        sections = '<p class="muted">该筛选下暂无 REQ</p>'
    return f"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(skill)} · REQ 报告</title>
<style>{CSS}</style>
</head>
<body>
{topbar}
<header>
  <h1>{esc(skill)} · REQ 报告</h1>
  <p class="meta">按类型 → 状态分组；点开每条 REQ 看详情。生成于 {esc(generated_at)}</p>
</header>
<main>
{sections}
</main>
<footer>shy-skill-suite · render_reqs.py</footer>
</body>
</html>
"""


def render(
    root: str,
    skill: str,
    kind: str | None = None,
    out_path: str | None = None,
) -> dict[str, Any]:
    base = Path(root)
    if not base.is_dir():
        return {"status": "error", "error": f"root 不是目录：{base}"}
    base = base.resolve()
    reqs, err = load_reqs(base, skill)
    if err:
        return {"status": "error", "error": err}
    if kind:
        reqs = [req for req in reqs if req["kind"] == kind]

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    html_text = build_html(skill, reqs, generated_at)
    destination = Path(out_path) if out_path else base / "reports" / f"{skill}-reqs.html"
    write_text(destination, html_text)
    return {
        "status": "success",
        "report": str(destination),
        "skill": skill,
        "reqs": len(reqs),
        "kinds": sorted({req["kind"] for req in reqs}),
    }


def _open_disabled_reason() -> str | None:
    for name in _OPEN_DISABLE_ENV:
        value = os.environ.get(name, "").strip().lower()
        if value and value not in ("0", "false", "no"):
            return name
    return None


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="把单个技能的 REQ 渲染成单文件自包含 HTML（reports/<skill>-reqs.html）。",
        epilog=(
            "示例:\n"
            "  python render_reqs.py --root . --skill shy-skill-suite\n"
            "  python render_reqs.py --root . --skill shy-skill-suite --kind feature\n"
            "  python render_reqs.py --root . --skill shy-skill-suite --out /tmp/reqs.html\n"
            "  python render_reqs.py --root . --skill shy-skill-suite --no-open\n"
            "\n"
            "参数:\n"
            "  --root   仓库根（默认 .）；读 <root>/docs/<skill>/requirements/REQ-*.md\n"
            "  --skill  （必填）只渲染该技能\n"
            "  --kind   只看某类 REQ（feature/fix/refactor/docs/hygiene/unspecified）\n"
            "  --out    输出 HTML 路径（缺省 <root>/reports/<skill>-reqs.html，原地覆盖）\n"
            "  --no-open 生成后不自动打开浏览器\n"
            "\n"
            "默认生成后用浏览器打开报告；关闭方式（任一即可）：--no-open，或设环境变量\n"
            "SHY_NO_OPEN / CI / NO_BROWSER 为真值。报告单文件、无外部资源、无网络。\n"
            "\n"
            "退出码:\n"
            "  0  成功（已写出 HTML）\n"
            "  1  技能不存在 / 无 REQ / root 非法 / 写出失败\n"
            "  2  参数错误（缺 --skill 等）\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", default=".", help="Repo root（默认 .）")
    parser.add_argument("--skill", required=True, help="（必填）只渲染该技能")
    parser.add_argument("--kind", help="只看某类 REQ（feature/fix/refactor/docs/hygiene/unspecified）")
    parser.add_argument("--out", "-o", help="输出 HTML 路径（缺省 <root>/reports/<skill>-reqs.html）")
    parser.add_argument("--no-open", action="store_true", help="生成后不自动打开浏览器")
    args = parser.parse_args()

    result = render(args.root, args.skill, args.kind, args.out)
    if result.get("status") == "success":
        if args.no_open:
            result["opened"] = False
            result["open_skipped"] = "--no-open"
        else:
            skip = _open_disabled_reason()
            if skip:
                result["opened"] = False
                result["open_skipped"] = skip
            else:
                try:
                    result["opened"] = webbrowser.open(Path(result["report"]).resolve().as_uri())
                except Exception:  # noqa: BLE001 - 无显示环境不报错
                    result["opened"] = False
    stream = sys.stderr if result.get("status") == "error" else sys.stdout
    print(json.dumps(result, indent=2, ensure_ascii=True), file=stream)
    return 1 if result.get("status") == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
