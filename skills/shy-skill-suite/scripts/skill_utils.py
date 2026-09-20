#!/usr/bin/env python3
"""技能开发套件 · 共享工具。

标准库实现，无第三方依赖。所有读写显式使用 UTF-8，避免 Windows 默认 GBK 报错。

用法:
    from skill_utils import load_skill, has_cjk, force_utf8_stdio
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_CJK_RE = re.compile(r"[\u3400-\u9fff]")

# 有效性轴覆盖的技能文件（相对技能根）；触发轴只看 description。
EFFECTIVENESS_PARTS = ("references", "scripts", "assets")
EFFECTIVENESS_EVAL = ("evals", "effectiveness.json")


def force_utf8_stdio() -> None:
    """让 stdout/stderr 以 UTF-8 输出，避免非 ASCII 内容在 GBK 控制台崩溃。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def has_cjk(text: str) -> bool:
    """判断文本是否含中日韩字符（用于中英文模板切换）。"""
    return bool(_CJK_RE.search(text or ""))


def read_text(path: str | Path) -> str:
    """按 UTF-8 读取文本并去掉可能存在的 BOM。"""
    return Path(path).read_text(encoding="utf-8").lstrip("\ufeff")


def write_text(path: str | Path, text: str) -> None:
    """按 UTF-8（无 BOM）写入，必要时创建父目录。"""
    p = Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _strip_scalar(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _parse_block(block: list[str]) -> Any:
    """把缩进块解析成列表（``- `` 行）或映射（``key: value`` 行）。"""
    if not block:
        return {}
    if all(line.strip().startswith("- ") for line in block):
        return [_strip_scalar(line.strip()[2:]) for line in block]
    mapping: dict[str, Any] = {}
    for line in block:
        match = re.match(r"^\s*([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            mapping[match.group(1)] = _strip_scalar(match.group(2))
    return mapping


def parse_frontmatter(content: str) -> tuple[dict[str, Any] | None, str, list[str]]:
    """解析 SKILL.md 的 YAML frontmatter。

    返回 (frontmatter_dict, body, errors)。轻量解析以避免 PyYAML 依赖：
    支持单行键值、``>`` / ``|`` 折叠标量、``- `` 列表、以及缩进映射（如 ``metadata``）。
    """
    errors: list[str] = []
    content = content.lstrip("\ufeff")

    if not content.startswith("---"):
        return None, content, ["Missing opening '---' delimiter"]

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content, ["Missing closing '---' delimiter"]

    lines = parts[1].split("\n")
    body = parts[2].strip()

    frontmatter: dict[str, Any] = {}
    i = 0
    total = len(lines)
    while i < total:
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue

        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not match:
            i += 1
            continue

        key = match.group(1)
        value = match.group(2).strip()

        if value in (">", "|"):
            block: list[str] = []
            i += 1
            while i < total and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                if lines[i].strip():
                    block.append(lines[i].strip())
                i += 1
            frontmatter[key] = " ".join(block).strip()
            continue

        if value:
            frontmatter[key] = _strip_scalar(value)
            i += 1
            continue

        block = []
        i += 1
        while i < total and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
            if lines[i].strip():
                block.append(lines[i])
            i += 1
        frontmatter[key] = _parse_block(block)

    if not frontmatter:
        return None, body, ["Empty frontmatter"]

    return frontmatter, body, errors


def parse_frontmatter_simple(content: str) -> tuple[dict[str, Any] | None, str]:
    """``parse_frontmatter`` 的简化版，只返回 (frontmatter, body)。"""
    frontmatter, body, _ = parse_frontmatter(content)
    return frontmatter, body


def load_skill(skill_dir: str | Path) -> tuple[dict[str, Any] | None, str, list[str]]:
    """读取技能目录下的 SKILL.md 并解析。"""
    skill_md = Path(skill_dir) / "SKILL.md"
    if not skill_md.is_file():
        return None, "", [f"SKILL.md not found: {skill_md}"]
    return parse_frontmatter(read_text(skill_md))


# --------------------------------------------------------------------------- #
# 证据指纹（分轴、确定性）
#
# eval 是独立取证路径；复审要判断手上的证据是不是**当前技能版本**产的，就得有指纹。
# 粒度刻意分轴：改 SKILL.md 正文不作废触发证据，改 description 才作废。
# 确定性要求（否则证据永远"不匹配"）：文件按相对路径排序、路径统一为 `/`、
# 只 hash 内容（不掺 mtime / 绝对路径 / 文件大小）。
# --------------------------------------------------------------------------- #

def _fingerprint_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _fingerprint_files(base: Path, files: list[Path]) -> str:
    digest = hashlib.sha256()
    for p in sorted(files, key=lambda x: x.relative_to(base).as_posix()):
        digest.update(p.relative_to(base).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(p.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:16]


def _skill_text_files(base: Path, part: str) -> list[Path]:
    d = base / part
    if not d.is_dir():
        return []
    return [
        p for p in d.rglob("*")
        if p.is_file() and p.suffix != ".pyc" and "__pycache__" not in p.parts
    ]


def trigger_fingerprint(skill_dir: str | Path) -> str:
    """触发轴指纹 = hash(description)。只随 description 变化。"""
    frontmatter, _body, _errors = load_skill(skill_dir)
    description = str((frontmatter or {}).get("description", ""))
    return _fingerprint_text(description)


def effectiveness_fingerprint(skill_dir: str | Path) -> str:
    """有效性轴指纹 = hash(SKILL.md + references/ + scripts/ + assets/ + evals/effectiveness.json)。"""
    base = Path(skill_dir)
    files: list[Path] = []
    skill_md = base / "SKILL.md"
    if skill_md.is_file():
        files.append(skill_md)
    for part in EFFECTIVENESS_PARTS:
        files.extend(_skill_text_files(base, part))
    eval_file = base.joinpath(*EFFECTIVENESS_EVAL)
    if eval_file.is_file():
        files.append(eval_file)
    return _fingerprint_files(base, files)


def skill_fingerprints(skill_dir: str | Path) -> dict[str, str]:
    """一次算出两轴指纹。"""
    return {
        "trigger": trigger_fingerprint(skill_dir),
        "effectiveness": effectiveness_fingerprint(skill_dir),
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def merge_evidence(
    iteration_dir: str | Path,
    skill_dir: str | Path,
    axes: tuple[str, ...] = ("trigger", "effectiveness"),
    model: str | None = None,
    skill_name: str | None = None,
) -> Path:
    """把指定轴的指纹 + 模型 ID + 时间写进 ``<iteration>/evidence.json``（合并已存在的轴）。

    过期证据不删：只更新本轮跑过的轴，其余轴原样保留，供复审按指纹挑最近一次匹配项。
    """
    path = Path(iteration_dir) / "evidence.json"
    existing: dict[str, Any] = {}
    if path.is_file():
        try:
            loaded = json.loads(read_text(path))
            if isinstance(loaded, dict):
                existing = loaded
        except (json.JSONDecodeError, OSError):
            existing = {}

    if skill_name is None:
        frontmatter, _b, _e = load_skill(skill_dir)
        skill_name = str((frontmatter or {}).get("name") or Path(skill_dir).name)

    fingerprints = skill_fingerprints(skill_dir)
    now = _now_iso()
    record: dict[str, Any] = {
        "skill": skill_name,
        "generated_at": now,
        "model": model,
        "axes": dict(existing.get("axes") or {}),
    }
    for axis in axes:
        if axis not in fingerprints:
            continue
        record["axes"][axis] = {
            "fingerprint": fingerprints[axis],
            "model": model,
            "updated_at": now,
        }
    write_text(path, json.dumps(record, indent=2, ensure_ascii=False))
    return path
