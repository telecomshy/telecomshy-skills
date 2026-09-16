#!/usr/bin/env python3
"""技能校验器：只查结构与规范（不做语义 / 质量审查）。

校验内容：
- frontmatter：必填 `name`/`description`；`name` 与目录同名、kebab-case、≤64；
  `description` ≤1024、不含尖括号、含 `TODO` 记 warning；
  顶层只允许 `agentskills.io` 基础字段 {name, description, license, compatibility, metadata, allowed-tools}
  加上客户端扩展字段 {disable-model-invocation, argument-hint}；多余字段报错。
- 结构：`SKILL.md` 大小写精确；技能目录内不得有 `README.md`。
- 引用：`SKILL.md` 与 `references/*.md` 里的相对 `.md` / 脚本链接必须指向存在的文件。

用法:
    python validate_skill.py <skill_dir>

输出 JSON：`{status, skill, errors, warnings}`；有 error 时退出码 1。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from skill_utils import force_utf8_stdio, parse_frontmatter, read_text

BASE_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
EXTENSION_FIELDS = {"disable-model-invocation", "argument-hint"}
ALLOWED_FIELDS = BASE_FIELDS | EXTENSION_FIELDS
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
REF_EXT_RE = re.compile(r"\.(md|py|sh|ps1|js|ts)$")
KEYVAL_RE = re.compile(r"^\s*[A-Za-z0-9_-]+:\s*(.+)$")


def yaml_hazards(content: str) -> list[str]:
    """检出"值含未加引号的 ': '"这类 PyYAML 会拒绝、而轻量解析器会放过的写法。"""
    parts = content.split("---", 2)
    if len(parts) < 3:
        return []
    hazards: list[str] = []
    for line in parts[1].splitlines():
        match = KEYVAL_RE.match(line)
        if not match:
            continue
        value = match.group(1).strip()
        if not value or value[0] in "\"'[{>|":
            continue
        if ": " in value:
            hazards.append(line.strip())
    return hazards


def check_references(skill_dir: Path) -> list[str]:
    """检查 SKILL.md 与 references/*.md 里的相对链接是否有悬空。"""
    errors: list[str] = []
    files = [skill_dir / "SKILL.md"]
    refs = skill_dir / "references"
    if refs.is_dir():
        files += sorted(refs.glob("*.md"))

    for file in files:
        if not file.is_file():
            continue
        text = FENCE_RE.sub("", read_text(file))
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "/")):
                continue
            if not REF_EXT_RE.search(target):
                continue
            if not (file.parent / target).exists():
                rel = file.relative_to(skill_dir).as_posix()
                errors.append(f"{rel}: 悬空引用 → {target}")
    return errors


def validate(skill_dir: str) -> dict:
    path = Path(skill_dir)
    errors: list[str] = []
    warnings: list[str] = []

    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        if path.is_dir():
            for entry in path.iterdir():
                if entry.name.lower() == "skill.md" and entry.name != "SKILL.md":
                    errors.append(f"发现 '{entry.name}'，文件名必须精确为 'SKILL.md'")
                    break
            else:
                errors.append("SKILL.md 不存在")
        else:
            errors.append(f"不是目录: {path}")
        return {"status": "error", "skill": path.name, "errors": errors, "warnings": warnings}

    if (path / "README.md").exists():
        errors.append("技能目录内不应有 README.md（README 只放仓库根）")

    frontmatter, _body, parse_errors = parse_frontmatter(read_text(skill_md))
    if frontmatter is None:
        errors.append("frontmatter 解析失败: " + ("; ".join(parse_errors) or "未知原因"))
        return {"status": "error", "skill": path.name, "errors": errors, "warnings": warnings}

    for hazard in yaml_hazards(read_text(skill_md)):
        errors.append(f"疑似非法 YAML（值含未加引号的 ': '）: {hazard}")

    extra = set(frontmatter) - ALLOWED_FIELDS
    if extra:
        errors.append(
            f"frontmatter 顶层多余字段: {', '.join(sorted(extra))}"
            f"（允许: {', '.join(sorted(ALLOWED_FIELDS))}）"
        )

    name = str(frontmatter.get("name", "")).strip()
    if not name:
        errors.append("缺少 name")
    else:
        if len(name) > 64:
            errors.append(f"name 超过 64 字符（{len(name)}）")
        if not NAME_RE.match(name):
            errors.append(f"name '{name}' 必须是小写字母/数字/连字符，且无首尾或连续连字符")
        if name != path.name:
            errors.append(f"name '{name}' 与目录名 '{path.name}' 不一致")

    description = str(frontmatter.get("description", "")).strip()
    if not description:
        errors.append("缺少 description")
    else:
        if len(description) > 1024:
            errors.append(f"description 超过 1024 字符（{len(description)}）")
        if "<" in description or ">" in description:
            errors.append("description 不能包含尖括号 < 或 >")
        if "TODO" in description:
            warnings.append("description 含 TODO 占位，需替换为真实触发描述")

    compatibility = frontmatter.get("compatibility")
    if compatibility and len(str(compatibility)) > 500:
        errors.append(f"compatibility 超过 500 字符（{len(str(compatibility))}）")

    errors.extend(check_references(path))

    return {
        "status": "error" if errors else "ok",
        "skill": name or path.name,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(description="Validate a skill's structure and frontmatter (spec only)")
    parser.add_argument("path", help="Path to the skill directory")
    args = parser.parse_args()

    result = validate(args.path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
