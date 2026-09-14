#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
knowledge-distill 技能工具脚本
------------------------------
提供本技能需要的确定性操作：
  - discover-vaults : 读取 obsidian.json 自动发现本机 Obsidian vault
  - load-config     : 读取持久化配置文件（格式 / vault / 笔记根目录）
  - save-config     : 写入持久化配置文件
  - list-structure  : 列出 AI 笔记根目录下的一层分类及每类下的笔记
  - list-index      : 读取分类下的目录文件（索引文件）
  - list-questions  : 列出索引「已收录疑问」条目（写入前查重、判断是否合并）
  - check-name      : 写入前检查同名笔记，避免误覆盖
  - search-notes    : 在笔记正文中按关键词/正则检索，返回命中片段
  - lint-notes      : 只读健康检查，报告链接结构问题 + 内容质量问题
  - write-note      : 事务化写入笔记（写入前备份、临时文件原子替换）
  - list-backups    : 列出笔记的备份版本（不带参数则列全部）
  - restore-note    : 把笔记恢复到某个备份版本（恢复前先备份当前版本）
  - gen-moc         : 按主题生成/刷新 MOC 内容地图（根目录 MOC-<主题>.md）
  - append-index-entry    : 向分类索引的"笔记导航"表格追加/更新一行
  - append-index-question : 向分类索引的"已收录疑问"追加/更新一条（链接可并列多个）

用法示例:
  python skill_tools.py discover-vaults
  python skill_tools.py load-config
  python skill_tools.py save-config --config '{"format":"obsidian","vault":"D:\\vault","note_root":"AI笔记"}'
  python skill_tools.py list-structure "D:\\vault\\AI笔记"
  python skill_tools.py list-index "D:\\vault\\AI笔记\\示例分类"
  python skill_tools.py list-questions "D:\\vault\\AI笔记\\示例分类"
  python skill_tools.py check-name "D:\\vault\\AI笔记\\示例分类" "示例笔记标题"
  python skill_tools.py search-notes "D:\\vault\\AI笔记" "关键词"
  python skill_tools.py lint-notes "D:\\vault\\AI笔记"
  python skill_tools.py write-note "D:\\vault\\AI笔记\\示例分类\\标题.md" --content-file draft.md
  python skill_tools.py list-backups "D:\\vault\\AI笔记\\示例分类\\标题.md"
  python skill_tools.py restore-note "D:\\vault\\AI笔记\\示例分类\\标题.md" --version 20260101-120000
  python skill_tools.py gen-moc "D:\\vault\\AI笔记" "分布式系统" --tag 分布式
  python skill_tools.py append-index-entry "D:\\vault\\AI笔记\\示例分类" "标题" "摘要"
  python skill_tools.py append-index-question "D:\\vault\\AI笔记\\示例分类" "示例疑问？" "标题"
"""

import argparse
import datetime
import hashlib
import json
import os
import posixpath
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

# 配置文件存放于用户主目录，跨会话持久；不随技能更新被覆盖
CONFIG_PATH = Path.home() / ".knowledge-distill-config.json"

# 笔记备份目录：放在用户主目录下（笔记库之外），既不污染笔记库、
# 也不会被 list-structure / lint-notes / search-notes 扫到。
BACKUP_DIR = Path.home() / ".knowledge-distill-backups"

# MOC（内容地图）文件前缀：MOC 统一放在笔记根目录下、以该前缀命名，
# 与分类子目录区分开（list-structure / lint-notes / search-notes 只处理
# 分类子目录，因此根目录下的 MOC 文件天然不会被误当作笔记）。
MOC_PREFIX = "MOC-"

DEFAULT_INDEX_FILE = "00-分类索引.md"

# 笔记文件扩展名（唯一权威）：技能只认这两种为知识笔记。
# 其它文件（含 .txt）一律视为附件，不参与笔记的列举、检索、索引与健康检查。
NOTE_SUFFIXES = (".md", ".markdown")

# 每个笔记文件在备份目录中保留的历史版本数，超出则淘汰最旧的（避免无限增长）。
_BACKUP_KEEP = 10

# 「已收录疑问」条目里并列多个笔记链接时的分隔符；
# 链接数超过阈值时给出提醒（一条疑问铺得太开，往往说明该疑问过于宽泛，宜拆分）。
_QUESTION_LINK_SEP = "、"
_QUESTION_LINK_WARN_THRESHOLD = 3

# 笔记间「疑似重复 / 可合并」候选检测（确定性、零依赖）。
# 只用结构化信号 + 已有的双链图谱，不引入向量 / 语义检索（与设计边界一致）。
# 权重把不同信号折算到同一分值；达到阈值才作为候选上报，仅报告、不改文件。
_SIMILAR_TAG_WEIGHT = 3.0        # tags Jaccard 重叠
_SIMILAR_TITLE_WEIGHT = 2.0      # 标题 / 别名 词元 Jaccard
_SIMILAR_LINK_WEIGHT = 2.0       # 图谱邻接：共享出链，或同列于一条「已收录疑问」
_SIMILAR_CATEGORY_WEIGHT = 0.5   # 同分类（弱信号）
_SIMILAR_THRESHOLD = 2.0         # 达到该分才作为候选
_SIMILAR_MAX_PAIRS = 50          # 最多返回的候选对数
_SIMILAR_PER_NOTE = 5            # 每篇笔记最多参与几个候选对（保留高分）

# 分类索引模板：脚本新建索引时按模板渲染，保证与 SKILL.md 走模板路径的产出结构一致
# （含 frontmatter、"笔记导航"、"已收录疑问" 三个部分，避免两条路径产出不一致）
INDEX_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "assets" / "分类索引模板.md"
_INDEX_FALLBACK_TEMPLATE = (
    "# 分类索引 —— {{分类名}}\n\n"
    "> 本文件为「智识沉淀」自动维护的分类目录文件，记录本分类下的笔记。\n"
    "> 以「笔记」为单位导航，相似问题会合并进同一篇笔记，不重复收录。\n\n"
    "## 笔记导航\n\n"
    "| 笔记 | 主题摘要 | 链接 |\n| ---- | -------- | ---- |\n\n"
    "## 已收录疑问\n"
)

# Windows 下不能出现在文件名中的字符。技能主要运行在 Windows，按更严格规则校验，
# 避免标题含 "/" 时被 Path 解析成子目录、或含 ":" 等导致写入失败。
INVALID_FILENAME_CHARS = '<>:"/\\|?*'
_FILENAME_CHAR_MAP = {
    "<": "＜", ">": "＞", ":": "：", '"': "”",
    "/": "／", "\\": "＼", "|": "｜", "?": "？", "*": "＊",
}
# Windows 保留设备名（含扩展名同样非法，如 CON.md）
_WINDOWS_RESERVED_NAMES = (
    {"con", "prn", "aux", "nul"}
    | {f"com{i}" for i in range(1, 10)}
    | {f"lpt{i}" for i in range(1, 10)}
)


def flatten_text(text):
    """把多行文本压成单行，避免破坏 Markdown 表格或列表结构。"""
    return re.sub(r"\s*\n\s*", " ", str(text)).strip()


def escape_table_cell(text):
    """把文本压成单行并转义竖线，避免破坏 Markdown 表格结构。"""
    return flatten_text(text).replace("|", "\\|")


# 标准 Markdown 链接 href 中需要转义的字符（中文保留原样，保证可读性）。
# 与 _normalize_link_target 的还原逻辑对称，写入与解析能对得上。
_MD_HREF_ESCAPE = {
    " ": "%20", "(": "%28", ")": "%29", "[": "%5B", "]": "%5D",
    "<": "%3C", ">": "%3E", "#": "%23", "?": "%3F", "&": "%26", "|": "%7C",
}


def _md_href(title):
    """把笔记标题转成标准 Markdown 链接的 href（相对同目录笔记，带 .md）。"""
    href = flatten_text(title)
    for ch, encoded in _MD_HREF_ESCAPE.items():
        href = href.replace(ch, encoded)
    return f"{href}.md"


def _resolve_format(fmt=None):
    """确定链接渲染格式：显式传入优先，否则读持久化配置，缺省 obsidian。"""
    if fmt:
        return str(fmt).strip().lower()
    cfg = load_config()
    return str(cfg.get("format") or "obsidian").strip().lower()


def render_note_link(title, fmt=None, table_safe=True):
    """按笔记格式渲染索引里的笔记链接。

    - Obsidian：双链 `[[标题]]`（原生支持，可点击、可进图谱）。
    - 普通 Markdown：标准链接 `[标题](标题.md)`（VSCode/Typora/GitHub 可点击，
      双链语法在普通 Markdown 阅读器里只是纯文本）。

    table_safe=True 时按表格单元格转义竖线（用于索引表格）；
    列表场景（如 MOC）传 False——双链里的 `|` 是别名分隔符，转义反而破坏链接。
    """
    display = escape_table_cell(title) if table_safe else flatten_text(title)
    if _resolve_format(fmt) in ("markdown", "md"):
        return f"[{display}]({_md_href(title)})"
    return f"[[{display}]]"


def sanitize_title(title):
    """把标题中的不安全字符替换为全角字符，返回可直接用作文件名的建议标题。"""
    cleaned = "".join(_FILENAME_CHAR_MAP.get(ch, ch) for ch in str(title))
    cleaned = re.sub(r"[\x00-\x1f]", "", cleaned).strip().rstrip(". ")
    if not cleaned:
        return "未命名笔记"
    if cleaned.casefold() in _WINDOWS_RESERVED_NAMES:
        cleaned = f"{cleaned}_笔记"
    return cleaned


def validate_title(title):
    """校验标题能否安全用作文件名。

    返回 (是否合法, 非法字符列表, 建议标题, 问题描述列表)。
    """
    raw = str(title or "")
    problems = []

    invalid_chars = sorted({ch for ch in raw if ch in INVALID_FILENAME_CHARS})
    if invalid_chars:
        problems.append("含非法字符 " + " ".join(invalid_chars))

    if any(ord(ch) < 32 for ch in raw):
        problems.append("含控制字符")
        invalid_chars.append("控制字符")
    invalid_chars = sorted(set(invalid_chars))

    if raw.strip() != raw:
        problems.append("首尾有空白")
    if raw.endswith((".", " ")):
        problems.append("以点或空格结尾")

    if raw.strip() and raw.casefold() in _WINDOWS_RESERVED_NAMES:
        problems.append("是 Windows 保留设备名")

    if not raw.strip():
        problems.append("标题为空")

    return (not problems), invalid_chars, sanitize_title(raw), problems


# ---------------------------------------------------------------- 配置读写
def load_config():
    """读取配置文件；不存在或损坏时返回空配置。"""
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(cfg):
    """写入配置文件（原子写，避免中断损坏）。

    临时文件保留原文件名并以进程号区分，避免 with_suffix 吃掉 .json 后缀，
    也避免多个会话同时保存时互相覆盖临时文件。
    """
    tmp = CONFIG_PATH.with_name(f"{CONFIG_PATH.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(CONFIG_PATH)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
    return cfg


# ---------------------------------------------------------------- vault 发现
# obsidian.json 在各平台的默认位置
OBSIDIAN_JSON_CANDIDATES = [
    # Windows
    Path(os.environ.get("APPDATA", "")) / "obsidian" / "obsidian.json",
    # macOS
    Path.home() / "Library" / "Application Support" / "obsidian" / "obsidian.json",
    # Linux
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    / "obsidian" / "obsidian.json",
]


def discover_vaults():
    """返回本机 Obsidian vault 路径列表（去重、仅保留存在的目录）。"""
    vaults = []
    seen = set()
    for candidate in OBSIDIAN_JSON_CANDIDATES:
        if not candidate.exists():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            continue
        vault_list = data.get("vaults", {})
        if not isinstance(vault_list, dict):
            vault_list = {}
        for info in vault_list.values():
            if not isinstance(info, dict):
                continue
            path = info.get("path")
            if not path:
                continue
            norm = os.path.normpath(path)
            if norm in seen:
                continue
            seen.add(norm)
            if os.path.isdir(norm):
                vaults.append(norm)
    return vaults


# ---------------------------------------------------------------- 目录结构
def list_structure(note_root):
    """列出 AI 笔记根目录下一层分类（子目录）及每类下的笔记文件。

    分类索引文件（00-分类索引.md）是技能自维护的导航文件，不是知识笔记，
    因此不计入 notes，改用 has_index 单独标记，避免调用方把它误判为可合并的笔记。
    """
    root = Path(note_root)
    if not root.is_dir():
        return {"exists": False, "note_root": str(root), "categories": []}

    categories = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue  # 只把一层子目录视为分类
        notes = []
        has_index = False
        for p in sorted(entry.iterdir()):
            if not p.is_file():
                continue
            if p.name.casefold() == DEFAULT_INDEX_FILE.casefold():
                has_index = True
                continue
            if p.suffix.lower() in NOTE_SUFFIXES:
                notes.append(p.name)
        categories.append({"name": entry.name, "notes": notes, "has_index": has_index})
    return {"exists": True, "note_root": str(root), "categories": categories}


def list_index(category_dir):
    """读取分类目录下的索引文件（00-分类索引.md）。"""
    index_file = Path(category_dir) / DEFAULT_INDEX_FILE
    if not index_file.exists():
        return {"exists": False, "index_file": str(index_file), "content": ""}
    return {"exists": True, "index_file": str(index_file),
            "content": index_file.read_text(encoding="utf-8-sig")}


def list_questions(category_dir):
    """列出分类索引「已收录疑问」章节的全部条目（结构化，供写入前查重）。

    写入新疑问前先调用本命令，比对是否已存在**语义等价**的疑问：
    - 等价 -> 复用已有条目的原疑问文本再调用 append-index-question，脚本会命中
      该条并合并链接，避免"同义不同文"变成多条冗余；
    - 不等价 -> 作为新疑问写入。

    返回每条疑问的原文与已并列的笔记链接（`links` 为空表示仍是未迁移的旧格式）。
    """
    cat = Path(category_dir)
    if not cat.is_dir():
        return {"ok": False, "error": f"分类目录不存在: {cat}"}
    index_file = cat / DEFAULT_INDEX_FILE
    if not index_file.exists():
        return {"ok": True, "exists": False, "index_file": str(index_file),
                "count": 0, "questions": []}
    items = _parse_index_questions(index_file.read_text(encoding="utf-8-sig"))
    return {"ok": True, "exists": True, "index_file": str(index_file),
            "count": len(items), "questions": items}


def check_name(category_dir, title):
    """写入前检查目标笔记是否已存在同名文件，避免误覆盖。

    同时校验标题能否安全用作文件名：标题含 `/` 时 `cat / f"{title}.md"` 会被解析成
    子目录、返回失真路径，含 `:` `*` `?` 等在 Windows 上则直接写入失败，因此必须先拦截。

    返回：
    - valid=False：标题非法，附带 illegal_chars 与 suggestion（建议标题），调用方应先改名。
    - exists=True：同名文件已存在，调用方必须向用户确认"覆盖 / 改名 / 合并"，不得直接写入。
    """
    cat = Path(category_dir)
    if not cat.is_dir():
        return {"ok": False, "error": f"分类目录不存在: {cat}"}

    valid, illegal_chars, suggested, problems = validate_title(title)
    if not valid:
        return {"ok": False, "valid": False, "exists": False,
                "title": str(title), "illegal_chars": illegal_chars,
                "suggested_title": suggested,
                "error": "标题不能直接用作文件名：" + "；".join(problems),
                "suggestion": f"建议改用标题「{suggested}」后重试"}

    target = cat / f"{title}.md"
    if not target.exists():
        return {"ok": True, "valid": True, "exists": False, "path": str(target)}

    # 同名文件已存在：尝试找出可能的同名笔记（Obsidian 双链会因同名而歧义）
    same_name = [p.name for p in cat.iterdir()
                 if p.is_file() and p.stem == title and p.suffix.lower() in NOTE_SUFFIXES]
    return {"ok": True, "valid": True, "exists": True, "path": str(target),
            "same_name_files": sorted(same_name),
            "suggestion": "向用户确认：覆盖 / 改名 / 合并进该笔记"}


def search_notes(note_root, query, category=None, use_regex=False, max_snippets=3, context=60, full=False):
    """在笔记正文中按关键词/正则检索，返回命中片段。

    用于 Step 2 判断"新建 vs 合并"、Step 5 检测新旧笔记冲突时真正看到已有笔记内容（而非只看标题），
    也支撑"我之前记过什么关于 X 的笔记"这类查找场景。

    - query：关键词（默认）或正则表达式（use_regex=True）
    - category：仅在该分类下检索；省略则检索所有分类
    - max_snippets：每篇笔记最多返回的命中片段数
    - context：每个片段前后保留的字符数
    - full：为 True 时额外返回命中笔记的**完整正文**（用于读取旧笔记后带引用作答）
    """
    root = Path(note_root)
    if not root.is_dir():
        return {"ok": False, "error": f"笔记根目录不存在: {root}"}

    try:
        pattern = re.compile(query if use_regex else re.escape(query), re.IGNORECASE)
    except re.error as e:
        return {"ok": False, "error": f"正则表达式无效: {e}"}

    if category:
        cat_dirs = [root / category]
        if not cat_dirs[0].is_dir():
            return {"ok": False, "error": f"分类不存在: {cat_dirs[0]}"}
    else:
        cat_dirs = sorted([d for d in root.iterdir() if d.is_dir()])

    hits = []
    for cat_dir in cat_dirs:
        for note in sorted(cat_dir.iterdir()):
            if not note.is_file() or note.suffix.lower() not in NOTE_SUFFIXES:
                continue
            if note.name.casefold() == DEFAULT_INDEX_FILE.casefold():
                continue  # 索引文件不是知识笔记，不参与检索
            try:
                text = note.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue

            matched = pattern.search(text)
            if not matched:
                continue

            fm_text, _ = _split_frontmatter(text)
            title_hit = bool(pattern.search(note.stem))
            date = _frontmatter_date(fm_text)

            if full:
                # 全文模式：命中即返回整篇正文，供带引用作答；不做片段截取
                hits.append({
                    "category": cat_dir.name,
                    "note": note.name,
                    "path": str(note),
                    "title_hit": title_hit,
                    "date": date,
                    "count": len(pattern.findall(text)),
                    "content": text,
                    "snippets": [],
                })
                continue

            snippets = []
            covered_until = -1
            for m in pattern.finditer(text):
                if len(snippets) >= max_snippets:
                    break
                start = max(0, m.start() - context)
                # 跳过与上一个片段区间重叠的命中，避免返回重复内容
                if start < covered_until:
                    continue
                end = min(len(text), m.end() + context)
                snippet = text[start:end].replace("\n", " ").strip()
                snippets.append({"match": m.group(0), "snippet": snippet})
                covered_until = end
            if snippets:
                hits.append({
                    "category": cat_dir.name,
                    "note": note.name,
                    "path": str(note),
                    "title_hit": title_hit,
                    "date": date,
                    "count": len(pattern.findall(text)),
                    "snippets": snippets,
                })

    # 确定性排序（不上向量）：标题命中优先 → 命中次数多 → 日期新（updated/created）→ 文件名
    hits.sort(key=lambda h: h["note"].casefold())
    hits.sort(key=lambda h: (h["title_hit"], h["count"], h["date"]), reverse=True)

    return {"ok": True, "query": query, "use_regex": use_regex, "full": full,
            "matched_notes": len(hits), "hits": hits}


def _strip_aigc_frontmatter_block(text):
    """剥离 frontmatter 中的 `AIGC:` 块（含其下的缩进子键）。

    平台合规标识由客户端在文件写入后按国标注入（每次内容唯一），
    技能不应自行生成或复制它。模板文件可能被 hook 注入过，这里做一次
    防御性剔除：只删 AIGC 块，保留 frontmatter 的其它字段与结构。
    """
    lines = text.splitlines()
    out = []
    skipping = False
    for line in lines:
        if re.match(r"^AIGC:\s*$", line):
            skipping = True
            continue
        if skipping:
            # 缩进行属于 AIGC 块；遇到非缩进行则结束跳过
            if re.match(r"^\s+\S", line) or not line.strip():
                continue
            skipping = False
        out.append(line)
    cleaned = "\n".join(out)
    # frontmatter 若被掏空（只剩 --- 两行），一并去掉，避免留下空块
    cleaned = re.sub(r"\A---\s*\n---\s*\n", "", cleaned)
    return cleaned


def _strip_aigc_watermark_line(text):
    """去掉模板里的显式标识行（如末尾的 `> AI生成`）。

    与 `_strip_aigc_frontmatter_block` 同理：显式标识应由平台在写入后注入，
    技能不自带，避免换用其它客户端时索引文件残留固定的合规标记。
    """
    lines = [ln for ln in text.splitlines()
             if not re.match(r"^\s*>\s*AI\s*生成\s*$", ln)]
    cleaned = "\n".join(lines)
    # 去掉剥离后可能残留在末尾的多余空行，保持单结尾换行
    return cleaned.rstrip("\n") + "\n" if cleaned.strip() else cleaned


def _render_index_template(category_name):
    """渲染分类索引模板：优先读 assets 模板，读取失败时用内置兜底模板。

    与 SKILL.md 中"复制模板为索引"的路径保持一致，含 frontmatter 与
    "笔记导航""已收录疑问"两个章节，避免脚本新建的索引结构缺章节。
    渲染前会剥离模板里的 AIGC 块与显式标识行——平台合规标识由客户端写入时
    注入，技能不自带，保证换用其它客户端时不携带过期/重复的固定标识。
    """
    template = ""
    try:
        template = INDEX_TEMPLATE_PATH.read_text(encoding="utf-8-sig")
    except OSError:
        template = _INDEX_FALLBACK_TEMPLATE
    content = _strip_aigc_frontmatter_block(template)
    content = _strip_aigc_watermark_line(content)
    content = content.replace("{{分类名}}", category_name)
    # 删除模板中的示例占位行（含其后的空行），真实疑问由后续流程补写
    content = re.sub(r"^- （此处分点记录[^\n]*\n\n?", "", content, flags=re.MULTILINE)
    return content if content.endswith("\n") else content + "\n"


def append_index_entry(category_dir, title, summary, fmt=None):
    """向分类索引的"笔记导航"表格追加一行（格式由脚本保证，避免 LLM 手写漂移）。

    - 标题/摘要中的竖线与换行会被转义，避免破坏 Markdown 表格结构。
    - 已存在同名条目则更新摘要，不重复追加。
    - 表格不存在时自动补表头。
    - 索引文件不存在时按模板新建（结构与 SKILL.md 的模板路径一致）。
    - `fmt` 指定链接写法：obsidian（双链）/ markdown（标准链接）；缺省读配置。
    """
    cat = Path(category_dir)
    if not cat.is_dir():
        return {"ok": False, "error": f"分类目录不存在: {cat}"}

    title_cell = escape_table_cell(title)
    summary_cell = escape_table_cell(summary)
    row = f"| {title_cell} | {summary_cell} | {render_note_link(title, fmt)} |"

    index_file = cat / DEFAULT_INDEX_FILE
    created = not index_file.exists()
    if created:
        index_file.write_text(_render_index_template(cat.name), encoding="utf-8")

    text = index_file.read_text(encoding="utf-8-sig")
    lines = text.splitlines()

    # 已存在同名条目 -> 更新摘要
    prefix = f"| {title_cell} |"
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            if line.strip() == row:
                return {"ok": True, "action": "unchanged", "index_file": str(index_file), "row": row}
            lines[i] = row
            index_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return {"ok": True, "action": "updated", "index_file": str(index_file), "row": row}

    # 不存在 -> 追加到表格末尾（找到表头分隔行后的最后一行表格）
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("| 笔记") or (line.startswith("|") and "主题摘要" in line):
            header_idx = i
            break
    if header_idx is None:
        lines.extend(["", "## 笔记导航", "", "| 笔记 | 主题摘要 | 链接 |", "| ---- | -------- | ---- |"])
        header_idx = len(lines) - 3

    insert_at = header_idx + 2  # 表头 + 分隔行之后
    while insert_at < len(lines) and lines[insert_at].startswith("|"):
        insert_at += 1
    lines.insert(insert_at, row)
    index_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "action": "created" if created else "appended",
            "index_file": str(index_file), "row": row}


def _link_key(title):
    """链接比较用的归一化键：忽略渲染转义差异（如 `\\|` 与 `|`）。"""
    return str(title or "").replace("\\", "").strip()


def _render_question_entry(question, link_fragments, fmt=None):
    """渲染一条疑问条目：`- 疑问 → 链接片段[、链接片段...]`（链接可并列多个）。"""
    links = _QUESTION_LINK_SEP.join(
        str(f).strip() for f in link_fragments if str(f).strip())
    return f"- {flatten_text(question)} → {links}"


def append_index_question(category_dir, question, note_title, fmt=None):
    """向分类索引的"已收录疑问"章节追加/更新一条疑问，并附指向笔记的链接。

    - 每条格式固定为 `- 疑问 → <链接>[、<链接>...]`，保证可点击跳转。
    - 同一疑问再次写入时**合并链接**：保留已有链接、追加新链接、去重、保持顺序，
      既不覆盖已有指向（避免丢信息），也不重复成多条。因此一条疑问可并列指向
      多篇笔记——笔记按主题各自成篇时，疑问把相关笔记都列出来，读者按需跳转。
    - 链接写法随格式变化：Obsidian 用双链，普通 Markdown 用标准链接。
    - 旧格式条目（`→` 后是纯文本回答、没有链接）会被规范为链接格式：本技能按
      "索引只负责导航"设计，回答正文保留在笔记里，索引不再重复承载。
    - "已收录疑问"章节不存在时自动补建；索引文件不存在时按模板新建。
    """
    cat = Path(category_dir)
    if not cat.is_dir():
        return {"ok": False, "error": f"分类目录不存在: {cat}"}

    question_text = flatten_text(question)
    note_link_title = flatten_text(note_title)
    if not question_text:
        return {"ok": False, "error": "疑问内容不能为空"}
    if not note_link_title:
        return {"ok": False, "error": "笔记标题不能为空"}

    index_file = cat / DEFAULT_INDEX_FILE
    if not index_file.exists():
        index_file.write_text(_render_index_template(cat.name), encoding="utf-8")

    text = index_file.read_text(encoding="utf-8-sig")
    lines = text.splitlines()

    # 已存在同一疑问 -> 合并链接：保留已有片段原样、按需追加新链接，不覆盖、不重复
    for i, line in enumerate(lines):
        if not line.startswith("- "):
            continue
        # 箭头两侧空格可有可无（兼容 `？→ 回答` 这类历史写法）
        m = re.match(r"^(.*?)\s*→\s*(.*)$", line[2:].strip(), re.DOTALL)
        if not m:
            continue
        existing_q, tail = m.group(1), m.group(2)
        if existing_q.strip() != question_text:
            continue

        existing_links = _extract_links(tail)
        # 旧格式（→ 后是纯文本回答、无任何链接）不保留回答文本，规范为仅链接
        if existing_links:
            parts = [p.strip() for p in tail.split(_QUESTION_LINK_SEP) if p.strip()]
        else:
            parts = []
        merged_links = list(existing_links)
        if not any(_link_key(t) == _link_key(note_link_title) for t in existing_links):
            parts.append(render_note_link(note_link_title, fmt))
            merged_links.append(note_link_title)

        entry = _render_question_entry(question_text, parts)
        result = {"ok": True, "action": "unchanged", "index_file": str(index_file),
                  "entry": entry, "links": merged_links,
                  "normalized": bool(tail.strip()) and not existing_links}
        if line.strip() != entry:
            lines[i] = entry
            index_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            result["action"] = "updated"
        if len(merged_links) > _QUESTION_LINK_WARN_THRESHOLD:
            result["warning"] = (
                f"该疑问已指向 {len(merged_links)} 篇笔记，可能过于宽泛；"
                "建议确认是否应拆分为更聚焦的疑问，或合并主题重复的笔记。"
            )
        return result

    entry = _render_question_entry(
        question_text, [render_note_link(note_link_title, fmt)])

    # 定位"已收录疑问"章节（容忍标题内的多余空格，如 `##  已收录疑问  `）
    section_idx = None
    section_re = re.compile(r"^\s*##\s+已收录疑问\s*$")
    for i, line in enumerate(lines):
        if section_re.match(line):
            section_idx = i
            break

    if section_idx is None:
        # 章节不存在 -> 追加到文件末尾
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(["## 已收录疑问", "", entry])
        index_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"ok": True, "action": "section_created",
                "index_file": str(index_file), "entry": entry}

    # 确定章节范围：下一个章节标题（容忍多余空格）或文件末尾
    section_end = len(lines)
    for i in range(section_idx + 1, len(lines)):
        if re.match(r"^\s*##\s+", lines[i]):
            section_end = i
            break

    # 章节内定位插入点：优先追加到最后一条疑问之后
    last_item = None
    for i in range(section_idx + 1, section_end):
        if lines[i].startswith("- "):
            last_item = i

    if last_item is not None:
        insert_at = last_item + 1
    else:
        # 章节内还没有疑问条目：跳过标题后的前导空行
        insert_at = section_idx + 1
        while insert_at < section_end and not lines[insert_at].strip():
            insert_at += 1

    lines.insert(insert_at, entry)
    # 保证条目与后续内容（下一条疑问/引用块/下一章节）之间有空行分隔
    if insert_at + 1 < len(lines) and lines[insert_at + 1].strip():
        lines.insert(insert_at + 1, "")

    index_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "action": "appended",
            "index_file": str(index_file), "entry": entry}


# ---------------------------------------------------------------- 健康检查
# 双链语法：[[目标]]、[[目标|别名]]、[[目标#锚点]]、[[分类/目标]]，以及嵌入 ![[目标]]
_LINK_RE = re.compile(r"!?\[\[([^\[\]]+)\]\]")
# 标准 Markdown 链接：`[显示文字](目标.md)`，以及图片 `![alt](x.png)`
_MD_LINK_RE = re.compile(r"(!?)\[([^\[\]]*)\]\(([^()]*)\)")
# 图片等非笔记附件，不参与断链判断
_ATTACHMENT_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico",
    ".pdf", ".mp3", ".mp4", ".wav", ".zip", ".xlsx", ".docx", ".pptx", ".csv",
    ".txt",
)
# 外链协议，不参与断链判断
_EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "ftp://", "tel:", "file://")
# 围栏代码块：其中的 [[...]] 是语法示例，不是真实双链，检查前先剔除
_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
# 行内代码：`[[笔记名]]` 这类语法示例同样要剔除，避免误报断链
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def _normalize_link_target(raw):
    """把 `[[A|别名]]` / `[[A#锚点]]` 规范成纯目标名（按 Obsidian 语义先切别名再切锚点）。"""
    target = str(raw or "").strip()
    if "|" in target:
        target = target.split("|", 1)[0]
    if "#" in target:
        target = target.split("#", 1)[0]
    return target.strip()


def _normalize_md_href(href):
    """把标准 Markdown 链接的 href 规范成笔记名（解码、去锚点、去路径与扩展名）。

    返回空字符串表示该链接不指向笔记（外链、图片附件、纯锚点等），
    调用方应跳过，避免把图片或网址误判成断链。
    """
    raw = str(href or "").strip()
    if not raw:
        return ""
    if raw.lower().startswith(_EXTERNAL_SCHEMES):
        return ""
    if raw.startswith("#"):
        return ""
    # 锚点与查询串不属于笔记名
    for sep in ("#", "?"):
        if sep in raw:
            raw = raw.split(sep, 1)[0]
    raw = urllib.parse.unquote(raw).strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()
    if raw.lower().endswith(_ATTACHMENT_SUFFIXES):
        return ""
    if raw.lower().endswith(NOTE_SUFFIXES):
        raw = raw.rsplit(".", 1)[0]
    # 规范化相对路径：去掉 `./` `../` 前缀并压平冗余分隔符，
    # 使 `../分类/笔记` 与 `分类/笔记` 一致，便于与库内相对路径比对
    raw = posixpath.normpath(raw.replace("\\", "/"))
    while raw.startswith(("./", "../")):
        raw = raw[3:] if raw.startswith("../") else raw[2:]
    if raw in (".", "/", ""):
        return ""
    return raw.strip()


def _link_basename(target):
    """取目标名的最后一段：`分类/笔记名` -> `笔记名`。"""
    return str(target or "").replace("\\", "/").split("/")[-1].strip()


def _strip_code_blocks(text):
    """去掉围栏代码块与行内代码，避免把代码里的 [[...]] 误判为双链。"""
    return _INLINE_CODE_RE.sub("", _FENCED_CODE_RE.sub("", text))


def _extract_links(text):
    """提取正文中的笔记链接目标（双链 + 标准 Markdown 链接，已规范化）。

    跳过纯锚点、外链与图片附件；两种链接语法混用也能正确识别，
    因此 Obsidian 与普通 Markdown 两种格式共用同一套健康检查。
    """
    cleaned = _strip_code_blocks(text)
    targets = []
    for m in _LINK_RE.finditer(cleaned):
        target = _normalize_link_target(m.group(1))
        if target:
            targets.append(target)
    for m in _MD_LINK_RE.finditer(cleaned):
        if m.group(1) == "!":
            continue  # 图片嵌入，不是笔记链接
        target = _normalize_md_href(m.group(3))
        if target:
            targets.append(target)
    return targets


def _parse_index_entries(index_text):
    """从索引「笔记导航」表格提取已收录的笔记名（按出现顺序，不去重）。

    兼容三种写法：`[[双链]]`、`[显示文字](笔记.md)`、以及未加链接的纯文本第一列，
    这样 Obsidian 与普通 Markdown 两种索引都能被正确解析。
    """
    entries = []
    for line in index_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or not cells[0]:
            continue
        if cells[0] == "笔记" or set(cells[0]) <= set("-: "):
            continue  # 表头 / 分隔行
        target = None
        for cell in cells:
            m = _LINK_RE.search(cell)
            if m:
                candidate = _normalize_link_target(m.group(1))
                if candidate:
                    target = candidate
                    break
            m = _MD_LINK_RE.search(cell)
            if m and m.group(1) != "!":
                candidate = _normalize_md_href(m.group(3))
                if candidate:
                    target = candidate
                    break
        if target is None:
            target = cells[0]
        if target:
            entries.append(target)
    return entries


def _parse_index_questions(index_text):
    """从索引「已收录疑问」章节提取疑问条目（按出现顺序）。

    返回 `[{"question": 疑问文本, "links": [链接目标...]}]`：
    - `links` 为该条疑问并列的笔记链接，可多个；
    - 旧格式条目（`→` 后是纯文本回答、不含链接）`links` 为空列表，便于调用方
      识别并迁移。

    只认 `## 已收录疑问` 到下一个二级标题之间的 `- ` 列表项；模板占位行
    （以"（"开头）不计入。
    """
    lines = index_text.splitlines()
    section_re = re.compile(r"^\s*##\s+已收录疑问\s*$")
    start = None
    for i, line in enumerate(lines):
        if section_re.match(line):
            start = i
            break
    if start is None:
        return []

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if re.match(r"^\s*##\s+", lines[i]):
            end = i
            break

    items = []
    for line in lines[start + 1:end]:
        s = line.strip()
        if not s.startswith("- "):
            continue
        body = s[2:].strip()
        if not body or body.startswith("（"):
            continue  # 空项 / 模板占位行
        # 箭头两侧空格可有可无（兼容 `？→ 回答` 这类历史写法）
        m = re.match(r"^(.*?)\s*→\s*(.*)$", body, re.DOTALL)
        if m:
            question, tail = m.group(1).strip(), m.group(2).strip()
        else:
            question, tail = body, ""
        if not question:
            continue
        items.append({"question": question, "links": _extract_links(tail)})
    return items


def _split_frontmatter(text):
    """拆出 YAML frontmatter，返回 (frontmatter 文本, 正文)。

    无 frontmatter 时返回 ("", 原文)。
    """
    m = re.match(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n?", text, re.DOTALL)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def _frontmatter_keys(fm_text):
    """取 frontmatter 的顶层键名集合（只判断键是否存在，不解析值）。"""
    keys = set()
    for line in fm_text.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*)[ \t]*:", line)
        if m:
            keys.add(m.group(1).lower())
    return keys


def _find_empty_sections(body):
    """找出"有标题、标题下却没有任何正文"的章节，返回标题列表。

    以标题行为界分段：段内除空行外无内容即为空章节。只检查 ## 及以下
    （H1 通常是文档标题本身）。

    两条边界处理，都是为了不误报：
    - **代码块内**的 `#` 行不算标题（代码注释不是章节）；但判断章节是否为空时
      仍以原始行为准——整章只有一段代码块属于有内容，不能因为"剥离代码块"被判空。
    - 段落延伸到下一个**同级或更高级**标题为止：父章节下紧跟的子标题算父章节的
      内容，只有整段（含其下所有子章节）都空时才报父章节；空的子章节单独报出。
    """
    lines = body.splitlines()
    in_code = False
    fenced = []  # 每行是否处于代码块内（含围栏行本身）
    for line in lines:
        if re.match(r"^\s*(```|~~~)", line):
            fenced.append(True)
            in_code = not in_code
            continue
        fenced.append(in_code)

    heads = []  # (行号, 级别, 标题)
    for i, line in enumerate(lines):
        if fenced[i]:
            continue
        m = re.match(r"^(#{2,6})\s+(.*\S)\s*$", line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2).strip()))
    empties = []
    for idx, (i, level, title) in enumerate(heads):
        end = len(lines)
        for j in range(idx + 1, len(heads)):
            if heads[j][1] <= level:  # 下一个同级或更高级标题 → 本段结束
                end = heads[j][0]
                break
        if not any(ln.strip() for ln in lines[i + 1:end]):
            empties.append(title)
    return empties


def _note_key(path):
    """返回笔记绝对路径的短哈希，用于备份名区分跨分类同名笔记。"""
    norm = os.path.normcase(os.path.abspath(str(path)))
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:6]


# 备份时间戳形如 20260101-120000，同一秒内多次备份追加 -1、-2 …
_BACKUP_STAMP_RE = re.compile(r"^\d{8}-\d{6}(-\d+)?$")


def _parse_backup_name(filename, note_name):
    """解析某笔记的备份文件名，返回 (key, stamp)；不匹配该笔记则返回 None。

    新命名 `{文件名}.{hash6}.{时间戳}.bak`，旧命名 `{文件名}.{时间戳}.bak`（key=None）。
    """
    if not filename.endswith(".bak") or not filename.startswith(note_name + "."):
        return None
    rest = filename[:-4][len(note_name) + 1:]
    parts = rest.split(".")
    if len(parts) == 1:
        key, stamp = None, parts[0]
    elif len(parts) == 2:
        key, stamp = parts[0], parts[1]
    else:
        return None
    return (key, stamp) if _BACKUP_STAMP_RE.match(stamp) else None


def _prune_backups(note_name, key=None, keep=_BACKUP_KEEP):
    """每个笔记（按 文件名 + 路径短哈希）只保留最近 keep 份备份，避免无限增长。"""
    if keep <= 0:
        return
    prefix = f"{note_name}.{key}." if key else f"{note_name}."
    candidates = [p for p in BACKUP_DIR.iterdir()
                  if p.is_file() and p.name.startswith(prefix) and p.name.endswith(".bak")]
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for old in candidates[keep:]:
        try:
            old.unlink()
        except OSError:
            pass


def _backup_file(target):
    """把原文件备份到备份目录（用户主目录下），返回备份路径。

    备份名含基于完整路径的短哈希，避免跨分类同名笔记的备份互相混淆。
    """
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    key = _note_key(target)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    base = f"{target.name}.{key}.{stamp}"
    dest = BACKUP_DIR / f"{base}.bak"
    n = 1
    while dest.exists():
        dest = BACKUP_DIR / f"{base}-{n}.bak"
        n += 1
    shutil.copy2(target, dest)
    _prune_backups(target.name, key)
    return dest


def list_backups(note_path=None):
    """列出备份版本。给了 note_path 只列该笔记的；否则列全部。

    每条含 `file`、`stamp`（时间戳，取不到为 null）、`size`、`mtime`；
    给了 note_path 时另含 `attributable`（是否能精确对应到该路径的笔记）。
    """
    if not BACKUP_DIR.is_dir():
        return {"ok": True, "backup_dir": str(BACKUP_DIR), "count": 0, "backups": []}
    name = Path(note_path).name if note_path else None
    key = _note_key(note_path) if note_path else None
    items = []
    for p in BACKUP_DIR.iterdir():
        if not p.is_file() or not p.name.endswith(".bak"):
            continue
        stamp, attributable = None, None
        if name:
            parsed = _parse_backup_name(p.name, name)
            if not parsed:
                continue
            bkey, stamp = parsed
            if bkey is not None and bkey != key:
                continue  # 同名但属于别的分类
            attributable = (bkey == key)
        else:
            m = _BACKUP_STAMP_RE.search(p.name[:-4].rsplit(".", 1)[-1])
            stamp = m.group(0) if m else None
        try:
            stat = p.stat()
        except OSError:
            continue
        item = {"file": p.name, "stamp": stamp,
                "size": stat.st_size, "mtime": int(stat.st_mtime)}
        if name:
            item["attributable"] = attributable
        items.append(item)
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return {"ok": True, "backup_dir": str(BACKUP_DIR), "count": len(items), "backups": items}


def restore_note(note_path, version=None):
    """把笔记恢复到某个历史备份版本（缺省=最近一版）。

    恢复前先对**当前版本**再备份一次，保证回退本身也能反悔。
    返回 action / path / from（所用备份）/ backup（当前版本的新备份）。
    """
    target = Path(note_path)
    if target.suffix.lower() not in NOTE_SUFFIXES:
        return {"ok": False, "error": f"只接受 Markdown 笔记文件: {target}"}
    name, key = target.name, _note_key(target)

    candidates = []
    if BACKUP_DIR.is_dir():
        for p in BACKUP_DIR.iterdir():
            if not p.is_file():
                continue
            parsed = _parse_backup_name(p.name, name)
            if not parsed:
                continue
            bkey, stamp = parsed
            if bkey is not None and bkey != key:
                continue  # 同名但不同分类
            candidates.append((p, stamp))
    if not candidates:
        return {"ok": False, "error": f"没有找到该笔记的备份: {target}"}

    if version:
        matches = [c for c in candidates if c[1] == version]
        if not matches:
            return {"ok": False,
                    "error": f"未找到版本 {version}；用 list-backups 查看可用版本"}
        chosen = matches[0][0]
    else:
        chosen = max(candidates, key=lambda c: c[0].stat().st_mtime)[0]

    try:
        content = chosen.read_text(encoding="utf-8-sig")
    except OSError as e:
        return {"ok": False, "error": f"读取备份失败: {e}"}

    backup_path = None
    if target.exists():
        try:
            backup_path = _backup_file(target)  # 先备份当前版本，回退可反悔
        except OSError as e:
            return {"ok": False, "error": f"备份当前版本失败（已中止恢复）: {e}"}

    result = write_note(str(target), content, backup=False)
    if not result.get("ok"):
        return result
    return {"ok": True, "action": "restored", "path": str(target),
            "from": str(chosen),
            "backup": str(backup_path) if backup_path else None,
            "bytes": result.get("bytes")}


def write_note(note_path, content, backup=True):
    """把笔记内容安全写入目标文件（事务化写入）。

    相比直接写文件，多做三件事以防误覆盖与写入中断损坏笔记：
    1. 目标已存在时，先把原文件备份到 `~/.knowledge-distill-backups/`；
    2. 先写同目录临时文件，再用 os.replace 原子替换（同分区内为原子操作）；
    3. 内容与原文完全一致时跳过写入，返回 action=unchanged（幂等、不产生备份）。

    重写整篇的场景（含"合并进已有笔记"：先读原文、在内存拼好完整内容再整体写回）
    都应走本命令，而不是直接覆盖。返回：action、path、backup、bytes。
    """
    target = Path(note_path)
    if target.suffix.lower() not in NOTE_SUFFIXES:
        return {"ok": False, "error": f"只接受 Markdown 笔记文件: {target}"}
    if not target.parent.is_dir():
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return {"ok": False, "error": f"创建上级目录失败: {e}"}

    new_text = content if content.endswith("\n") else content + "\n"
    existed = target.exists()
    if existed:
        try:
            old_text = target.read_text(encoding="utf-8-sig", errors="replace")
        except OSError as e:
            return {"ok": False, "error": f"读取原文件失败: {e}"}
        if old_text == new_text:
            return {"ok": True, "action": "unchanged", "path": str(target),
                    "backup": None, "bytes": len(new_text.encode("utf-8"))}

    backup_path = None
    if existed and backup:
        try:
            backup_path = _backup_file(target)
        except OSError as e:
            return {"ok": False, "error": f"备份原文件失败（已中止写入）: {e}"}

    tmp = target.with_name(target.name + ".tmp-distill")
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_text)
        os.replace(tmp, target)
    except OSError as e:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        return {"ok": False, "error": f"写入失败: {e}"}

    return {"ok": True,
            "action": "overwritten" if existed else "created",
            "path": str(target),
            "backup": str(backup_path) if backup_path else None,
            "bytes": len(new_text.encode("utf-8"))}


def find_similar_notes(note_root, threshold=_SIMILAR_THRESHOLD,
                       max_pairs=_SIMILAR_MAX_PAIRS, per_note=_SIMILAR_PER_NOTE):
    """确定性检测「疑似重复 / 可合并」的笔记候选对（只报告，不改文件）。

    信号（全部确定性、零依赖，不做向量 / 语义检索）：
    - tags 重叠（Jaccard）；
    - 标题 + aliases 的词元重叠（中文二元组近似）；
    - 图谱邻接：共享出链目标，或同列于一条索引「已收录疑问」下；
    - 同分类（弱信号）。

    候选对按加权分排序，阈值以上才上报，并给出命中依据（reasons）供人工判断。
    只提示候选，是否合并由用户决定。
    """
    root = Path(note_root)
    if not root.is_dir():
        return {"ok": False, "error": f"笔记根目录不存在: {root}"}

    notes = []
    tag_index, term_index, link_index, question_index = {}, {}, {}, {}
    by_cat_stem = {}

    def _add(index, key, nid):
        if key:
            index.setdefault(key, set()).add(nid)

    cat_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    for cat_dir in cat_dirs:
        for p in sorted(cat_dir.iterdir()):
            if not p.is_file() or p.suffix.lower() not in NOTE_SUFFIXES:
                continue
            if p.name.casefold() == DEFAULT_INDEX_FILE.casefold():
                continue
            try:
                text = p.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            fm_text, _body = _split_frontmatter(text)
            tags = {t.strip().casefold() for t in _frontmatter_tags(fm_text) if t.strip()}
            aliases = _frontmatter_aliases(fm_text)
            title_terms = _terms(p.stem) | _terms(" ".join(aliases))
            outlinks = {_link_basename(t).casefold() for t in _extract_links(text) if _link_basename(t)}
            nid = len(notes)
            notes.append({"id": nid, "name": p.name, "stem": p.stem,
                          "category": cat_dir.name, "path": str(p),
                          "tags": tags, "title_terms": title_terms, "outlinks": outlinks})
            by_cat_stem[(cat_dir.name, p.stem.casefold())] = nid
            for t in tags:
                _add(tag_index, t, nid)
            for t in title_terms:
                _add(term_index, t, nid)
            for t in outlinks:
                _add(link_index, t, nid)

        # 同列于一条疑问：从该分类索引的「已收录疑问」读取
        index_file = cat_dir / DEFAULT_INDEX_FILE
        if not index_file.exists():
            continue
        try:
            idx_text = index_file.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        for item in _parse_index_questions(idx_text):
            q = (item.get("question") or "").strip().casefold()
            if not q:
                continue
            ids = [by_cat_stem.get((cat_dir.name, _link_basename(t).casefold()))
                   for t in item.get("links", [])]
            for nid in [x for x in ids if x is not None]:
                _add(question_index, q, nid)

    # 候选对：只比较共享某个索引键的笔记，避免 O(n²) 全量两两比
    pair_ids = set()
    for index in (tag_index, term_index, link_index, question_index):
        for members in index.values():
            m = sorted(members)
            for i in range(len(m)):
                for j in range(i + 1, len(m)):
                    pair_ids.add((m[i], m[j]))

    pairs = []
    for a, b in pair_ids:
        na, nb = notes[a], notes[b]
        score = 0.0
        reasons = []
        tag_j = _jaccard(na["tags"], nb["tags"])
        if tag_j:
            score += _SIMILAR_TAG_WEIGHT * tag_j
            reasons.append("标签重叠：" + "、".join(sorted(na["tags"] & nb["tags"])))
        title_j = _jaccard(na["title_terms"], nb["title_terms"])
        if title_j:
            score += _SIMILAR_TITLE_WEIGHT * title_j
            reasons.append("标题 / 别名相似")
        link_j = _jaccard(na["outlinks"], nb["outlinks"])
        if link_j:
            score += _SIMILAR_LINK_WEIGHT * link_j
            reasons.append("共同链接到：" + "、".join(sorted(na["outlinks"] & nb["outlinks"])))
        shared_q = {q for q, ids in question_index.items() if a in ids and b in ids}
        if shared_q:
            score += _SIMILAR_LINK_WEIGHT
            reasons.append("同列于疑问：" + "、".join(sorted(shared_q)))
        if na["category"] == nb["category"]:
            score += _SIMILAR_CATEGORY_WEIGHT
        if score >= threshold:
            pairs.append({
                "a": na["stem"], "b": nb["stem"],
                "category_a": na["category"], "category_b": nb["category"],
                "path_a": na["path"], "path_b": nb["path"],
                "score": round(score, 2), "reasons": reasons,
            })

    pairs.sort(key=lambda x: (-x["score"], x["path_a"], x["path_b"]))
    if per_note and per_note > 0:  # 每篇最多参与 per_note 个候选对，保留高分
        kept, count = [], {}
        for pair in pairs:
            if count.get(pair["path_a"], 0) >= per_note or count.get(pair["path_b"], 0) >= per_note:
                continue
            kept.append(pair)
            count[pair["path_a"]] = count.get(pair["path_a"], 0) + 1
            count[pair["path_b"]] = count.get(pair["path_b"], 0) + 1
        pairs = kept
    if max_pairs and max_pairs > 0:
        pairs = pairs[:max_pairs]

    return {"ok": True, "note_root": str(root), "threshold": threshold,
            "count": len(pairs), "pairs": pairs}


def lint_notes(note_root):
    """只读健康检查：既查链接结构，也查内容质量。

    全部为确定性检查（文件存在性、链接目标、索引收录、frontmatter 字段、
    空章节、索引时效），不做语义判断，因此结果准确、可复现；
    本命令不修改任何文件，修复动作交回调用方确认。

    链接结构问题（原有五类）：
    - index_orphans   ：索引收录但文件不存在（笔记被删后索引未同步）
    - broken_links    ：笔记内双链指向不存在的笔记
    - unindexed_notes ：笔记存在但所在分类索引未收录（分类无索引时全部计入）
    - orphan_notes    ：既无入链、也未被索引收录（写了但找不到）
    - question_orphans：索引「已收录疑问」里的链接指向不存在的笔记

    内容质量问题（新增三类）：
    - missing_frontmatter：Obsidian 笔记缺 frontmatter 或必填字段（tags/created/source）。
                          仅当用户已配置为 Obsidian 格式时检查——普通 Markdown 无此要求。
    - empty_sections     ：有标题、标题下却没有任何正文的章节（骨架写了没填）
    - stale_index        ：笔记比其分类索引更新（改了笔记但索引摘要未同步）
    """
    root = Path(note_root)
    if not root.is_dir():
        return {"ok": False, "error": f"笔记根目录不存在: {root}"}

    cfg = load_config()
    # frontmatter 是 Obsidian 的约定：仅在用户已配置为 Obsidian 时检查，
    # 避免对普通 Markdown 笔记库（含尚未配置的场景）产生误报。
    check_frontmatter = bool(cfg) and _resolve_format() not in ("markdown", "md")

    # 1. 收集分类与笔记（只处理一层子目录，与 list-structure 保持一致）
    categories = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        notes = [p for p in sorted(entry.iterdir())
                 if p.is_file() and p.suffix.lower() in NOTE_SUFFIXES
                 and p.name.casefold() != DEFAULT_INDEX_FILE.casefold()]
        index_file = entry / DEFAULT_INDEX_FILE
        index_text = index_file.read_text(encoding="utf-8-sig", errors="replace") if index_file.exists() else ""
        entries = _parse_index_entries(index_text)
        categories.append({
            "dir": entry,
            "notes": notes,
            "has_index": index_file.exists(),
            "index_file": index_file,
            "index_text": index_text,
            "index_entries": entries,
            "indexed_stems": {_link_basename(e).casefold() for e in entries if _link_basename(e)},
        })

    # 2. 全库笔记名索引，用于判断双链目标是否存在
    all_stems = set()
    rel_stems = set()
    for cat in categories:
        for note in cat["notes"]:
            all_stems.add(note.stem.casefold())
            rel_stems.add(f"{cat['dir'].name}/{note.stem}".casefold())

    def target_exists(target):
        base = _link_basename(target).casefold()
        if not base:
            return True  # 纯锚点，不参与存在性判断
        if base in all_stems:
            return True
        return target.replace("\\", "/").casefold() in rel_stems

    # 3. 初始化入链计数（键：分类名, 笔记名小写）
    inlink_counts = {}
    for cat in categories:
        for note in cat["notes"]:
            inlink_counts[(cat["dir"].name, note.stem.casefold())] = 0

    index_orphans, broken_links, unindexed_notes, question_orphans = [], [], [], []
    missing_frontmatter, empty_sections, stale_index = [], [], []

    # 4. 逐分类检查：索引孤儿、疑问断链、未收录笔记、断链，并累计入链
    for cat in categories:
        cat_name = cat["dir"].name

        for entry in cat["index_entries"]:
            if not _link_basename(entry):
                continue
            if not target_exists(entry):
                index_orphans.append({"category": cat_name, "target": entry,
                                      "index_file": str(cat["index_file"])})

        for item in _parse_index_questions(cat["index_text"]):
            for target in item["links"]:
                if not target_exists(target):
                    question_orphans.append({"category": cat_name,
                                             "question": item["question"],
                                             "target": target,
                                             "index_file": str(cat["index_file"])})

        for note in cat["notes"]:
            if note.stem.casefold() not in cat["indexed_stems"]:
                unindexed_notes.append({"category": cat_name, "note": note.name,
                                        "path": str(note), "has_index": cat["has_index"]})
            try:
                text = note.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue

            # 内容质量检查：frontmatter 完整度、空章节、索引时效
            fm_text, body = _split_frontmatter(text)
            if check_frontmatter:
                if not fm_text.strip():
                    missing_frontmatter.append({"category": cat_name, "note": note.name,
                                                "path": str(note), "missing": ["frontmatter"]})
                else:
                    lack = [k for k in ("tags", "created", "source")
                            if k not in _frontmatter_keys(fm_text)]
                    if lack:
                        missing_frontmatter.append({"category": cat_name, "note": note.name,
                                                    "path": str(note), "missing": lack})
            for section in _find_empty_sections(body):
                empty_sections.append({"category": cat_name, "note": note.name,
                                       "path": str(note), "section": section})
            if cat["has_index"] and note.stem.casefold() in cat["indexed_stems"]:
                try:
                    if note.stat().st_mtime > cat["index_file"].stat().st_mtime + 1.0:
                        stale_index.append({"category": cat_name, "note": note.name,
                                            "path": str(note),
                                            "index_file": str(cat["index_file"])})
                except OSError:
                    pass

            for target in _extract_links(text):
                if not target_exists(target):
                    broken_links.append({"category": cat_name, "note": note.name,
                                         "path": str(note), "target": target,
                                         "link": f"[[{target}]]"})
                    continue
                base = _link_basename(target).casefold()
                if base == note.stem.casefold():
                    continue  # 自链接不算入链
                for other in categories:
                    for other_note in other["notes"]:
                        if other_note.stem.casefold() == base:
                            inlink_counts[(other["dir"].name, base)] += 1

    # 5. 孤立笔记：无入链 且 未被索引收录
    orphan_notes = []
    for cat in categories:
        for note in cat["notes"]:
            key = (cat["dir"].name, note.stem.casefold())
            if inlink_counts.get(key, 0) == 0 and note.stem.casefold() not in cat["indexed_stems"]:
                orphan_notes.append({"category": cat["dir"].name, "note": note.name,
                                     "path": str(note)})

    structure_issues = (len(index_orphans) + len(broken_links)
                        + len(unindexed_notes) + len(orphan_notes)
                        + len(question_orphans))
    content_issues = (len(missing_frontmatter) + len(empty_sections)
                      + len(stale_index))
    # 合并候选为**参考信息**，不计入 issues（确定性信号会有误报，是否合并由用户判断）
    similar = find_similar_notes(root)
    similar_pairs = similar.get("pairs", []) if similar.get("ok") else []
    return {
        "ok": True,
        "note_root": str(root),
        "summary": {
            "categories": len(categories),
            "notes": sum(len(c["notes"]) for c in categories),
            "issues": structure_issues + content_issues,
            "structure_issues": structure_issues,
            "content_issues": content_issues,
            "similar_notes": len(similar_pairs),
        },
        "index_orphans": index_orphans,
        "question_orphans": question_orphans,
        "broken_links": broken_links,
        "unindexed_notes": unindexed_notes,
        "orphan_notes": orphan_notes,
        "missing_frontmatter": missing_frontmatter,
        "empty_sections": empty_sections,
        "stale_index": stale_index,
        "similar_notes": similar_pairs,
    }


def _frontmatter_tags(fm_text):
    """从 frontmatter 取 tags 列表，兼容 `tags: [a, b]` 行内与 `- a` 缩进两种写法。"""
    lines = fm_text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^tags[ \t]*:[ \t]*(.*)$", line, re.IGNORECASE)
        if not m:
            continue
        rest = m.group(1).strip()
        if rest.startswith("[") and rest.endswith("]"):
            return [x.strip().strip("'\"") for x in rest[1:-1].split(",") if x.strip()]
        if rest:
            return [rest.strip("'\"")]
        tags = []
        for nxt in lines[i + 1:]:
            m2 = re.match(r"^\s+-\s+(.+?)\s*$", nxt)
            if not m2:
                break
            tags.append(m2.group(1).strip().strip("'\""))
        return tags
    return []


def _frontmatter_aliases(fm_text):
    """从 frontmatter 取 aliases 列表（兼容 `aliases: [a, b]` 与 `- a` 缩进两种写法）。"""
    lines = fm_text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^aliases?[ \t]*:[ \t]*(.*)$", line, re.IGNORECASE)
        if not m:
            continue
        rest = m.group(1).strip()
        if rest.startswith("[") and rest.endswith("]"):
            return [x.strip().strip("'\"") for x in rest[1:-1].split(",") if x.strip()]
        if rest:
            return [rest.strip("'\"")]
        alts = []
        for nxt in lines[i + 1:]:
            m2 = re.match(r"^\s+-\s+(.+?)\s*$", nxt)
            if not m2:
                break
            alts.append(m2.group(1).strip().strip("'\""))
        return alts
    return []


def _frontmatter_date(fm_text):
    """取 frontmatter 的 updated（优先）或 created 日期，用于检索结果的新近度排序。

    返回 `YYYY-MM-DD` 字符串；缺失时返回空串（排序时视为最旧）。
    """
    for key in ("updated", "created"):
        m = re.search(rf"^{key}[ \t]*:[ \t]*['\"]?(\d{{4}}-\d{{2}}-\d{{2}})",
                      fm_text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1)
    return ""


_CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")
_ASCII_TERM_RE = re.compile(r"[a-z0-9]{2,}")


def _terms(text):
    """把文本切成用于相似度比较的词元集合：ASCII 小写单词 + 中文二元组。

    中文不引入分词依赖，用二元组（bigram）近似；ASCII 取长度 >= 2 的小写词。
    """
    s = str(text or "").casefold()
    terms = set(_ASCII_TERM_RE.findall(s))
    for run in _CJK_RUN_RE.findall(s):
        if len(run) == 1:
            terms.add(run)
        else:
            terms.update(run[i:i + 2] for i in range(len(run) - 1))
    return terms


def _jaccard(a, b):
    """集合 Jaccard 相似度；任一为空或交集为空时返回 0。"""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if not inter:
        return 0.0
    return inter / len(a | b)


def _clip_summary(text, limit):
    """按长度截断摘要，尽量断在标点处，避免截出半句话。"""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for i in range(len(cut) - 1, max(0, len(cut) - 20), -1):
        if cut[i] in "。！？；，、）)":
            return cut[:i + 1]
    return cut + "…"


def _note_summary(body, limit=60):
    """取笔记正文的一句话作为摘要。

    优先级：**开头的概述引用**（本技能生成的笔记结构为「标题 + 引用概述」，
    这句最贴题）→ 第一个**普通段落**。以下都不适合当摘要，一律跳过：
    标题、列表项、表格行、代码块、callout 标记行、以及"创建/来源/更新"这类
    元信息行。这么设计是为避免出现"摘要 = 第一个列表项"或无关章节正文。
    """
    first_quote = ""
    first_para = ""
    in_code = False
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code or not s:
            continue
        if s[0] == ">":
            text = s.lstrip(">").strip()
            if not text or text.startswith("[!"):
                continue  # callout 标记行不是正文
            text = re.sub(r"[*_`\[\]]", "", text).strip()
            if (text and not first_quote
                    and not re.match(r"^(创建|来源|更新)\s*[:：]", text)):
                first_quote = _clip_summary(text, limit)
            continue
        if s[0] in "#|" or re.match(r"^([-*+]|\d+[.、)])\s+", s):
            continue
        text = re.sub(r"[*_`\[\]]", "", s).strip()
        if text and not first_para:
            first_para = _clip_summary(text, limit)
    return first_quote or first_para


def generate_moc(note_root, topic, tag=None, keyword=None, category=None, description=None):
    """生成/刷新一篇 MOC（内容地图）：把散在各分类、同一主题的笔记聚成一页链接清单。

    用途：分类目录回答"笔记放在哪个抽屉"，MOC 回答"关于这个主题我知道些什么"——
    同一主题的笔记可能分属不同分类，MOC 把它们跨分类聚到一页，便于一次找齐。

    - 匹配规则：给了 tag 按 frontmatter 标签精确匹配；否则用 keyword（缺省为 topic）
      在标题、frontmatter、正文中做关键词命中。
    - 输出：写到笔记根目录下的 `MOC-<主题>.md`；走 write_note 事务化写入
      （已存在则先备份、原子替换），因此可反复重新生成以刷新内容。
    - 位置说明：放在笔记根目录（与分类子目录同级），而 list-structure / lint-notes /
      search-notes 只处理分类子目录，所以 MOC 不会被误当作笔记或报未收录。
    """
    root = Path(note_root)
    if not root.is_dir():
        return {"ok": False, "error": f"笔记根目录不存在: {root}"}

    kw = (keyword or topic).strip()
    tag_key = tag.strip().lower() if tag else None
    pattern = re.compile(re.escape(kw), re.IGNORECASE) if kw else None

    cat_dirs = sorted([d for d in root.iterdir() if d.is_dir()])
    if category:
        cat_dirs = [d for d in cat_dirs if d.name == category]
        if not cat_dirs:
            return {"ok": False, "error": f"分类不存在: {category}"}

    groups = []
    total = 0
    for cat_dir in cat_dirs:
        items = []
        for note in sorted(cat_dir.iterdir()):
            if not note.is_file() or note.suffix.lower() not in NOTE_SUFFIXES:
                continue
            if note.name.casefold() == DEFAULT_INDEX_FILE.casefold():
                continue
            try:
                text = note.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            fm_text, body = _split_frontmatter(text)
            if tag_key:
                hit = tag_key in [x.lower() for x in _frontmatter_tags(fm_text)]
            elif pattern:
                hit = bool(pattern.search(note.stem) or pattern.search(fm_text)
                           or pattern.search(body))
            else:
                hit = False
            if hit:
                items.append({"title": note.stem, "summary": _note_summary(body)})
        if items:
            groups.append({"category": cat_dir.name, "items": items})
            total += len(items)

    today = datetime.date.today().isoformat()
    desc = (description or "").strip() or f"自动聚合「{topic}」相关的笔记（跨分类），便于一次找齐。"
    lines = [
        "---",
        f"tags: [MOC, {topic}]",
        f"created: {today}",
        "source: 智识沉淀生成",
        "---",
        "",
        f"# 知识地图 —— {topic}",
        "",
        f"> {desc}",
        ">",
        "> 本页由「智识沉淀」按需生成，可重新生成以刷新；请勿手工编辑（下次生成会覆盖）。",
        "",
    ]
    for g in groups:
        lines.append(f"## {g['category']}")
        lines.append("")
        for it in g["items"]:
            entry = f"- {render_note_link(it['title'], table_safe=False)}"
            if it["summary"]:
                entry += f" — {it['summary']}"
            lines.append(entry)
        lines.append("")
    if total == 0:
        lines.extend(["> **暂无匹配笔记**：可更换标签或关键词后重新生成。", ""])
    lines.append(f"共 {total} 篇笔记。")
    lines.append("")
    content = "\n".join(lines)

    moc_name = MOC_PREFIX + sanitize_title(topic)
    write_result = write_note(str(root / f"{moc_name}.md"), content)
    if not write_result.get("ok"):
        return write_result
    return {
        "ok": True,
        "path": write_result["path"],
        "action": write_result["action"],
        "backup": write_result.get("backup"),
        "matched_notes": total,
        "groups": [{"category": g["category"], "count": len(g["items"])} for g in groups],
    }


# ---------------------------------------------------------------- 命令行入口
def main(argv=None):
    # 强制以 UTF-8 输出，避免 Windows 控制台默认编码（如 cp936）把中文 JSON 写乱。
    # 由脚本自处理，调用方无需再手动设置 PYTHONUTF8。
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="knowledge-distill 技能工具")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("discover-vaults", help="发现本机 Obsidian vault")

    sub.add_parser("load-config", help="读取配置文件")

    p_save = sub.add_parser("save-config", help="写入配置文件")
    p_save.add_argument("--config", help='内联 JSON 配置，如 {"format":"obsidian"}')
    p_save.add_argument("--config-file", help="从 JSON 文件读取配置（更可靠，推荐）")

    p_list = sub.add_parser("list-structure", help="列出笔记根目录结构")
    p_list.add_argument("note_root")

    p_index = sub.add_parser("list-index", help="读取分类索引文件")
    p_index.add_argument("category_dir")

    p_questions = sub.add_parser("list-questions",
                                 help="列出分类索引「已收录疑问」条目（写入前语义查重用）")
    p_questions.add_argument("category_dir")

    p_check = sub.add_parser("check-name", help="写入前检查同名笔记，避免误覆盖")
    p_check.add_argument("category_dir")
    p_check.add_argument("title")

    p_search = sub.add_parser("search-notes", help="在笔记正文中检索关键词/正则")
    p_search.add_argument("note_root")
    p_search.add_argument("query")
    p_search.add_argument("--category", help="仅在该分类下检索")
    p_search.add_argument("--regex", action="store_true", help="把 query 当作正则表达式")
    p_search.add_argument("--max-snippets", type=int, default=3, help="每篇笔记最多返回的片段数")
    p_search.add_argument("--context", type=int, default=60, help="片段前后保留的字符数")
    p_search.add_argument("--full", action="store_true",
                          help="同时返回命中笔记的完整正文（读取旧笔记后带引用作答）")

    p_lint = sub.add_parser("lint-notes",
                            help="只读健康检查：链接结构（索引孤儿/断链/未收录/孤立/疑问断链）"
                                 "+ 内容质量（缺 frontmatter/空章节/索引过期）")
    p_lint.add_argument("note_root")

    p_write = sub.add_parser("write-note",
                             help="事务化写入笔记：先备份、临时文件原子替换、内容相同则跳过")
    p_write.add_argument("note_path", help="目标笔记的绝对路径（.md / .markdown）")
    p_write.add_argument("--content-file", help="从文件读取笔记完整内容（推荐，避免长文本转义问题）")
    p_write.add_argument("--content", help="直接传入笔记完整内容（短内容可用）")

    p_lb = sub.add_parser("list-backups", help="列出笔记的备份版本（不带参数则列全部）")
    p_lb.add_argument("note_path", nargs="?", help="目标笔记路径；省略则列出全部备份")

    p_rn = sub.add_parser("restore-note", help="把笔记恢复到某个备份版本（缺省=最近一版）")
    p_rn.add_argument("note_path", help="目标笔记的绝对路径（.md / .markdown）")
    p_rn.add_argument("--version", help="要恢复的时间戳版本（用 list-backups 查看；缺省=最近一版）")

    p_moc = sub.add_parser("gen-moc", help="按主题生成/刷新 MOC 内容地图（根目录 MOC-<主题>.md）")
    p_moc.add_argument("note_root", help="笔记根目录（MOC 写在其下）")
    p_moc.add_argument("topic", help="MOC 主题（用于文件名与标题）")
    p_moc.add_argument("--tag", help="按 frontmatter 标签精确匹配笔记（优先于关键词）")
    p_moc.add_argument("--keyword", help="按关键词匹配标题/frontmatter/正文，缺省用主题")
    p_moc.add_argument("--category", help="仅聚合该分类下的笔记")
    p_moc.add_argument("--description", help="自定义 MOC 说明文字")

    p_append = sub.add_parser("append-index-entry", help="向分类索引追加/更新一行笔记导航")
    p_append.add_argument("category_dir")
    p_append.add_argument("title")
    p_append.add_argument("summary")
    p_append.add_argument("--format", choices=["obsidian", "markdown"],
                          help="链接写法，缺省读配置（obsidian=双链，markdown=标准链接）")

    p_question = sub.add_parser("append-index-question", help="向分类索引追加/更新一条已收录疑问")
    p_question.add_argument("category_dir")
    p_question.add_argument("question")
    p_question.add_argument("note_title")
    p_question.add_argument("--format", choices=["obsidian", "markdown"],
                            help="链接写法，缺省读配置（obsidian=双链，markdown=标准链接）")

    args = parser.parse_args(argv)

    if args.command == "discover-vaults":
        print(json.dumps({"vaults": discover_vaults()}, ensure_ascii=False, indent=2))
    elif args.command == "load-config":
        print(json.dumps(load_config(), ensure_ascii=False, indent=2))
    elif args.command == "save-config":
        if not args.config and not args.config_file:
            print(json.dumps({"ok": False, "error": "需提供 --config 或 --config-file"}, ensure_ascii=False))
            return 1
        if args.config_file:
            try:
                cfg = json.loads(Path(args.config_file).read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError) as e:
                print(json.dumps({"ok": False, "error": f"读取配置文件失败: {e}"}, ensure_ascii=False))
                return 1
        else:
            try:
                cfg = json.loads(args.config)
            except json.JSONDecodeError:
                print(json.dumps({"ok": False, "error": "config 不是合法 JSON（建议改用 --config-file 传文件路径）"}, ensure_ascii=False))
                return 1
        cfg = save_config(cfg)
        print(json.dumps({"ok": True, "config": cfg, "path": str(CONFIG_PATH)}, ensure_ascii=False, indent=2))
    elif args.command == "list-structure":
        print(json.dumps(list_structure(args.note_root), ensure_ascii=False, indent=2))
    elif args.command == "list-index":
        print(json.dumps(list_index(args.category_dir), ensure_ascii=False, indent=2))
    elif args.command == "list-questions":
        result = list_questions(args.category_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result.get("ok"):
            return 1
    elif args.command == "check-name":
        result = check_name(args.category_dir, args.title)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result.get("ok"):
            return 1
    elif args.command == "search-notes":
        result = search_notes(args.note_root, args.query, category=args.category,
                              use_regex=args.regex, max_snippets=args.max_snippets,
                              context=args.context, full=args.full)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result.get("ok"):
            return 1
    elif args.command == "write-note":
        if args.content_file and args.content is not None:
            print(json.dumps({"ok": False, "error": "--content-file 与 --content 只能给一个"}, ensure_ascii=False))
            return 1
        if args.content_file:
            try:
                content = Path(args.content_file).read_text(encoding="utf-8-sig")
            except OSError as e:
                print(json.dumps({"ok": False, "error": f"读取内容文件失败: {e}"}, ensure_ascii=False))
                return 1
        elif args.content is not None:
            content = args.content
        else:
            print(json.dumps({"ok": False, "error": "需提供 --content-file 或 --content"}, ensure_ascii=False))
            return 1
        result = write_note(args.note_path, content)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result.get("ok"):
            return 1
    elif args.command == "list-backups":
        print(json.dumps(list_backups(args.note_path), ensure_ascii=False, indent=2))
    elif args.command == "restore-note":
        result = restore_note(args.note_path, version=args.version)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result.get("ok"):
            return 1
    elif args.command == "gen-moc":
        result = generate_moc(args.note_root, args.topic, tag=args.tag,
                              keyword=args.keyword, category=args.category,
                              description=args.description)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result.get("ok"):
            return 1
    elif args.command == "lint-notes":
        result = lint_notes(args.note_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result.get("ok"):
            return 1
    elif args.command == "append-index-entry":
        result = append_index_entry(args.category_dir, args.title, args.summary,
                                    fmt=args.format)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result.get("ok"):
            return 1
    elif args.command == "append-index-question":
        result = append_index_question(args.category_dir, args.question, args.note_title,
                                       fmt=args.format)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result.get("ok"):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
