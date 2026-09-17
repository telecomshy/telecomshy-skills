#!/usr/bin/env python3
"""轻量脚手架：创建一个技能目录骨架（只有 SKILL.md）。

只生成目录结构——不建子目录、不生成需求文档、不填领域内容；技能靠后续迭代完善。

用法:
    python scaffold_skill.py <name> [--path skills] [--description "<触发描述>"] [--force]

生成 `<path>/<name>/SKILL.md`（合法 frontmatter + H1 标题），并输出 JSON。
`--description` 省略时写入显式占位 `TODO: ...`，便于需求明确前先起骨架。
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


def scaffold(name: str, path: str, description: str | None, force: bool) -> dict:
    error = validate_name(name)
    if error:
        return {"status": "error", "error": error}

    skill_dir = Path(path) / name
    skill_md = skill_dir / "SKILL.md"

    if skill_md.exists() and not force:
        return {
            "status": "skipped",
            "skill_dir": str(skill_dir),
            "files": [str(skill_md)],
            "reason": f"已存在，未改动: {skill_md}（要覆盖请加 --force）",
        }

    backup = None
    if skill_md.exists() and force:
        backup_path = skill_md.with_name(skill_md.name + ".bak")
        write_text(backup_path, read_text(skill_md))
        backup = str(backup_path)

    write_text(skill_md, build_skill_md(name, description or PLACEHOLDER))
    result = {
        "status": "success",
        "skill_dir": str(skill_dir),
        "files": [str(skill_md)],
        "description": description or PLACEHOLDER,
    }
    if backup:
        result["backup"] = backup
    return result


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="创建一个技能骨架（只生成 SKILL.md；不建子目录、不生成需求文档）。",
        epilog=(
            "示例:\n"
            '  python scaffold_skill.py my-skill --description "当用户要 X 时使用本技能"\n'
            "  python scaffold_skill.py my-skill --path skills --force\n"
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
    args = parser.parse_args()

    result = scaffold(args.name, args.path, args.description, args.force)
    stream = sys.stderr if result["status"] == "error" else sys.stdout
    print(json.dumps(result, indent=2, ensure_ascii=False), file=stream)
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
