#!/usr/bin/env python3
"""本地需求跟踪（tracker 查询）。

扫描 `docs/<skill>/requirements/REQ-*.md` 的 frontmatter，输出：

- **frontier**：现在就能开始的 REQ（`status ∈ {ready, in-progress}`，且所有 `blocked_by` 都已 `done`）
- **blocked**：在等前置 REQ 的
- **deferred**：`status: deferred` 的（附 `defer_reason`），不算 frontier
- **errors**：`blocked_by` / `superseded_by` 悬空、缺 `id`、同一技能内重复 `id`
- **warnings**：`blocked_by` 指向 `out-of-scope` / `deferred`、缺 `skill` 字段
- **by_kind**：按 `kind`（feature / fix / refactor / docs / hygiene）分组的 status 计数（供"功能 / 问题"两个读数）
- 状态汇总

本脚本只管**排期**（frontier / 依赖 / 状态），**不管回归**：Spec 轴的回归由复审的
**不变量集**承担（见 `references/reviewing-skills.md` Step 3），不靠状态戳。

编号约定：**每个技能各自从 `REQ-0001` 起**（唯一性按 `(skill, id)` 判定）。
`blocked_by` 默认在同技能内解析；跨技能写 `<skill>:REQ-NNNN`。

frontier 由状态**推导**，不落盘索引文件（避免派生索引过期）。

用法:
    python track_requirements.py [--root .] [--skill <name>] [--view summary|overview] [--full] [--output <path>]

默认打**有界摘要**（frontier / blocked / deferred 只给 id + title）；`--full` 打完整 JSON，
`--output <path>` 把完整 JSON 写到文件（大仓库避免被输出上限截断）；
`--view overview` 打**终端人读摘要**（`kind × status` 计数 + frontier + 按技能分组列 title）。

**stdout 一律输出纯 ASCII 转义 JSON**（`ensure_ascii=True`）：Windows PowerShell 5.1
管道会按控制台代码页解码再以 US-ASCII 重编码，非 ASCII 字节会被破坏、甚至吞掉紧随的
JSON 定界符，令下游 `json.loads` 报 `Invalid control character`。`--output` 写文件仍是
UTF-8（不过管道），人读走 `--view overview`。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from skill_utils import (
    KIND_LABELS,
    KIND_ORDER,
    force_utf8_stdio,
    parse_frontmatter,
    read_text,
    write_text,
)

RESOLVED = {"done"}
ACTIONABLE = {"ready", "in-progress"}


def as_list(value: Any) -> list[str]:
    """把 frontmatter 值规范成字符串列表（兼容内联 ``[A, B]`` 与块列表）。"""
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        text = str(value).strip()
        if text.startswith("[") and text.endswith("]"):
            text = text[1:-1]
        items = text.split(",") if text else []
    return [str(i).strip().strip('"').strip("'") for i in items if str(i).strip()]


def discover(root: Path, skill: str | None) -> list[Path]:
    if skill:
        base = root / "docs" / skill / "requirements"
        return sorted(base.glob("REQ-*.md")) if base.is_dir() else []
    return sorted(root.glob("docs/*/requirements/REQ-*.md"))


def load(path: Path) -> dict[str, Any]:
    frontmatter, _body, errors = parse_frontmatter(read_text(path))
    if frontmatter is None:
        return {"_path": str(path), "_parse_errors": errors}
    frontmatter["_path"] = str(path)
    return frontmatter


def resolve_blocker(ref: str, skill: str) -> tuple[str, str]:
    """把 blocked_by 引用解析成 (skill, id)；``<skill>:REQ-NNNN`` 为跨技能。"""
    if ":" in ref:
        owner, _, rid = ref.partition(":")
        return owner.strip(), rid.strip()
    return skill, ref


def analyze(reqs: list[dict[str, Any]]) -> dict[str, Any]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for req in reqs:
        if req.get("_parse_errors"):
            errors.append({"path": req["_path"], "error": "; ".join(req["_parse_errors"])})
            continue
        rid = str(req.get("id", "")).strip()
        if not rid:
            errors.append({"path": req["_path"], "error": "缺少 id"})
            continue
        skill = str(req.get("skill", "")).strip()
        if not skill:
            warnings.append({"id": rid, "warning": "缺少 skill 字段"})
        key = (skill, rid)
        if key in by_key:
            errors.append({"skill": skill, "id": rid, "error": "同一技能内重复 id"})
            continue
        by_key[key] = req

    frontier: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    all_entries: list[dict[str, Any]] = []
    summary: dict[str, int] = {}
    by_kind: dict[str, dict[str, int]] = {}

    for skill, rid in sorted(by_key):
        req = by_key[(skill, rid)]
        status = str(req.get("status", "")).strip() or "draft"
        kind = str(req.get("kind", "")).strip() or "unspecified"
        summary[status] = summary.get(status, 0) + 1
        by_kind.setdefault(kind, {})
        by_kind[kind][status] = by_kind[kind].get(status, 0) + 1
        blockers = as_list(req.get("blocked_by"))

        missing: list[str] = []
        oos: list[str] = []
        deferred_refs: list[str] = []
        unresolved: list[str] = []
        for ref in blockers:
            bkey = resolve_blocker(ref, skill)
            if bkey not in by_key:
                missing.append(ref)
                unresolved.append(ref)
                continue
            bstatus = str(by_key[bkey].get("status", "")).strip()
            if bstatus == "out-of-scope":
                oos.append(ref)
            if bstatus == "deferred":
                deferred_refs.append(ref)
            if bstatus not in RESOLVED:
                unresolved.append(ref)

        if missing:
            errors.append({"skill": skill, "id": rid, "error": f"blocked_by 悬空: {', '.join(missing)}"})
        if oos:
            warnings.append({"skill": skill, "id": rid, "warning": f"blocked_by 指向 out-of-scope: {', '.join(oos)}"})
        if deferred_refs:
            warnings.append({"skill": skill, "id": rid, "warning": f"blocked_by 指向 deferred: {', '.join(deferred_refs)}（需先恢复）"})

        superseded_by = str(req.get("superseded_by", "")).strip()
        if superseded_by and resolve_blocker(superseded_by, skill) not in by_key:
            errors.append({"skill": skill, "id": rid, "error": f"superseded_by 悬空: {superseded_by}"})

        entry = {
            "skill": skill,
            "id": rid,
            "title": str(req.get("title", "")).strip(),
            "status": status,
            "kind": kind,
            "path": req["_path"],
        }
        if superseded_by:
            entry["superseded_by"] = superseded_by
        all_entries.append(entry)
        if status == "deferred":
            defer_reason = str(req.get("defer_reason", "")).strip()
            if not defer_reason:
                warnings.append({"skill": skill, "id": rid, "warning": "deferred 缺 defer_reason"})
            deferred.append({**entry, "defer_reason": defer_reason})
        elif status in ACTIONABLE:
            if unresolved:
                blocked.append({**entry, "waiting_on": unresolved})
            else:
                frontier.append(entry)

    return {
        "status": "errors" if errors else "ok",
        "total": len(by_key),
        "summary": summary,
        "by_kind": by_kind,
        "all": all_entries,
        "frontier": frontier,
        "blocked": blocked,
        "deferred": deferred,
        "errors": errors,
        "warnings": warnings,
    }


def filter_by_kind(result: dict[str, Any], kind: str) -> dict[str, Any]:
    """按 kind 过滤**展示列表**（在 analyze 全集之后做）。

    引用（blocked_by / superseded_by）已对照**全集**解析过，所以过滤不会
    把跨 kind 的合法引用误判成悬空——kind 只影响展示与读数，不影响 status。
    """
    out = dict(result)
    keep = lambda items: [e for e in items if e.get("kind") == kind]  # noqa: E731
    out["all"] = keep(result.get("all", []))
    out["frontier"] = keep(result["frontier"])
    out["blocked"] = keep(result["blocked"])
    out["deferred"] = keep(result["deferred"])
    summary = result["by_kind"].get(kind, {})
    out["summary"] = summary
    out["total"] = sum(summary.values())
    out["by_kind"] = {kind: summary}
    return out


def summarize(result: dict[str, Any]) -> dict[str, Any]:
    """默认输出：有界摘要——frontier / blocked / deferred 只给 id + title。"""

    def brief(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in items:
            row = {"id": item["id"], "title": item.get("title", "")}
            if "waiting_on" in item:
                row["waiting_on"] = item["waiting_on"]
            out.append(row)
        return out

    return {
        "status": result["status"],
        "total": result["total"],
        "summary": result["summary"],
        "by_kind": result["by_kind"],
        "frontier": brief(result["frontier"]),
        "blocked": brief(result["blocked"]),
        "deferred": brief(result["deferred"]),
        "errors": result["errors"],
        "warnings": result["warnings"],
        "root": result["root"],
        "files": result["files"],
        "hint": "完整数据（含 path / defer_reason）用 --full，或 --output <path> 写文件；--kind <feature|fix|...> 只看一类",
    }


def render_overview(result: dict[str, Any], focus_skill: str | None = None) -> str:
    """终端人读摘要：`kind × status` 计数 + frontier + 按技能分组列 title。

    纯文本（不是 JSON）：给人扫一眼"做到哪了"。脚本仍只做排期，不出白话——
    唯一例外是 `--skill` 聚焦时给一行**白话 kind 计数摘要**（如
    `shy-skill-suite：新增功能 3 / 修复缺陷 1`），供 `/shy-reqs` 直接引用。
    """
    lines: list[str] = []
    by_kind = result.get("by_kind") or {}
    if focus_skill:
        parts = []
        for kind in KIND_ORDER:
            counts = by_kind.get(kind)
            n = sum(counts.values()) if counts else 0
            if n:
                parts.append(f"{KIND_LABELS.get(kind, kind)} {n}")
        lines.append(f"{focus_skill}：{' / '.join(parts) if parts else '（无 REQ）'}")
        lines.append("")
    lines.append(f"REQ 总览：共 {result['total']} 条")
    lines.append("")
    lines.append("kind × status 计数：")
    if by_kind:
        for kind in sorted(by_kind):
            counts = by_kind[kind]
            parts = " ".join(f"{st}={counts[st]}" for st in sorted(counts))
            lines.append(f"  {kind}: {parts}")
    else:
        lines.append("  （无）")
    lines.append("")
    frontier = result.get("frontier") or []
    lines.append(f"frontier（{len(frontier)} 条，现在能开始）：")
    if frontier:
        for entry in frontier:
            lines.append(f"  {entry.get('skill', '')}  {entry['id']}  {entry.get('title', '')}")
    else:
        lines.append("  （无）")
    lines.append("")
    lines.append("按技能分组（全部 REQ）：")
    by_skill: dict[str, list[dict[str, Any]]] = {}
    for entry in result.get("all") or []:
        by_skill.setdefault(str(entry.get("skill", "")), []).append(entry)
    if by_skill:
        for skill_name in sorted(by_skill):
            lines.append(f"  [{skill_name}]")
            for entry in by_skill[skill_name]:
                lines.append(
                    f"    {entry['id']}  [{entry.get('status', '')}/{entry.get('kind', '')}]  "
                    f"{entry.get('title', '')}"
                )
    else:
        lines.append("  （无）")
    lines.append("")
    lines.append(f"errors：{len(result.get('errors') or [])} 条；warnings：{len(result.get('warnings') or [])} 条")
    return "\n".join(lines)


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description=(
            "扫描 docs/<skill>/requirements/ 的 REQ frontmatter，输出 frontier / blocked / "
            "deferred 与错误。只管排期，不管回归。"
        ),
        epilog=(
            "示例:\n"
            "  python track_requirements.py --root .\n"
            "  python track_requirements.py --root . --skill my-skill\n"
            "  python track_requirements.py --root . --view overview\n"
            "  python track_requirements.py --root . --full\n"
            "  python track_requirements.py --root . --output reqs.json\n"
            "\n"
            "退出码:\n"
            "  0  无 error\n"
            "  1  存在 error（blocked_by / superseded_by 悬空 / 缺 id / 同技能重复 id）\n"
            "  2  参数错误\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", default=".", help="Repo root to scan (default: .)")
    parser.add_argument("--skill", help="Limit to docs/<skill>/requirements/")
    parser.add_argument("--kind", help="Only include REQs with this kind（feature/fix/refactor/docs/hygiene）")
    parser.add_argument(
        "--view", choices=("summary", "overview"), default="summary",
        help="summary=默认有界 JSON；overview=终端人读摘要（kind × status 计数 + frontier + 按技能分组列 title；--skill 聚焦时附一行白话计数摘要）",
    )
    parser.add_argument("--full", action="store_true", help="Print the full JSON instead of the bounded summary")
    parser.add_argument("--output", "-o", help="Write the full JSON to this path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = discover(root, args.skill)
    result = analyze([load(p) for p in files])  # 全集分析：跨 kind 引用才能正确解析
    result["root"] = str(root)
    result["files"] = len(files)
    if args.kind:
        result = filter_by_kind(result, args.kind)

    if args.output:
        # 文件不过 shell 管道，保留 UTF-8（可读）。
        write_text(args.output, json.dumps(result, indent=2, ensure_ascii=False))
    if args.view == "overview":
        print(render_overview(result, focus_skill=args.skill))
        return 1 if result["errors"] else 0
    payload = result if args.full else summarize(result)
    # stdout 走管道：ASCII 转义，避免 Windows PowerShell 5.1 的代码页重编码破坏 JSON。
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
