#!/usr/bin/env python3
"""轻量脚手架：创建一个技能目录骨架。

默认只生成 `<path>/<name>/SKILL.md`（合法 frontmatter + H1 标题）——不建子目录、
不生成需求文档、不填领域内容；技能靠后续迭代完善。

加 `--project` 走**开发层**：额外建 `docs/<name>/requirements/`（目录），并在项目根
（`--path` 的父目录）追加 `.gitignore` 条目（`*-workspace/` / `reports/` /
`__pycache__/`，仅缺失时追加）。**仍不预建** `scripts/` / `references/` / `assets/` /
`evals/` / `commands/` 空目录，**不写 REQ 正文**（REQ 由阶段 1 产出）。

用法:
    python scaffold_skill.py <name> [--path skills] [--description "<触发描述>"] [--force] [--project]

`--description` 省略时写入显式占位 `TODO: ...`，便于需求明确前先起骨架。
输出 JSON（含 `status` / `skill_dir` / `files`；`--project` 时另有 `project` 字段）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from skill_utils import force_utf8_stdio, read_text, write_text

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLACEHOLDER = "TODO: 一句话说明它做什么、何时触发"
# 开发层要补的 .gitignore 条目（工作区 / 报告 / Python 缓存）。
GITIGNORE_ENTRIES = ("*-workspace/", "reports/", "__pycache__/")


def validate_name(name: str) -> str | None:
    if not name:
        return "name 不能为空"
    if len(name) > 64:
        return "name 超过 64 字符"
    if not NAME_RE.match(name):
        return "name 必须是小写字母/数字/连字符，且无首尾或连续连字符"
    return None


def yaml_scalar(value: str) -> str:
    """把字符串安全地写成 YAML 双引号标量。"""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()
    return f'"{escaped}"'


def build_skill_md(name: str, description: str) -> str:
    title = " ".join(word.capitalize() for word in name.split("-"))
    return f"---\nname: {name}\ndescription: {yaml_scalar(description)}\n---\n\n# {title}\n"


def ensure_gitignore(project_root: Path) -> dict:
    """仅在缺失时把 `GITIGNORE_ENTRIES` 追加到项目根 `.gitignore`。

    不重复、不覆盖已有内容：按整行（strip 后）判存在，已存在的条目不动。
    返回 `{path, added, present}`——`added` 为空表示本来就齐、本次未改文件。
    """
    gi = project_root / ".gitignore"
    lines = read_text(gi).splitlines() if gi.is_file() else []
    present = {ln.strip() for ln in lines}
    added = [entry for entry in GITIGNORE_ENTRIES if entry not in present]
    result = {
        "path": str(gi),
        "added": added,
        "present": [entry for entry in GITIGNORE_ENTRIES if entry in present],
    }
    if not added:
        return result
    if lines:
        text = "\n".join(lines).rstrip("\n") + "\n" + "\n".join(added) + "\n"
    else:
        text = "# 技能工作区 / 生成物（scaffold_skill.py --project 追加）\n" + "\n".join(added) + "\n"
    write_text(gi, text)
    return result


def scaffold(name: str, path: str, description: str | None, force: bool,
             project: bool = False) -> dict:
    error = validate_name(name)
    if error:
        return {"status": "error", "error": error}

    skill_dir = Path(path) / name
    skill_md = skill_dir / "SKILL.md"
    skipped = skill_md.exists() and not force

    backup = None
    if not skipped:
        if skill_md.exists() and force:
            backup_path = skill_md.with_name(skill_md.name + ".bak")
            write_text(backup_path, read_text(skill_md))
            backup = str(backup_path)
        write_text(skill_md, build_skill_md(name, description or PLACEHOLDER))

    result: dict = {
        "status": "skipped" if skipped else "success",
        "skill_dir": str(skill_dir),
        "files": [str(skill_md)],
    }
    if skipped:
        result["reason"] = f"已存在，未改动: {skill_md}（要覆盖请加 --force）"
    else:
        result["description"] = description or PLACEHOLDER
        if backup:
            result["backup"] = backup

    if project:
        # 项目根 = 技能父目录的父目录（`--path skills` → `.`）；docs 与 skills 同级。
        project_root = Path(path).parent
        docs_dir = project_root / "docs" / name / "requirements"
        docs_dir.mkdir(parents=True, exist_ok=True)
        result["project"] = {
            "project_root": str(project_root),
            "docs_dir": str(docs_dir),
            "gitignore": ensure_gitignore(project_root),
        }
    return result


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description=(
            "创建一个技能骨架。默认只生成 <path>/<name>/SKILL.md（不建子目录、不生成需求文档）；"
            "加 --project 走开发层，另建 docs/<name>/requirements/ 并追加 .gitignore 条目。"
        ),
        epilog=(
            "示例:\n"
            '  python scaffold_skill.py my-skill --description "当用户要 X 时使用本技能"\n'
            "  python scaffold_skill.py my-skill --path skills --project --description \"当用户要 X 时使用本技能\"\n"
            "  python scaffold_skill.py my-skill --path skills --force\n"
            "\n"
            "参数:\n"
            "  name           技能名（kebab-case，与目录同名）\n"
            "  --path         技能父目录（默认 skills）；--project 时项目根取其父目录\n"
            "  --description  触发描述；省略则写 TODO 占位\n"
            "  --force        覆盖已有 SKILL.md（先备份为 SKILL.md.bak）\n"
            "  --project      开发层：建 docs/<name>/requirements/ 并追加 .gitignore 条目\n"
            "                 （*-workspace/ / reports/ / __pycache__/，仅缺失时追加；不预建子目录、不写 REQ）\n"
            "\n"
            "退出码:\n"
            "  0  成功，或目标已存在且未加 --force（status: skipped，幂等）\n"
            "  1  名称非法\n"
            "  2  参数错误\n"
            "\n"
            "--force 会覆盖已有 SKILL.md，但先把它备份为 SKILL.md.bak（输出里的 backup 字段）。\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("name", help="Skill name (kebab-case, matches the directory)")
    parser.add_argument("--path", default="skills", help="Parent directory for skills (default: skills)")
    parser.add_argument("--description", help="Trigger description; omit for a TODO placeholder")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing SKILL.md (backs it up to .bak first)")
    parser.add_argument(
        "--project", action="store_true",
        help="开发层：建 docs/<name>/requirements/ 并追加 .gitignore 条目（仅缺失时；不预建子目录、不写 REQ）",
    )
    args = parser.parse_args()

    result = scaffold(args.name, args.path, args.description, args.force, args.project)
    stream = sys.stderr if result["status"] == "error" else sys.stdout
    print(json.dumps(result, indent=2, ensure_ascii=False), file=stream)
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
