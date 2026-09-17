#!/usr/bin/env python3
"""本地需求跟踪（tracker 查询）。

扫描 `docs/<skill>/requirements/REQ-*.md` 的 frontmatter，输出：

- **frontier**：现在就能开始的 REQ（`status ∈ {ready, in-progress}`，且所有 `blocked_by` 都已 `done`）
- **blocked**：在等前置 REQ 的
- **deferred**：`status: deferred` 的（附 `defer_reason`），不算 frontier
- **regression_debt**：`status: done` 但需复核的 REQ（见下），附 `reasons`
- **errors**：`blocked_by` 悬空、缺 `id`、同一技能内重复 `id`
- **warnings**：`blocked_by` 指向 `out-of-scope` / `deferred`、缺 `skill` 字段
- 状态汇总

**回归债（regression_debt）**：`done` 只保证"写的那一刻成立"。技能没有编译期，
后续 REQ 改同一份文本会让旧验收静默失效，故 `done` 需带时效。一条 REQ 入债的条件（满足其一）：

- `no last_verified`：从未做过回归验证（缺 frontmatter `last_verified`）
- `updated after last_verified`：`updated` 晚于 `last_verified`
- `unchecked criteria`：`## 验收标准` 有未勾选且**未标「待验证」**的条目

脚本只报"该复核哪些"，不跑验收（验收标准是 prose，不可机器执行）。

编号约定：**每个技能各自从 `REQ-0001` 起**（唯一性按 `(skill, id)` 判定）。
`blocked_by` 默认在同技能内解析；跨技能写 `<skill>:REQ-NNNN`。

frontier 由状态**推导**，不落盘索引文件（避免派生索引过期）。

用法:
    python track_requirements.py [--root .] [--skill <name>]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from skill_utils import force_utf8_stdio, parse_frontmatter, read_text

RESOLVED = {"done"}
ACTIONABLE = {"ready", "in-progress"}

_CRITERIA_HEADING_RE = re.compile(r"^##\s*验收标准\s*$")
_HEADING_RE = re.compile(r"^##\s+")
_CRITERION_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s*(.*)$")
_PENDING_MARK = "待验证"


def scan_criteria(body: str) -> dict[str, int]:
    """统计 `## 验收标准` 节的勾选情况。

    返回 ``{"checked": n, "unchecked": n, "pending": n}``；``pending`` 是
    未勾选但标了「待验证」的条目（按规范允许，不计入回归债）。
    """
    checked = unchecked = pending = 0
    in_section = False
    for line in body.splitlines():
        if _HEADING_RE.match(line):
            in_section = bool(_CRITERIA_HEADING_RE.match(line))
            continue
        if not in_section:
            continue
        match = _CRITERION_RE.match(line)
        if not match:
            continue
        if match.group(1).strip():
            checked += 1
        elif _PENDING_MARK in match.group(2):
            pending += 1
        else:
            unchecked += 1
    return {"checked": checked, "unchecked": unchecked, "pending": pending}


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
    frontmatter, body, errors = parse_frontmatter(read_text(path))
    if frontmatter is None:
        return {"_path": str(path), "_parse_errors": errors}
    frontmatter["_path"] = str(path)
    frontmatter["_criteria"] = scan_criteria(body)
    return frontmatter


def regression_reasons(req: dict[str, Any]) -> list[str]:
    """判断一条 `done` REQ 是否入回归债；返回原因列表（空 = 无债）。"""
    reasons: list[str] = []
    last_verified = str(req.get("last_verified", "")).strip()
    updated = str(req.get("updated", "")).strip()
    if not last_verified:
        reasons.append("no last_verified")
    elif updated and updated > last_verified:
        reasons.append("updated after last_verified")
    unchecked = (req.get("_criteria") or {}).get("unchecked", 0)
    if unchecked:
        reasons.append(f"unchecked criteria ({unchecked})")
    return reasons


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
    regression_debt: list[dict[str, Any]] = []
    summary: dict[str, int] = {}

    for skill, rid in sorted(by_key):
        req = by_key[(skill, rid)]
        status = str(req.get("status", "")).strip() or "draft"
        summary[status] = summary.get(status, 0) + 1
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

        entry = {
            "skill": skill,
            "id": rid,
            "title": str(req.get("title", "")).strip(),
            "status": status,
            "path": req["_path"],
        }
        if status == "deferred":
            deferred.append({**entry, "defer_reason": str(req.get("defer_reason", "")).strip()})
        elif status in ACTIONABLE:
            if unresolved:
                blocked.append({**entry, "waiting_on": unresolved})
            else:
                frontier.append(entry)
        elif status == "done":
            reasons = regression_reasons(req)
            if reasons:
                regression_debt.append(
                    {
                        **entry,
                        "last_verified": str(req.get("last_verified", "")).strip(),
                        "criteria": req.get("_criteria") or {},
                        "reasons": reasons,
                    }
                )

    return {
        "status": "errors" if errors else "ok",
        "total": len(by_key),
        "summary": summary,
        "frontier": frontier,
        "blocked": blocked,
        "deferred": deferred,
        "regression_debt": regression_debt,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description=(
            "扫描 docs/<skill>/requirements/ 的 REQ frontmatter，输出 frontier / blocked / "
            "deferred / regression_debt 与错误。"
        ),
        epilog=(
            "回归债 (regression_debt):\n"
            "  status: done 但需复核的 REQ。原因: no last_verified（缺 frontmatter\n"
            "  last_verified）/ updated after last_verified / unchecked criteria\n"
            "  （验收标准有未勾选且未标「待验证」的条目）。\n"
            "\n"
            "示例:\n"
            "  python track_requirements.py --root .\n"
            "  python track_requirements.py --root . --skill my-skill\n"
            "\n"
            "退出码:\n"
            "  0  无 error\n"
            "  1  存在 error（blocked_by 悬空 / 缺 id / 同技能重复 id）\n"
            "  2  参数错误\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", default=".", help="Repo root to scan (default: .)")
    parser.add_argument("--skill", help="Limit to docs/<skill>/requirements/")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = discover(root, args.skill)
    result = analyze([load(p) for p in files])
    result["root"] = str(root)
    result["files"] = len(files)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
