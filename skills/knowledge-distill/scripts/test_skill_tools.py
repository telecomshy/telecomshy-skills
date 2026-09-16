#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""knowledge-distill 技能工具脚本单元测试

运行方式（在技能目录下）：
    python scripts/test_skill_tools.py
    # 或：python -m unittest scripts.test_skill_tools -v

测试全部在临时目录中进行，不会触碰用户真实配置与笔记。
"""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_tools as t  # noqa: E402


class KnowledgeDistillTestCase(unittest.TestCase):
    """共用临时沙箱：隔离配置路径与笔记目录。"""

    def setUp(self):
        self.sandbox = Path(tempfile.mkdtemp(prefix="kd_test_"))
        self._orig_config = t.CONFIG_PATH
        self._orig_backup_dir = t.BACKUP_DIR
        t.CONFIG_PATH = self.sandbox / ".knowledge-distill-config.json"
        # 备份目录也重定向到沙箱，避免测试往用户主目录写备份文件
        t.BACKUP_DIR = self.sandbox / "backups"

    def tearDown(self):
        t.CONFIG_PATH = self._orig_config
        t.BACKUP_DIR = self._orig_backup_dir
        shutil.rmtree(self.sandbox, ignore_errors=True)

    # ------------------------------------------------------------ 配置读写
    def test_save_config_keeps_json_suffix(self):
        """临时文件名不能吃掉 .json 后缀。"""
        t.save_config({"format": "obsidian"})
        self.assertEqual(t.CONFIG_PATH.name, ".knowledge-distill-config.json")
        self.assertTrue(t.CONFIG_PATH.exists())

    def test_save_and_load_config_roundtrip(self):
        cfg = {"format": "obsidian", "vault": r"D:\vault", "note_root": "AI笔记"}
        t.save_config(cfg)
        self.assertEqual(t.load_config(), cfg)

    def test_save_config_leaves_no_tmp_file(self):
        t.save_config({"format": "obsidian"})
        leftovers = [p for p in self.sandbox.iterdir() if p.suffix == ".tmp"]
        self.assertEqual(leftovers, [])

    def test_save_config_is_idempotent(self):
        cfg = {"format": "markdown", "directory": r"D:\notes"}
        t.save_config(cfg)
        t.save_config(cfg)
        self.assertEqual(t.load_config(), cfg)

    def test_load_config_missing_returns_empty(self):
        self.assertEqual(t.load_config(), {})

    def test_load_config_corrupted_returns_empty(self):
        t.CONFIG_PATH.write_text("{bad json", encoding="utf-8")
        self.assertEqual(t.load_config(), {})

    # ------------------------------------------------------------ 目录结构
    def _make_category(self):
        root = self.sandbox / "AI笔记"
        cat = root / "示例分类"
        cat.mkdir(parents=True)
        (cat / "00-分类索引.md").write_text("# index", encoding="utf-8")
        (cat / "示例笔记标题.md").write_text("# note", encoding="utf-8")
        (cat / "附录.txt").write_text("txt", encoding="utf-8")
        (cat / "图片.png").write_bytes(b"\x89PNG")
        return root, cat

    def test_list_structure_excludes_index_file(self):
        root, _ = self._make_category()
        cats = {c["name"]: c for c in t.list_structure(str(root))["categories"]}
        self.assertNotIn("00-分类索引.md", cats["示例分类"]["notes"])

    def test_list_structure_keeps_real_notes(self):
        root, _ = self._make_category()
        cats = {c["name"]: c for c in t.list_structure(str(root))["categories"]}
        self.assertEqual(set(cats["示例分类"]["notes"]), {"示例笔记标题.md"})

    def test_list_structure_excludes_txt_and_non_documents(self):
        """只把 .md/.markdown 当笔记：.txt 与图片都不计入。"""
        root, _ = self._make_category()
        cats = {c["name"]: c for c in t.list_structure(str(root))["categories"]}
        self.assertNotIn("附录.txt", cats["示例分类"]["notes"])
        self.assertNotIn("图片.png", cats["示例分类"]["notes"])

    def test_list_structure_empty_category(self):
        root = self.sandbox / "AI笔记"
        (root / "空分类").mkdir(parents=True)
        cats = {c["name"]: c for c in t.list_structure(str(root))["categories"]}
        self.assertEqual(cats["空分类"]["notes"], [])

    def test_list_structure_missing_root(self):
        self.assertFalse(t.list_structure(str(self.sandbox / "不存在"))["exists"])

    # ------------------------------------------------------------ 索引读取
    def test_list_index_reads_content(self):
        root, _ = self._make_category()
        t.append_index_entry(str(root), "示例分类", "示例笔记标题", "摘要")
        result = t.list_index(str(root))
        self.assertTrue(result["exists"])
        self.assertIn("示例笔记标题", result["content"])
        self.assertIn("## 示例分类", result["content"])

    def test_list_index_missing_returns_empty(self):
        empty = self.sandbox / "空"
        empty.mkdir()
        result = t.list_index(str(empty))
        self.assertFalse(result["exists"])
        self.assertEqual(result["content"], "")

    # ------------------------------------------------------------ 同名检查
    def test_check_name_free(self):
        _, cat = self._make_category()
        result = t.check_name(str(cat), "全新笔记")
        self.assertTrue(result["ok"])
        self.assertFalse(result["exists"])

    def test_check_name_conflict(self):
        _, cat = self._make_category()
        result = t.check_name(str(cat), "示例笔记标题")
        self.assertTrue(result["ok"])
        self.assertTrue(result["exists"])
        self.assertEqual(result["same_name_files"], ["示例笔记标题.md"])
        self.assertIn("覆盖", result["suggestion"])

    def test_check_name_missing_category(self):
        result = t.check_name(str(self.sandbox / "不存在"), "任意")
        self.assertFalse(result["ok"])

    # ------------------------------------------------------------ 内容检索
    def test_search_notes_keyword(self):
        root, _ = self._make_category()
        result = t.search_notes(str(root), "note")
        self.assertTrue(result["ok"])
        self.assertEqual(result["matched_notes"], 1)
        self.assertEqual(result["hits"][0]["note"], "示例笔记标题.md")

    def test_search_notes_excludes_index(self):
        root, cat = self._make_category()
        (cat / "00-分类索引.md").write_text("独家关键词ZZZ", encoding="utf-8")
        result = t.search_notes(str(root), "独家关键词ZZZ")
        self.assertEqual(result["matched_notes"], 0)

    def test_search_notes_category_filter(self):
        root, _ = self._make_category()
        (root / "其它").mkdir()
        (root / "其它" / "无关.md").write_text("note", encoding="utf-8")
        result = t.search_notes(str(root), "note", category="示例分类")
        self.assertEqual(result["matched_notes"], 1)

    def test_search_notes_regex(self):
        root, _ = self._make_category()
        result = t.search_notes(str(root), "note|txt", use_regex=True)
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(result["matched_notes"], 1)

    def test_search_notes_invalid_regex(self):
        root, _ = self._make_category()
        result = t.search_notes(str(root), "[", use_regex=True)
        self.assertFalse(result["ok"])
        self.assertIn("error", result)

    def test_search_notes_no_match(self):
        root, _ = self._make_category()
        result = t.search_notes(str(root), "绝对不存在的词XYZ")
        self.assertEqual(result["matched_notes"], 0)
        self.assertEqual(result["hits"], [])

    def test_search_notes_snippets_deduplicated(self):
        root = self.sandbox / "AI笔记"
        cat = root / "分类"
        cat.mkdir(parents=True)
        (cat / "密集命中.md").write_text("关键词 " * 20, encoding="utf-8")
        result = t.search_notes(str(root), "关键词", max_snippets=3)
        # 命中密集时，重叠片段应被合并，不应返回 3 个几乎相同的片段
        self.assertEqual(len(result["hits"][0]["snippets"]), 1)

    def test_search_notes_missing_root(self):
        result = t.search_notes(str(self.sandbox / "不存在"), "任意")
        self.assertFalse(result["ok"])

    # ------------------------------------------------------------ 索引写入
    def test_append_index_entry_creates_file(self):
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        result = t.append_index_entry(str(root), "示例分类", "示例笔记标题", "示例摘要")
        self.assertTrue(result["ok"])
        self.assertEqual(result["action"], "created")
        content = (root / "总目录.md").read_text(encoding="utf-8")
        self.assertIn("## 示例分类", content)
        self.assertIn("| 示例笔记标题 | 示例摘要 | [[示例笔记标题]] |", content)

    def test_append_index_entry_appends_row(self):
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_entry(str(root), "分类", "笔记A", "摘要A")
        result = t.append_index_entry(str(root), "分类", "笔记B", "摘要B")
        self.assertEqual(result["action"], "appended")
        content = (root / "总目录.md").read_text(encoding="utf-8")
        self.assertIn("| 笔记A | 摘要A | [[笔记A]] |", content)
        self.assertIn("| 笔记B | 摘要B | [[笔记B]] |", content)

    def test_append_index_entry_updates_existing(self):
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_entry(str(root), "分类", "笔记A", "旧摘要")
        result = t.append_index_entry(str(root), "分类", "笔记A", "新摘要")
        self.assertEqual(result["action"], "updated")
        content = (root / "总目录.md").read_text(encoding="utf-8")
        self.assertIn("新摘要", content)
        self.assertNotIn("旧摘要", content)
        self.assertEqual(content.count("| 笔记A |"), 1)

    def test_append_index_entry_unchanged(self):
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_entry(str(root), "分类", "笔记A", "摘要")
        result = t.append_index_entry(str(root), "分类", "笔记A", "摘要")
        self.assertEqual(result["action"], "unchanged")

    def test_append_index_entry_preserves_existing_content(self):
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        toc = root / "总目录.md"
        toc.write_text("# 总目录\n\n## 分类\n\n| 笔记 | 摘要 | 链接 |\n| ---- | ---- | ---- |\n"
                       "| 笔记A | 摘要A | [[笔记A]] |\n", encoding="utf-8")
        t.append_index_entry(str(root), "分类", "笔记B", "摘要B")
        content = toc.read_text(encoding="utf-8")
        self.assertIn("| 笔记A | 摘要A | [[笔记A]] |", content)
        self.assertIn("| 笔记B | 摘要B | [[笔记B]] |", content)

    def test_append_index_entry_missing_root(self):
        result = t.append_index_entry(str(self.sandbox / "不存在"), "分类", "标题", "摘要")
        self.assertFalse(result["ok"])

    # ------------------------------------------------------------ 表格转义
    def test_escape_table_cell_pipe_and_newline(self):
        self.assertEqual(t.escape_table_cell("含|竖线"), "含\\|竖线")
        self.assertEqual(t.escape_table_cell("第一行\n第二行"), "第一行 第二行")
        self.assertEqual(t.escape_table_cell("  空白  "), "空白")

    def test_append_index_entry_escapes_pipe_in_title_and_summary(self):
        """标题/摘要含竖线时不得破坏表格结构。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        result = t.append_index_entry(str(root), "分类", "含|竖线的标题", "摘要含|竖线")
        self.assertTrue(result["ok"])
        content = (root / "总目录.md").read_text(encoding="utf-8")
        row = "| 含\\|竖线的标题 | 摘要含\\|竖线 | [[含\\|竖线的标题]] |"
        self.assertIn(row, content)
        # 该行应恰好有 4 个未转义竖线（3 个单元格的边界），未被内容中的竖线切碎
        data_line = [ln for ln in content.splitlines() if ln.startswith("| 含")][0]
        unescaped = data_line.count("|") - data_line.count("\\|")
        self.assertEqual(unescaped, 4)

    def test_append_index_entry_escapes_newline_in_summary(self):
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_entry(str(root), "分类", "标题", "第一行\n第二行")
        content = (root / "总目录.md").read_text(encoding="utf-8")
        self.assertIn("| 标题 | 第一行 第二行 | [[标题]] |", content)

    # ------------------------------------------------------------ 标题校验
    def test_check_name_rejects_slash_title(self):
        """标题含 / 会被解析成子目录，必须拦截而不是返回失真路径。"""
        _, cat = self._make_category()
        result = t.check_name(str(cat), "含/斜杠")
        self.assertFalse(result["ok"])
        self.assertFalse(result["valid"])
        self.assertIn("/", result["illegal_chars"])
        self.assertNotIn("/", result["suggested_title"])
        self.assertIn("建议", result["suggestion"])

    def test_check_name_rejects_windows_invalid_chars(self):
        _, cat = self._make_category()
        for title in ["冒号:标题", "星号*标题", "问号?标题", "引号\"标题", "竖线|标题"]:
            result = t.check_name(str(cat), title)
            self.assertFalse(result["ok"], msg=title)
            self.assertFalse(result["valid"], msg=title)

    def test_check_name_rejects_reserved_device_name(self):
        _, cat = self._make_category()
        result = t.check_name(str(cat), "CON")
        self.assertFalse(result["ok"])
        self.assertFalse(result["valid"])
        self.assertNotEqual(result["suggested_title"].casefold(), "con")

    def test_check_name_rejects_trailing_dot(self):
        _, cat = self._make_category()
        result = t.check_name(str(cat), "标题.")
        self.assertFalse(result["valid"])

    def test_check_name_accepts_normal_title(self):
        _, cat = self._make_category()
        result = t.check_name(str(cat), "正常的笔记标题")
        self.assertTrue(result["ok"])
        self.assertTrue(result["valid"])
        self.assertFalse(result["exists"])

    def test_sanitize_title_replaces_all_invalid_chars(self):
        cleaned = t.sanitize_title('a<b>c:d"e/f\\g|h?i*j')
        self.assertFalse(any(ch in cleaned for ch in t.INVALID_FILENAME_CHARS))

    # ------------------------------------------------------------ 索引结构一致
    def test_created_index_matches_template_structure(self):
        """脚本新建的根目录「总目录」应含分类章节，且不写与文件名重复的一级标题。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_entry(str(root), "分类", "笔记A", "摘要A")
        content = (root / "总目录.md").read_text(encoding="utf-8")
        self.assertNotIn("# 总目录", content)
        self.assertIn("## 分类", content)
        self.assertIn("| 笔记 | 摘要 | 链接 |", content)
        # 技能不自带合规标识：由平台写入时注入，换用其它客户端不应携带
        self.assertNotIn("AIGC:", content)
        self.assertNotIn("ContentProducer", content)

    def test_strip_aigc_frontmatter_block(self):
        """AIGC 块应被完整剥离，frontmatter 其它字段与正文保留。"""
        text = ("---\n"
                "tags:\n  - 测试\n"
                "AIGC:\n"
                "  ContentProducer: 'abc'\n"
                "  ProduceID: '11111111-2222-3333-4444-555555555555'\n"
                "  Label: '1'\n"
                "created: 2026-09-09\n"
                "---\n\n# 标题\n")
        cleaned = t._strip_aigc_frontmatter_block(text)
        self.assertNotIn("AIGC", cleaned)
        self.assertNotIn("ContentProducer", cleaned)
        self.assertNotIn("ProduceID", cleaned)
        self.assertIn("tags:", cleaned)
        self.assertIn("created: 2026-09-09", cleaned)
        self.assertIn("# 标题", cleaned)

    def test_strip_aigc_removes_empty_frontmatter(self):
        """frontmatter 只剩 AIGC 时应整体去掉，不留空 --- 块。"""
        text = ("---\n"
                "AIGC:\n"
                "  ContentProducer: 'abc'\n"
                "  Label: '1'\n"
                "---\n\n# 标题\n")
        cleaned = t._strip_aigc_frontmatter_block(text)
        self.assertFalse(cleaned.startswith("---"))
        self.assertIn("# 标题", cleaned)

    def test_strip_aigc_watermark_line(self):
        """末尾 `> AI生成` 显式标识行应被剥离，正文保留。"""
        text = "# 标题\n\n正文\n\n> AI生成\n"
        cleaned = t._strip_aigc_watermark_line(text)
        self.assertNotIn("AI生成", cleaned)
        self.assertIn("# 标题", cleaned)
        self.assertTrue(cleaned.endswith("\n"))

    def test_strip_aigc_watermark_line_keeps_normal_quote(self):
        """普通引用块不应被误删。"""
        text = "# 标题\n\n> 这是正常的引用\n\n> AI生成\n"
        cleaned = t._strip_aigc_watermark_line(text)
        self.assertIn("> 这是正常的引用", cleaned)
        self.assertNotIn("AI生成", cleaned)

    # ------------------------------------------------------------ 已收录疑问
    def test_append_index_question_creates_and_formats(self):
        """疑问条目必须统一为 `- 疑问 → [[笔记标题]]` 双链格式。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        result = t.append_index_question(str(root), "分类", "示例疑问？", "示例笔记标题")
        self.assertTrue(result["ok"])
        content = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertIn("- 示例疑问？ → [[示例笔记标题]]", content)

    def test_append_index_question_appends_to_section(self):
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_question(str(root), "分类", "疑问一", "笔记A")
        result = t.append_index_question(str(root), "分类", "疑问二", "笔记B")
        self.assertEqual(result["action"], "appended")
        content = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertIn("- 疑问一 → [[笔记A]]", content)
        self.assertIn("- 疑问二 → [[笔记B]]", content)
        # 两条疑问都应位于「分类」章节内，且顺序保持
        self.assertLess(content.index("## 分类"), content.index("- 疑问一"))
        self.assertLess(content.index("- 疑问一"), content.index("- 疑问二"))

    def test_append_index_question_merges_multiple_links(self):
        """同一疑问指向不同笔记时**合并**链接：保留旧的、追加新的，不覆盖、不重复。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_question(str(root), "分类", "同一个疑问", "笔记A")
        result = t.append_index_question(str(root), "分类", "同一个疑问", "笔记B")
        self.assertEqual(result["action"], "updated")
        self.assertEqual(result["links"], ["笔记A", "笔记B"])
        content = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertIn("- 同一个疑问 → [[笔记A]]、[[笔记B]]", content)
        self.assertEqual(content.count("- 同一个疑问"), 1)

    def test_append_index_question_unchanged(self):
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_question(str(root), "分类", "疑问", "笔记A")
        result = t.append_index_question(str(root), "分类", "疑问", "笔记A")
        self.assertEqual(result["action"], "unchanged")

    def test_append_index_question_creates_missing_section(self):
        """疑问文件不存在时自动新建，并写入分类章节。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        result = t.append_index_question(str(root), "分类", "新疑问", "笔记A")
        self.assertEqual(result["action"], "created")
        content = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertIn("## 分类", content)
        self.assertIn("- 新疑问 → [[笔记A]]", content)

    def test_append_index_question_rejects_empty(self):
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        self.assertFalse(t.append_index_question(str(root), "分类", "   ", "笔记A")["ok"])

    def test_append_index_question_missing_root(self):
        self.assertFalse(t.append_index_question(str(self.sandbox / "不存在"), "分类", "疑问", "笔记A")["ok"])

    def test_append_index_question_section_title_with_extra_spaces(self):
        """分类标题带多余空格时仍应识别为已有章节，而不是重复创建。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        (root / "收录疑问.md").write_text(
            "# 疑问\n\n##  分类  \n\n- 旧疑问 → [[旧笔记]]\n", encoding="utf-8")
        result = t.append_index_question(str(root), "分类", "新疑问", "笔记A")
        self.assertEqual(result["action"], "appended")
        content = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertEqual(content.count("##  分类  "), 1)
        self.assertIn("- 新疑问 → [[笔记A]]", content)

    def test_append_index_question_flattens_newlines(self):
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_question(str(root), "分类", "疑问\n换行", "笔记A")
        content = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertIn("- 疑问 换行 → [[笔记A]]", content)

    def test_append_index_question_does_not_break_navigation(self):
        """疑问写入后，总目录的笔记导航表格结构保持完整。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_entry(str(root), "分类", "笔记A", "摘要A")
        t.append_index_question(str(root), "分类", "疑问一", "笔记A")
        toc = (root / "总目录.md").read_text(encoding="utf-8")
        self.assertIn("| 笔记A | 摘要A | [[笔记A]] |", toc)
        q = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertIn("- 疑问一 → [[笔记A]]", q)

    def test_append_index_question_merge_is_idempotent(self):
        """重复写入同一（疑问, 笔记）组合不应产生重复链接。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_question(str(root), "分类", "疑问", "笔记A")
        t.append_index_question(str(root), "分类", "疑问", "笔记B")
        result = t.append_index_question(str(root), "分类", "疑问", "笔记A")
        self.assertEqual(result["action"], "unchanged")
        self.assertEqual(result["links"], ["笔记A", "笔记B"])
        content = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertEqual(content.count("[[笔记A]]"), 1)

    def test_append_index_question_link_order_preserved(self):
        """合并链接时保持首次写入顺序，新链接追加在末尾。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_question(str(root), "分类", "疑问", "笔记A")
        t.append_index_question(str(root), "分类", "疑问", "笔记B")
        t.append_index_question(str(root), "分类", "疑问", "笔记C")
        content = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertIn("- 疑问 → [[笔记A]]、[[笔记B]]、[[笔记C]]", content)

    def test_append_index_question_warns_when_too_many_links(self):
        """一条疑问指向超过 3 篇笔记时给出 warning，但不拦截写入。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        for title in ("笔记A", "笔记B", "笔记C"):
            t.append_index_question(str(root), "分类", "疑问", title)
        result = t.append_index_question(str(root), "分类", "疑问", "笔记D")
        self.assertTrue(result["ok"])
        self.assertIn("warning", result)
        self.assertEqual(len(result["links"]), 4)

    def test_append_index_question_normalizes_legacy_plain_answer(self):
        """旧格式（→ 后是纯文本回答）命中时规范为链接格式，回答不再重复承载。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        (root / "收录疑问.md").write_text(
            "# 疑问\n\n## 分类\n\n- 旧疑问？→ 这是一句旧回答。\n", encoding="utf-8")
        result = t.append_index_question(str(root), "分类", "旧疑问？", "笔记A")
        self.assertEqual(result["action"], "updated")
        self.assertTrue(result["normalized"])
        content = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertIn("- 旧疑问？ → [[笔记A]]", content)
        self.assertNotIn("这是一句旧回答", content)

    def test_append_index_question_matches_legacy_arrow_without_space(self):
        """历史写法的 `？→ 回答`（箭头前无空格）也能被识别为同一疑问。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        (root / "收录疑问.md").write_text(
            "# 疑问\n\n## 分类\n\n- 旧疑问？→ 旧回答\n", encoding="utf-8")
        t.append_index_question(str(root), "分类", "旧疑问？", "笔记A")
        content = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertEqual(content.count("- 旧疑问？"), 1)

    # ------------------------------------------------------------ 疑问查重
    def test_list_questions_parses_questions_and_links(self):
        """list-questions 应解析出疑问原文与已并列的笔记链接。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_question(str(root), "分类", "疑问一", "笔记A")
        t.append_index_question(str(root), "分类", "疑问一", "笔记B")
        t.append_index_question(str(root), "分类", "疑问二", "笔记C")
        result = t.list_questions(str(root))
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["questions"][0]["question"], "疑问一")
        self.assertEqual(result["questions"][0]["links"], ["笔记A", "笔记B"])
        self.assertEqual(result["questions"][1]["links"], ["笔记C"])

    def test_list_questions_flags_legacy_entry_without_links(self):
        """旧格式条目的链接识别不到时，按顿号兜底解析。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        (root / "收录疑问.md").write_text(
            "# 疑问\n\n## 分类\n\n- 旧疑问？→ 旧回答\n", encoding="utf-8")
        result = t.list_questions(str(root))
        self.assertEqual(result["questions"][0]["question"], "旧疑问？")
        self.assertEqual(result["questions"][0]["links"], ["旧回答"])

    def test_list_questions_missing_index(self):
        """根目录存在但尚无疑问文件时，返回空列表而非报错。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        result = t.list_questions(str(root))
        self.assertTrue(result["ok"])
        self.assertFalse(result["exists"])
        self.assertEqual(result["count"], 0)

    def test_list_questions_missing_root(self):
        result = t.list_questions(str(self.sandbox / "不存在"))
        self.assertTrue(result["ok"])
        self.assertFalse(result["exists"])

    def test_list_questions_ignores_template_placeholder(self):
        """占位行（以"（"开头）不应被当成真实疑问。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        (root / "收录疑问.md").write_text(
            "# 疑问\n\n## 分类\n\n- （此处分点记录关键疑问）\n", encoding="utf-8")
        result = t.list_questions(str(root))
        self.assertEqual(result["count"], 0)

    # ------------------------------------------------------------ 健康检查
    def _make_root(self):
        """建一个含单个分类的笔记根目录，返回 (root, cat)。"""
        root = self.sandbox / "AI笔记"
        cat = root / "分类A"
        cat.mkdir(parents=True)
        return root, cat

    def _write_index(self, root, rows):
        """写根目录「总目录」，含分类A下的若干笔记行；rows 为 (标题, 链接目标) 列表。"""
        lines = ["# 总目录", "", "## 分类A", "",
                 "| 笔记 | 摘要 | 链接 |", "| ---- | ---- | ---- |"]
        for title, target in rows:
            lines.append(f"| {title} | 摘要 | [[{target}]] |")
        (root / "总目录.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_lint_notes_healthy_library(self):
        """索引与笔记一致、无断链时应报告 0 问题。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n内容\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertTrue(result["ok"])
        self.assertEqual(result["summary"]["issues"], 0)
        self.assertEqual(result["index_orphans"], [])
        self.assertEqual(result["broken_links"], [])
        self.assertEqual(result["unindexed_notes"], [])
        self.assertEqual(result["orphan_notes"], [])

    def test_lint_notes_detects_index_orphan(self):
        """索引收录但文件已删除 -> index_orphans。"""
        root, cat = self._make_root()
        self._write_index(root, [("已删笔记", "已删笔记")])
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["index_orphans"]), 1)
        self.assertEqual(result["index_orphans"][0]["target"], "已删笔记")

    def test_lint_notes_detects_broken_link(self):
        """双链指向不存在的笔记 -> broken_links。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n见 [[不存在的笔记]]\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["broken_links"]), 1)
        self.assertEqual(result["broken_links"][0]["target"], "不存在的笔记")

    def test_lint_notes_detects_unindexed_note(self):
        """笔记存在但索引未收录 -> unindexed_notes。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        (cat / "笔记B.md").write_text("# 笔记B\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        names = [x["note"] for x in result["unindexed_notes"]]
        self.assertEqual(names, ["笔记B.md"])

    def test_lint_notes_detects_orphan_note(self):
        """无入链且未收录 -> orphan_notes（同时也会计入 unindexed_notes）。"""
        root, cat = self._make_root()
        (cat / "孤儿.md").write_text("# 孤儿\n", encoding="utf-8")
        self._write_index(root, [])
        result = t.lint_notes(str(root))
        self.assertEqual([x["note"] for x in result["orphan_notes"]], ["孤儿.md"])
        self.assertEqual([x["note"] for x in result["unindexed_notes"]], ["孤儿.md"])

    def test_lint_notes_detects_question_orphan(self):
        """「已收录疑问」里的链接指向不存在的笔记 -> question_orphans。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        t.append_index_question(str(root), "分类A", "疑问一", "已删笔记")
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["question_orphans"]), 1)
        self.assertEqual(result["question_orphans"][0]["target"], "已删笔记")
        self.assertEqual(result["question_orphans"][0]["question"], "疑问一")

    def test_lint_notes_question_links_ok_not_reported(self):
        """疑问链接指向存在的笔记时不应报告问题。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        t.append_index_question(str(root), "分类A", "疑问一", "笔记A")
        result = t.lint_notes(str(root))
        self.assertEqual(result["question_orphans"], [])
        self.assertEqual(result["summary"]["issues"], 0)

    def test_lint_notes_detects_broken_markdown_question_link(self):
        """普通 Markdown 疑问文件里的链接失效也应被检出。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        (root / "收录疑问.md").write_text(
            "# 疑问\n\n## 分类A\n\n- 疑问一 → [已删笔记](分类A/已删笔记.md)\n",
            encoding="utf-8")
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["question_orphans"]), 1)
        self.assertEqual(t._link_basename(result["question_orphans"][0]["target"]), "已删笔记")

    def test_lint_notes_question_orphan_counts_into_total(self):
        """question_orphans 应计入 summary.issues 总数。"""
        root, cat = self._make_root()
        self._write_index(root, [])
        t.append_index_question(str(root), "分类A", "疑问一", "已删笔记")
        result = t.lint_notes(str(root))
        expected = (len(result["index_orphans"]) + len(result["broken_links"])
                    + len(result["unindexed_notes"]) + len(result["orphan_notes"])
                    + len(result["question_orphans"]))
        self.assertEqual(result["summary"]["issues"], expected)
        self.assertGreaterEqual(result["summary"]["issues"], 1)

    def test_lint_notes_indexed_note_not_orphan(self):
        """被索引收录的笔记不算孤立，即使没有入链。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["orphan_notes"], [])

    def test_lint_notes_inlink_prevents_orphan(self):
        """有其它笔记双链指向、但未被索引收录 -> 不算孤立，但仍计入未收录。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n见 [[笔记B]]\n", encoding="utf-8")
        (cat / "笔记B.md").write_text("# 笔记B\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["orphan_notes"], [])
        self.assertEqual([x["note"] for x in result["unindexed_notes"]], ["笔记B.md"])

    def test_lint_notes_ignores_links_in_code(self):
        """行内代码与围栏代码块中的 [[...]] 是语法示例，不得误报断链。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n双链 `[[笔记名]]` 与 `[[笔记]]` 的写法：\n\n"
            "```\n[[代码里的链接]]\n```\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])

    def test_lint_notes_handles_alias_and_anchor(self):
        """[[目标|别名]] 与 [[目标#锚点]] 应按目标名判断，不算断链。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n[[笔记B|自定义文字]] 和 [[笔记B#章节]]\n", encoding="utf-8")
        (cat / "笔记B.md").write_text("# 笔记B\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A"), ("笔记B", "笔记B")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])

    def test_lint_notes_handles_category_prefixed_link(self):
        """[[分类/笔记名]] 形式应能正确解析出笔记名。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n[[分类A/笔记B]]\n", encoding="utf-8")
        (cat / "笔记B.md").write_text("# 笔记B\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A"), ("笔记B", "笔记B")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])

    def test_lint_notes_ignores_self_link(self):
        """自链接不计入入链，笔记未被索引收录时仍应算孤立。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n[[笔记A]]\n", encoding="utf-8")
        self._write_index(root, [])
        result = t.lint_notes(str(root))
        self.assertEqual([x["note"] for x in result["orphan_notes"]], ["笔记A.md"])

    def test_lint_notes_index_file_not_treated_as_note(self):
        """索引文件本身不是笔记，不得计入 unindexed_notes 或孤立笔记。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["summary"]["notes"], 1)
        self.assertEqual(result["unindexed_notes"], [])

    def test_lint_notes_missing_index_counts_all_unindexed(self):
        """根目录没有总目录时，其中所有笔记都应计入未收录。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["unindexed_notes"]), 1)

    def test_lint_notes_missing_root_fails(self):
        """笔记根目录不存在时返回 ok=False。"""
        result = t.lint_notes(str(self.sandbox / "不存在"))
        self.assertFalse(result["ok"])

    def test_lint_notes_does_not_modify_files(self):
        """健康检查是只读操作，不得改动任何文件内容。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n[[断链]]\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A"), ("幽灵", "幽灵")])
        before = {p: p.read_text(encoding="utf-8") for p in root.rglob("*") if p.is_file()}
        t.lint_notes(str(root))
        after = {p: p.read_text(encoding="utf-8") for p in root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_lint_notes_parses_index_without_link(self):
        """总目录行未写链接时，退回第一列文本判断收录，避免误报未收录。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        (root / "总目录.md").write_text(
            "# 总目录\n\n## 分类A\n\n| 笔记 | 摘要 | 链接 |\n"
            "| ---- | ---- | ---- |\n| 笔记A | 摘要 |  |\n", encoding="utf-8")
        result = t.lint_notes(str(root))
        self.assertEqual(result["unindexed_notes"], [])
        self.assertEqual(result["index_orphans"], [])

    def test_lint_notes_summary_counts(self):
        """summary 应正确统计分类数、笔记数、问题总数。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n[[断链]]\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A"), ("幽灵", "幽灵")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["summary"]["categories"], 1)
        self.assertEqual(result["summary"]["notes"], 1)
        self.assertEqual(result["summary"]["issues"], 2)  # 1 断链 + 1 索引孤儿

    # ------------------------------------------------- 普通 Markdown 格式支持
    def test_render_note_link_obsidian_and_markdown(self):
        """链接写法随格式切换：Obsidian 双链 / 普通 Markdown 标准链接。"""
        self.assertEqual(t.render_note_link("笔记A", "obsidian"), "[[笔记A]]")
        self.assertEqual(t.render_note_link("笔记A", "markdown"), "[笔记A](笔记A.md)")

    def test_render_note_link_defaults_to_config_format(self):
        """未显式指定格式时，读持久化配置。"""
        t.save_config({"format": "markdown"})
        self.assertEqual(t.render_note_link("笔记A"), "[笔记A](笔记A.md)")
        t.save_config({"format": "obsidian"})
        self.assertEqual(t.render_note_link("笔记A"), "[[笔记A]]")

    def test_render_note_link_encodes_spaces_and_parens(self):
        """标题含空格/括号时 href 需编码，保证链接可用。"""
        link = t.render_note_link("含 空格(括号)", "markdown")
        self.assertEqual(link, "[含 空格(括号)](含%20空格%28括号%29.md)")

    def test_append_index_entry_markdown_format(self):
        """普通 Markdown 下索引应生成标准链接（带分类前缀），而非双链。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        result = t.append_index_entry(str(root), "分类", "笔记A", "摘要A", fmt="markdown")
        self.assertTrue(result["ok"])
        content = (root / "总目录.md").read_text(encoding="utf-8")
        self.assertIn("| 笔记A | 摘要A | [笔记A](分类/笔记A.md) |", content)
        self.assertNotIn("[[笔记A]]", content)

    def test_append_index_question_markdown_format(self):
        """普通 Markdown 下疑问条目也应使用标准链接。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        result = t.append_index_question(str(root), "分类", "如何排查？", "笔记A", fmt="markdown")
        self.assertTrue(result["ok"])
        content = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertIn("- 如何排查？ → [笔记A](分类/笔记A.md)", content)

    def test_append_index_question_markdown_multi_links(self):
        """普通 Markdown 下多链接也用标准链接，以顿号分隔。"""
        root = self.sandbox / "AI笔记"
        root.mkdir(parents=True)
        t.append_index_question(str(root), "分类", "如何排查？", "笔记A", fmt="markdown")
        t.append_index_question(str(root), "分类", "如何排查？", "笔记B", fmt="markdown")
        content = (root / "收录疑问.md").read_text(encoding="utf-8")
        self.assertIn(
            "- 如何排查？ → [笔记A](分类/笔记A.md)、[笔记B](分类/笔记B.md)", content)

    def test_lint_notes_recognizes_markdown_links(self):
        """标准 Markdown 链接应被识别为入链，不误报断链或孤立。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        (cat / "笔记B.md").write_text(
            "# 笔记B\n\n见 [笔记A](笔记A.md)。\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A"), ("笔记B", "笔记B")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])
        self.assertEqual(result["orphan_notes"], [])
        self.assertEqual(result["unindexed_notes"], [])

    def test_lint_notes_markdown_index_parsed(self):
        """总目录里的标准 Markdown 链接应被正确解析为收录条目。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        (root / "总目录.md").write_text(
            "# 总目录\n\n## 分类A\n\n| 笔记 | 摘要 | 链接 |\n"
            "| ---- | ---- | ---- |\n| 笔记A | 摘要 | [笔记A](分类A/笔记A.md) |\n",
            encoding="utf-8")
        result = t.lint_notes(str(root))
        self.assertEqual(result["unindexed_notes"], [])
        self.assertEqual(result["index_orphans"], [])

    def test_lint_notes_detects_broken_markdown_link(self):
        """标准 Markdown 链接指向不存在的笔记时应报断链。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n见 [不存在的笔记](不存在的笔记.md)。\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["broken_links"]), 1)
        self.assertEqual(result["broken_links"][0]["target"], "不存在的笔记")

    def test_lint_notes_ignores_images_and_external_links(self):
        """图片、外链、纯锚点不应被当成笔记链接误报断链。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n![图](img.png)\n\n[官网](https://example.com)\n\n"
            "[跳转](#章节)\n\n[文件](data.xlsx)\n",
            encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])

    def test_lint_notes_ignores_markdown_link_in_code(self):
        """代码块里的标准 Markdown 链接是示例，不应报断链。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n```markdown\n[示例](不存在.md)\n```\n\n"
            "行内 `[示例](也不存在.md)` 同理。\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])

    def test_lint_notes_mixed_link_syntax(self):
        """同一笔记库混用双链与标准链接时都能识别。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        (cat / "笔记B.md").write_text(
            "# 笔记B\n\n[[笔记A]]\n\n[笔记A](笔记A.md)\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A"), ("笔记B", "笔记B")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])
        self.assertEqual(result["orphan_notes"], [])

    def test_normalize_md_href(self):
        """href 规范化：解码、去锚点、去路径与扩展名；跳过外链与附件。"""
        self.assertEqual(t._normalize_md_href("笔记A.md"), "笔记A")
        self.assertEqual(t._normalize_md_href("../分类/笔记A.md"), "分类/笔记A")
        self.assertEqual(t._normalize_md_href("含%20空格.md"), "含 空格")
        self.assertEqual(t._normalize_md_href("笔记A.md#章节"), "笔记A")
        self.assertEqual(t._normalize_md_href("https://example.com"), "")
        self.assertEqual(t._normalize_md_href("img.png"), "")
        self.assertEqual(t._normalize_md_href("#章节"), "")
        self.assertEqual(t._normalize_md_href(""), "")

    # ------------------------------------------------------------ 事务化写入
    def _write_target(self, name="笔记A.md"):
        """返回沙箱内一个可写的笔记文件路径（父目录已建好）。"""
        cat = self.sandbox / "AI笔记" / "分类A"
        cat.mkdir(parents=True, exist_ok=True)
        return cat / name

    def test_write_note_creates_new_file(self):
        """新建：action=created，无备份，内容落盘且补足末尾换行。"""
        target = self._write_target()
        result = t.write_note(str(target), "# 标题\n\n正文")
        self.assertTrue(result["ok"])
        self.assertEqual(result["action"], "created")
        self.assertIsNone(result["backup"])
        self.assertEqual(target.read_text(encoding="utf-8"), "# 标题\n\n正文\n")

    def test_write_note_overwrite_makes_backup(self):
        """覆盖：先备份原文（内容为旧版），再替换为新内容。"""
        target = self._write_target()
        target.write_text("旧内容\n", encoding="utf-8")
        result = t.write_note(str(target), "新内容")
        self.assertEqual(result["action"], "overwritten")
        self.assertTrue(result["backup"])
        self.assertEqual(Path(result["backup"]).read_text(encoding="utf-8"), "旧内容\n")
        self.assertEqual(target.read_text(encoding="utf-8"), "新内容\n")

    def test_write_note_unchanged_skips_backup_and_write(self):
        """内容一致：返回 unchanged，不写、不备份（幂等）。"""
        target = self._write_target()
        target.write_text("同样内容\n", encoding="utf-8")
        result = t.write_note(str(target), "同样内容")
        self.assertEqual(result["action"], "unchanged")
        self.assertIsNone(result["backup"])
        backups = list(t.BACKUP_DIR.glob("*")) if t.BACKUP_DIR.exists() else []
        self.assertEqual(backups, [])

    def test_write_note_leaves_no_tmp_file(self):
        """写入后不应残留 .tmp-distill 临时文件。"""
        target = self._write_target()
        t.write_note(str(target), "内容")
        self.assertEqual(list(target.parent.glob("*.tmp-distill")), [])

    def test_write_note_backup_can_be_disabled(self):
        """backup=False 时覆盖不产生备份。"""
        target = self._write_target()
        target.write_text("旧\n", encoding="utf-8")
        result = t.write_note(str(target), "新", backup=False)
        self.assertEqual(result["action"], "overwritten")
        self.assertIsNone(result["backup"])

    def test_backup_retention_keeps_newest_n(self):
        """同一笔记的备份只保留最近 _BACKUP_KEEP 份，避免无限增长。"""
        target = self._write_target()
        for i in range(t._BACKUP_KEEP + 5):
            target.write_text(f"第{i}版\n", encoding="utf-8")
            t.write_note(str(target), f"新{i}版")
        backups = [p for p in t.BACKUP_DIR.iterdir()
                   if p.name.startswith("笔记A.md.") and p.name.endswith(".bak")]
        self.assertEqual(len(backups), t._BACKUP_KEEP)

    def test_write_note_rejects_non_markdown(self):
        """只接受 Markdown 文件，避免误写其它类型。"""
        target = self._write_target("笔记.txt")
        result = t.write_note(str(target), "内容")
        self.assertFalse(result["ok"])
        self.assertFalse(target.exists())

    # ------------------------------------------------------------ 备份列表 / 回退
    def test_backup_name_includes_path_key(self):
        """备份名含路径短哈希（区分跨分类同名笔记）。"""
        target = self._write_target()
        target.write_text("旧\n", encoding="utf-8")
        result = t.write_note(str(target), "新")
        backup = Path(result["backup"]).name
        self.assertRegex(backup, r"^笔记A\.md\.[0-9a-f]{6}\.\d{8}-\d{6}(-\d+)?\.bak$")

    def test_list_backups_for_note(self):
        target = self._write_target()
        target.write_text("v1\n", encoding="utf-8")
        t.write_note(str(target), "v2")
        target.write_text("v2\n", encoding="utf-8")
        t.write_note(str(target), "v3")
        result = t.list_backups(str(target))
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 2)
        self.assertTrue(all(b["attributable"] for b in result["backups"]))
        self.assertTrue(all(b["stamp"] for b in result["backups"]))

    def test_restore_note_latest(self):
        """缺省恢复最近一版；恢复前先备份当前版本（可反悔）。"""
        target = self._write_target()
        target.write_text("旧版本\n", encoding="utf-8")
        t.write_note(str(target), "新版本")
        result = t.restore_note(str(target))
        self.assertTrue(result["ok"])
        self.assertEqual(result["action"], "restored")
        self.assertEqual(target.read_text(encoding="utf-8"), "旧版本\n")
        self.assertTrue(result["backup"])  # 当前（新版）也被备份，可再退回

    def test_restore_note_specific_version(self):
        target = self._write_target()
        target.write_text("v1\n", encoding="utf-8")
        t.write_note(str(target), "v2")          # 备份 v1
        target.write_text("v2\n", encoding="utf-8")
        t.write_note(str(target), "v3")          # 备份 v2
        backups = t.list_backups(str(target))["backups"]
        # 按内容挑出保存 v1 的那份备份（避免同秒时间戳并列）
        v1 = next(b for b in backups
                  if (t.BACKUP_DIR / b["file"]).read_text(encoding="utf-8") == "v1\n")
        result = t.restore_note(str(target), version=v1["stamp"])
        self.assertTrue(result["ok"])
        self.assertEqual(target.read_text(encoding="utf-8"), "v1\n")

    def test_restore_note_without_backup_fails(self):
        target = self._write_target()
        target.write_text("内容\n", encoding="utf-8")
        result = t.restore_note(str(target))
        self.assertFalse(result["ok"])
        self.assertIn("备份", result["error"])

    def test_restore_note_disambiguates_same_name_across_categories(self):
        """跨分类同名笔记的备份互不串用（按路径哈希区分）。"""
        a = self.sandbox / "AI笔记" / "运维" / "排查.md"
        b = self.sandbox / "AI笔记" / "开发" / "排查.md"
        a.parent.mkdir(parents=True); b.parent.mkdir(parents=True)
        a.write_text("运维旧\n", encoding="utf-8"); t.write_note(str(a), "运维新")
        b.write_text("开发旧\n", encoding="utf-8"); t.write_note(str(b), "开发新")
        self.assertTrue(t.restore_note(str(a))["ok"])
        self.assertEqual(a.read_text(encoding="utf-8"), "运维旧\n")
        self.assertEqual(b.read_text(encoding="utf-8"), "开发新\n")  # b 不受影响

    def test_write_note_creates_missing_parent_dir(self):
        """父目录不存在时自动创建。"""
        target = self.sandbox / "AI笔记" / "新分类" / "笔记.md"
        result = t.write_note(str(target), "内容")
        self.assertTrue(result["ok"])
        self.assertTrue(target.exists())

    # ------------------------------------------------------------ frontmatter 解析
    def test_frontmatter_tags_inline_and_block(self):
        """tags 兼容行内 [a, b] 与缩进 - a 两种写法。"""
        self.assertEqual(t._frontmatter_tags("tags: [a, b]"), ["a", "b"])
        self.assertEqual(t._frontmatter_tags("tags:\n  - a\n  - b\nother: 1"), ["a", "b"])
        self.assertEqual(t._frontmatter_tags("created: 2026-01-01"), [])

    # ------------------------------------------------------------ 内容质量检查
    def _obsidian_note(self, cat, name, body, fm=None):
        """写一篇带 frontmatter 的 Obsidian 笔记（fm 省略时给全三个必填字段）。"""
        fm = fm if fm is not None else "tags: [测试]\ncreated: 2026-01-01\nsource: 对话总结"
        (cat / name).write_text(f"---\n{fm}\n---\n\n{body}", encoding="utf-8")

    def test_lint_notes_missing_frontmatter_when_configured(self):
        """已配置 Obsidian 时，无 frontmatter 的笔记应被报出。"""
        t.save_config({"format": "obsidian"})
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n正文\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["missing_frontmatter"]), 1)
        self.assertEqual(result["missing_frontmatter"][0]["missing"], ["frontmatter"])

    def test_lint_notes_missing_frontmatter_fields(self):
        """frontmatter 存在但缺必填字段时，列出缺哪些。"""
        t.save_config({"format": "obsidian"})
        root, cat = self._make_root()
        self._obsidian_note(cat, "笔记A.md", "# 笔记A\n",
                            fm="tags: [测试]\ncreated: 2026-01-01")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["missing_frontmatter"][0]["missing"], ["source"])

    def test_lint_notes_frontmatter_skipped_for_plain_markdown(self):
        """普通 Markdown 无 frontmatter 要求，不应误报。"""
        t.save_config({"format": "markdown"})
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n正文\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["missing_frontmatter"], [])

    def test_lint_notes_frontmatter_skipped_without_config(self):
        """未配置（setUp 状态）时不做 frontmatter 检查，避免误报。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n正文\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["missing_frontmatter"], [])

    def test_lint_notes_detects_empty_section(self):
        """有标题无正文的章节应被报出。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n## 空章节\n\n## 有内容\n\n正文\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual([e["section"] for e in result["empty_sections"]], ["空章节"])

    def test_lint_notes_empty_section_ignores_code_block(self):
        """代码块内的 # 行不算标题，且章节里有代码就不算空。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n## 章节\n\n```\n# 不是标题\n```\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["empty_sections"], [])

    def test_lint_notes_parent_section_with_subheading_not_empty(self):
        """父章节下紧跟子标题时不算空（子标题行本身就是内容）。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n## 父章节\n\n### 子章节\n\n正文\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["empty_sections"], [])

    def test_lint_notes_empty_subsection_reported(self):
        """父章节有子标题、子标题下无正文时，只报子章节为空。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n## 父章节\n\n### 空子章节\n\n## 有内容\n\n正文\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual([e["section"] for e in result["empty_sections"]], ["空子章节"])

    def test_lint_notes_detects_stale_index(self):
        """笔记比索引新 -> stale_index。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n正文\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        old = time.time() - 100
        os.utime(root / "总目录.md", (old, old))
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["stale_index"]), 1)
        self.assertEqual(result["stale_index"][0]["note"], "笔记A.md")

    def test_lint_notes_stale_index_ignored_for_unindexed(self):
        """未被索引收录的笔记不参与索引时效检查。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n正文\n", encoding="utf-8")
        (cat / "笔记B.md").write_text("# 笔记B\n\n正文\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A")])
        old = time.time() - 100
        os.utime(root / "总目录.md", (old, old))
        result = t.lint_notes(str(root))
        self.assertEqual([s["note"] for s in result["stale_index"]], ["笔记A.md"])

    def test_lint_notes_summary_groups_and_total(self):
        """summary 给出结构/内容分组计数，且总数为两者之和。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n## 空章节\n\n## 有内容\n\n见 [[缺失笔记]]\n", encoding="utf-8")
        self._write_index(root, [("笔记A", "笔记A"), ("已删笔记", "已删笔记")])
        result = t.lint_notes(str(root))
        summary = result["summary"]
        self.assertEqual(summary["issues"],
                         summary["structure_issues"] + summary["content_issues"])
        self.assertEqual(summary["content_issues"], 1)
        self.assertEqual(summary["structure_issues"], 2)

    def test_search_notes_full_returns_content(self):
        """--full：命中笔记返回完整正文，不再截片段。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n关键词在这里，后面还有内容。\n", encoding="utf-8")
        result = t.search_notes(str(root), "关键词", full=True)
        self.assertEqual(result["matched_notes"], 1)
        self.assertIn("后面还有内容", result["hits"][0]["content"])
        self.assertEqual(result["hits"][0]["snippets"], [])
        self.assertTrue(result["full"])

    def test_search_notes_default_omits_content(self):
        """默认不返回完整正文，避免无谓的上下文占用。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n关键词在这里。\n", encoding="utf-8")
        result = t.search_notes(str(root), "关键词")
        self.assertNotIn("content", result["hits"][0])
        self.assertFalse(result["full"])

    # ------------------------------------------------------------ 链接渲染（表格/列表）
    def test_render_note_link_table_safe_toggle(self):
        """表格场景转义竖线；列表场景保留竖线（双链别名语义）。"""
        self.assertEqual(t.render_note_link("含|竖线", "obsidian"), "[[含\\|竖线]]")
        self.assertEqual(t.render_note_link("含|竖线", "obsidian", table_safe=False),
                         "[[含|竖线]]")

    # ------------------------------------------------------------ 检索排序
    def test_search_notes_ranks_title_hit_first(self):
        """标题命中的笔记排在前面，即使正文命中次数更少。"""
        root = self.sandbox / "AI笔记"
        cat = root / "分类"
        cat.mkdir(parents=True)
        (cat / "关键词笔记.md").write_text("# 标题\n\n这里有关键词一次。\n", encoding="utf-8")
        (cat / "其它.md").write_text("# 其它\n\n关键词 关键词 关键词。\n", encoding="utf-8")
        result = t.search_notes(str(root), "关键词")
        self.assertEqual(result["hits"][0]["note"], "关键词笔记.md")

    def test_search_notes_ranks_more_hits_first(self):
        """标题均未命中时，正文命中次数多的排前。"""
        root = self.sandbox / "AI笔记"
        cat = root / "分类"
        cat.mkdir(parents=True)
        (cat / "少.md").write_text("# 标题\n\n关键词一次。\n", encoding="utf-8")
        (cat / "多.md").write_text("# 标题\n\n关键词 关键词 关键词。\n", encoding="utf-8")
        result = t.search_notes(str(root), "关键词")
        self.assertEqual(result["hits"][0]["note"], "多.md")

    def test_search_notes_ranks_newer_date_first(self):
        """命中与次数相同时，updated/created 更新的排前。"""
        root = self.sandbox / "AI笔记"
        cat = root / "分类"
        cat.mkdir(parents=True)
        (cat / "旧.md").write_text("---\ncreated: 2026-01-01\n---\n\n# 旧\n\n关键词。\n", encoding="utf-8")
        (cat / "新.md").write_text("---\ncreated: 2026-09-01\n---\n\n# 新\n\n关键词。\n", encoding="utf-8")
        result = t.search_notes(str(root), "关键词")
        self.assertEqual(result["hits"][0]["note"], "新.md")

    # ------------------------------------------------------------ 笔记间相似 / 合并候选
    def test_frontmatter_aliases_inline_and_block(self):
        self.assertEqual(t._frontmatter_aliases("aliases: [别名一, 别名二]"), ["别名一", "别名二"])
        self.assertEqual(t._frontmatter_aliases("aliases:\n  - 别名一\n  - 别名二\n"),
                         ["别名一", "别名二"])
        self.assertEqual(t._frontmatter_aliases("tags:\n  - x\n"), [])

    def test_frontmatter_date_prefers_updated(self):
        self.assertEqual(t._frontmatter_date("created: 2026-01-01\nupdated: 2026-09-09\n"),
                         "2026-09-09")
        self.assertEqual(t._frontmatter_date("created: 2026-01-01\n"), "2026-01-01")
        self.assertEqual(t._frontmatter_date("tags: [x]\n"), "")

    def test_terms_ascii_and_cjk_bigram(self):
        terms = t._terms("Nginx 网关 502")
        self.assertIn("nginx", terms)
        self.assertIn("502", terms)
        self.assertIn("网关", terms)

    def test_jaccard(self):
        self.assertAlmostEqual(t._jaccard({"a", "b"}, {"b", "c"}), 1 / 3)
        self.assertEqual(t._jaccard(set(), {"a"}), 0.0)
        self.assertEqual(t._jaccard({"a"}, {"b"}), 0.0)

    def _similar_lib(self):
        root = self.sandbox / "AI笔记"
        cat = root / "运维"
        cat.mkdir(parents=True)
        return root, cat

    def test_find_similar_notes_flags_tag_and_title_overlap(self):
        root, cat = self._similar_lib()
        (cat / "Nginx 502 排查.md").write_text(
            "---\ntags:\n  - 运维\n  - nginx\n---\n\n# Nginx 502 排查\n", encoding="utf-8")
        (cat / "Nginx 网关 502 处理.md").write_text(
            "---\ntags:\n  - 运维\n  - nginx\n---\n\n# Nginx 网关 502 处理\n", encoding="utf-8")
        result = t.find_similar_notes(str(root))
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        self.assertTrue(any("标签重叠" in r for r in result["pairs"][0]["reasons"]))

    def test_find_similar_notes_ignores_unrelated(self):
        root, cat = self._similar_lib()
        (cat / "Nginx 502.md").write_text("---\ntags:\n  - nginx\n---\n\n正文\n", encoding="utf-8")
        (cat / "Python 装饰器.md").write_text("---\ntags:\n  - python\n---\n\n正文\n", encoding="utf-8")
        self.assertEqual(t.find_similar_notes(str(root))["count"], 0)

    def test_find_similar_notes_flags_shared_question(self):
        """同列在一条「已收录疑问」下的两篇笔记应被判为候选（图谱邻接信号）。"""
        root, cat = self._similar_lib()
        (cat / "排查记录.md").write_text("# 排查记录\n", encoding="utf-8")
        (cat / "网关处理.md").write_text("# 网关处理\n", encoding="utf-8")
        (root / "收录疑问.md").write_text(
            "# 疑问\n\n## 运维\n\n- 如何排查 502？ → [[排查记录]]、[[网关处理]]\n",
            encoding="utf-8")
        result = t.find_similar_notes(str(root))
        self.assertEqual(result["count"], 1)
        self.assertTrue(any("同列于疑问" in r for r in result["pairs"][0]["reasons"]))

    def test_lint_notes_includes_similar_notes(self):
        root, cat = self._similar_lib()
        (cat / "Nginx 502 排查.md").write_text(
            "---\ntags:\n  - nginx\n---\n\n# Nginx 502 排查\n", encoding="utf-8")
        (cat / "Nginx 网关 502 处理.md").write_text(
            "---\ntags:\n  - nginx\n---\n\n# Nginx 网关 502 处理\n", encoding="utf-8")
        result = t.lint_notes(str(root))
        self.assertIn("similar_notes", result)
        self.assertGreaterEqual(result["summary"]["similar_notes"], 1)

    # ------------------------------------------------------------ BOM 健壮性
    def test_bom_notes_are_parsed(self):
        """带 UTF-8 BOM 的笔记应能正确解析 frontmatter（读取统一用 utf-8-sig）。"""
        t.save_config({"format": "obsidian"})
        root, cat = self._similar_lib()
        bom = "\ufeff"
        note = bom + ("---\ntags:\n  - nginx\ncreated: 2026-01-01\nsource: 对话总结\n---\n\n# 笔记A\n")
        (cat / "笔记A.md").write_text(note, encoding="utf-8")
        result = t.lint_notes(str(root))
        self.assertEqual(result["missing_frontmatter"], [])
        self.assertEqual(t.search_notes(str(root), "笔记A")["matched_notes"], 1)


class _FakeYoudao:
    """内存版有道后端：模拟 youdaonote CLI 暴露的 MCP 工具，供单元测试使用。

    不联网、不依赖真实账号，只覆盖技能用到的工具子集；`run` 可直接替换
    `skill_tools._youdao_run`。
    """

    def __init__(self):
        self.nodes = {}  # id -> {"id","name","dir","parentId","content"}
        self._next = 1

    def _new_id(self):
        nid = str(self._next)
        self._next += 1
        return nid

    def _entries(self, parent):
        return [{"id": n["id"], "name": n["name"], "dir": n["dir"], "parentId": n["parentId"]}
                for n in self.nodes.values() if n["parentId"] == str(parent)]

    def run(self, tool, args=None, **kwargs):
        args = args or {}
        if tool == "listNotes":
            return {"entries": self._entries(args.get("parentId", "0"))}
        if tool == "createDir":
            parent, name = str(args.get("parentId", "0")), args.get("dirName")
            for n in self.nodes.values():
                if n["parentId"] == parent and n["dir"] and n["name"] == name:
                    return {"id": n["id"]}
            nid = self._new_id()
            self.nodes[nid] = {"id": nid, "name": name, "dir": True,
                               "parentId": parent, "content": ""}
            return {"id": nid}
        if tool == "createAnyNote":
            nid = self._new_id()
            self.nodes[nid] = {"id": nid, "name": args.get("title"), "dir": False,
                               "parentId": str(args.get("parentId", "0")),
                               "content": args.get("content", "")}
            return {"fileId": nid}
        if tool == "updateMarkdownNote":
            fid = str(args.get("fileId"))
            if fid not in self.nodes:
                raise t.YoudaoError("笔记不存在")
            self.nodes[fid]["content"] = args.get("content", "")
            if args.get("title"):
                self.nodes[fid]["name"] = args["title"]
            return {"ok": True}
        if tool == "getNoteTextContent":
            fid = str(args.get("fileId"))
            if fid not in self.nodes:
                raise t.YoudaoError("笔记不存在")
            return {"content": self.nodes[fid]["content"], "title": self.nodes[fid]["name"]}
        if tool == "searchNotes":
            kw = str(args.get("keyword") or "").casefold()
            hits = [n for n in self.nodes.values()
                    if not n["dir"] and kw
                    and (kw in n["name"].casefold() or kw in (n["content"] or "").casefold())]
            return {"entries": [{"id": n["id"], "name": n["name"], "dir": False,
                                 "parentId": n["parentId"]} for n in hits]}
        raise t.YoudaoError(f"未实现的工具: {tool}")


class YoudaoBackendTestCase(unittest.TestCase):
    """有道后端单元测试：用内存假后端替换 CLI，不依赖真实账号与网络。"""

    def setUp(self):
        self.sandbox = Path(tempfile.mkdtemp(prefix="kd_youdao_test_"))
        self._orig_config = t.CONFIG_PATH
        self._orig_backup_dir = t.BACKUP_DIR
        self._orig_run = t._youdao_run
        t.CONFIG_PATH = self.sandbox / ".knowledge-distill-config.json"
        t.BACKUP_DIR = self.sandbox / "backups"
        t.save_config({"format": "youdao", "note_root": "AI笔记"})
        self.fake = _FakeYoudao()
        t._youdao_run = self.fake.run

    def tearDown(self):
        t._youdao_run = self._orig_run
        t.CONFIG_PATH = self._orig_config
        t.BACKUP_DIR = self._orig_backup_dir
        shutil.rmtree(self.sandbox, ignore_errors=True)

    # ------------------------------------------------------------ 链接渲染
    def test_render_note_link_youdao_is_plain_text(self):
        self.assertEqual(t.render_note_link("标题", fmt="youdao"), "标题")
        self.assertTrue(t._is_youdao_format())

    # ------------------------------------------------------------ CLI 定位
    def test_youdao_cli_env_override_wins(self):
        with mock.patch.dict(t.os.environ, {"KNOWLEDGE_DISTILL_YOUDAO_CLI": "/custom/youdaonote"}):
            self.assertEqual(t._youdao_cli(), "/custom/youdaonote")

    def test_youdao_cli_falls_back_to_path(self):
        env = {k: v for k, v in t.os.environ.items() if k != "KNOWLEDGE_DISTILL_YOUDAO_CLI"}
        with mock.patch.dict(t.os.environ, env, clear=True), \
                mock.patch.object(t, "_YOUDAO_BIN_DIR", self.sandbox / "missing"):
            self.assertEqual(t._youdao_cli(), "youdaonote")

    def test_youdao_cli_prefers_skill_managed_bin_dir(self):
        bin_dir = self.sandbox / "bin"
        bin_dir.mkdir()
        exe = bin_dir / t._YOUDAO_EXE_NAME
        exe.write_text("x", encoding="utf-8")
        env = {k: v for k, v in t.os.environ.items() if k != "KNOWLEDGE_DISTILL_YOUDAO_CLI"}
        with mock.patch.dict(t.os.environ, env, clear=True), \
                mock.patch.object(t, "_YOUDAO_BIN_DIR", bin_dir):
            self.assertEqual(t._youdao_cli(), str(exe))

    # ------------------------------------------------------------ 结构 / 查重
    def test_list_structure_missing_root(self):
        self.assertFalse(t.youdao_list_structure("AI笔记")["exists"])

    def test_check_name_free_then_conflict(self):
        free = t.youdao_check_name("AI笔记/示例分类", "新笔记")
        self.assertTrue(free["valid"])
        self.assertFalse(free["exists"])
        t.youdao_write_note("AI笔记/示例分类/新笔记.md", "x\n")
        conflict = t.youdao_check_name("AI笔记/示例分类", "新笔记")
        self.assertTrue(conflict["exists"])
        self.assertIn("file_id", conflict)

    def test_check_name_empty_title(self):
        self.assertFalse(t.youdao_check_name("AI笔记/示例分类", "  ")["ok"])

    # ------------------------------------------------------------ 写入
    def test_write_note_creates_note_and_folder(self):
        r = t.youdao_write_note("AI笔记/示例分类/示例笔记.md", "# 标题\n\n正文\n")
        self.assertTrue(r["ok"])
        self.assertEqual(r["action"], "created")
        self.assertIsNotNone(r["file_id"])
        cats = {c["name"]: c for c in t.youdao_list_structure("AI笔记")["categories"]}
        self.assertIn("示例分类", cats)
        # 有道靠标题后缀区分笔记类型：创建时必须带 .md，否则客户端无法预览
        self.assertIn("示例笔记.md", cats["示例分类"]["notes"])

    def test_index_note_has_md_suffix(self):
        t.youdao_append_index_entry("AI笔记", "示例分类", "标题A", "摘要A")
        names = [n["name"] for n in self.fake.nodes.values() if not n["dir"]]
        self.assertIn("总目录.md", names)

    def test_write_note_overwrite_backs_up_old_content(self):
        t.youdao_write_note("AI笔记/示例分类/笔记.md", "旧内容\n")
        r = t.youdao_write_note("AI笔记/示例分类/笔记.md", "新内容\n")
        self.assertEqual(r["action"], "overwritten")
        self.assertIsNotNone(r["backup"])
        self.assertIn("旧内容", Path(r["backup"]).read_text(encoding="utf-8"))

    def test_write_note_unchanged_skips_backup(self):
        t.youdao_write_note("AI笔记/示例分类/笔记.md", "内容\n")
        r = t.youdao_write_note("AI笔记/示例分类/笔记.md", "内容\n")
        self.assertEqual(r["action"], "unchanged")
        self.assertIsNone(r["backup"])

    def test_write_note_normalizes_crlf_for_unchanged(self):
        t.youdao_write_note("AI笔记/示例分类/笔记.md", "一行\n二行\n")
        r = t.youdao_write_note("AI笔记/示例分类/笔记.md", "一行\r\n二行\r\n")
        self.assertEqual(r["action"], "unchanged")

    # ------------------------------------------------------------ 索引
    def test_append_index_entry_creates_then_updates(self):
        r1 = t.youdao_append_index_entry("AI笔记", "示例分类", "标题A", "摘要A")
        self.assertEqual(r1["action"], "created")
        idx = t.youdao_list_index("AI笔记")
        self.assertTrue(idx["exists"])
        self.assertIn("## 示例分类", idx["content"])
        self.assertIn("标题A", idx["content"])
        r2 = t.youdao_append_index_entry("AI笔记", "示例分类", "标题A", "摘要B")
        self.assertEqual(r2["action"], "updated")
        self.assertIn("摘要B", t.youdao_list_index("AI笔记")["content"])

    def test_append_index_question_plain_links_and_merge(self):
        r1 = t.youdao_append_index_question("AI笔记", "示例分类", "疑问？", "笔记A")
        self.assertTrue(r1["ok"])
        self.assertIn("笔记A", r1["entry"])
        r2 = t.youdao_append_index_question("AI笔记", "示例分类", "疑问？", "笔记B")
        self.assertIn("笔记A", r2["entry"])
        self.assertIn("笔记B", r2["entry"])
        r3 = t.youdao_append_index_question("AI笔记", "示例分类", "疑问？", "笔记B")
        self.assertEqual(r3["action"], "unchanged")
        qs = t.youdao_list_questions("AI笔记")
        self.assertEqual(qs["count"], 1)
        self.assertEqual(set(qs["questions"][0]["links"]), {"笔记A", "笔记B"})

    def test_append_index_question_rejects_empty(self):
        self.assertFalse(t.youdao_append_index_question("AI笔记", "示例分类", "  ", "笔记A")["ok"])

    # ------------------------------------------------------------ 检索
    def test_search_notes_finds_body_and_snippet(self):
        t.youdao_write_note("AI笔记/示例分类/幂等笔记.md",
                            "# 幂等\n\n按电梯按钮一次与多次结果相同。\n")
        r = t.youdao_search_notes("AI笔记", "电梯")
        self.assertTrue(r["ok"])
        self.assertEqual(r["matched_notes"], 1)
        self.assertIn("电梯", r["hits"][0]["snippets"][0]["snippet"])

    def test_search_notes_invalid_regex(self):
        self.assertFalse(t.youdao_search_notes("AI笔记", "(", use_regex=True)["ok"])

    def test_search_notes_full_returns_content(self):
        t.youdao_write_note("AI笔记/示例分类/笔记.md", "含关键字的正文\n")
        r = t.youdao_search_notes("AI笔记", "关键字", full=True)
        self.assertIn("content", r["hits"][0])

    # ------------------------------------------------------------ 备份 / 回退
    def test_list_backups_and_restore(self):
        t.youdao_write_note("AI笔记/示例分类/笔记.md", "第一版\n")
        t.youdao_write_note("AI笔记/示例分类/笔记.md", "第二版\n")
        backups = t.youdao_list_backups("AI笔记/示例分类/笔记.md")
        self.assertEqual(backups["count"], 1)
        self.assertTrue(backups["backups"][0]["attributable"])
        r = t.youdao_restore_note("AI笔记/示例分类/笔记.md")
        self.assertTrue(r["ok"])
        self.assertEqual(r["action"], "restored")
        folder_id = t._youdao_folder_id(["AI笔记", "示例分类"])
        _, content = t._youdao_read_note(folder_id, "笔记")
        self.assertIn("第一版", content)

    def test_restore_without_backup_fails(self):
        t.youdao_write_note("AI笔记/示例分类/笔记.md", "内容\n")
        self.assertFalse(t.youdao_restore_note("AI笔记/示例分类/笔记.md")["ok"])

    # ------------------------------------------------------------ 就绪检测 / 错误
    def test_ready_reports_missing_cli(self):
        with mock.patch.object(t.subprocess, "run", side_effect=FileNotFoundError):
            result = t.youdao_ready()
        self.assertFalse(result["ok"])
        self.assertFalse(result["cli_installed"])

    def test_ready_parses_checks(self):
        class _Proc:
            returncode = 0
            stdout = '{"ok": true, "checks": [{"name": "api-key", "status": "pass"}]}'
            stderr = ""

        with mock.patch.object(t.subprocess, "run", return_value=_Proc()):
            result = t.youdao_ready()
        self.assertTrue(result["ok"])
        self.assertTrue(result["cli_installed"])

    def test_youdao_guard_wraps_error_as_dict(self):
        def boom(*args, **kwargs):
            raise t.YoudaoError("有道认证失败")

        result = t._youdao_guard(boom)
        self.assertFalse(result["ok"])
        self.assertIn("认证失败", result["error"])

    def test_error_kind_classification(self):
        self.assertEqual(t._youdao_error_kind("API Key 未配置"), "auth")
        self.assertEqual(t._youdao_error_kind("error: unknown option '--json'"), "permanent")
        self.assertEqual(t._youdao_error_kind("429 Too Many Requests"), "transient")

    def _count_run_attempts(self, returncode, stderr):
        """跑一次 _youdao_run，返回 subprocess.run 的调用次数（预期抛 YoudaoError）。"""
        class _Proc:
            stdout = ""

            def __init__(self, rc, err):
                self.returncode = rc
                self.stderr = err

        calls = {"n": 0}

        def fake_run(*args, **kwargs):
            calls["n"] += 1
            return _Proc(returncode, stderr)

        with mock.patch.object(t.subprocess, "run", side_effect=fake_run), \
                mock.patch.object(t.time, "sleep", return_value=None):
            with self.assertRaises(t.YoudaoError):
                self._orig_run("listNotes", {"parentId": "0"})  # 真实现（setUp 已把 t._youdao_run 换成假后端）
        return calls["n"]

    def test_permanent_error_is_not_retried(self):
        self.assertEqual(self._count_run_attempts(1, "error: unknown option '--json'"), 1)

    def test_auth_error_is_not_retried(self):
        self.assertEqual(self._count_run_attempts(1, "API Key 未配置"), 1)

    def test_transient_error_is_retried(self):
        self.assertEqual(self._count_run_attempts(1, "429 Too Many Requests"),
                         t._YOUDAO_RETRY_ATTEMPTS)

    def test_run_parses_json_on_success(self):
        class _Proc:
            returncode = 0
            stdout = '{"entries": [{"id": "1", "name": "示例"}]}'
            stderr = ""

        with mock.patch.object(t.subprocess, "run", return_value=_Proc()):
            result = self._orig_run("listNotes", {"parentId": "0"})
        self.assertEqual(result["entries"][0]["name"], "示例")

    def test_ready_handles_timeout(self):
        with mock.patch.object(t.subprocess, "run",
                               side_effect=t.subprocess.TimeoutExpired(cmd="youdaonote", timeout=30)):
            result = t.youdao_ready()
        self.assertFalse(result["ok"])
        self.assertTrue(result["cli_installed"])

    def test_youdao_toc_has_category_section(self):
        t.youdao_append_index_entry("AI笔记", "示例分类", "标题A", "摘要A")
        content = t.youdao_list_index("AI笔记")["content"]
        self.assertNotIn("# 总目录", content)
        self.assertIn("## 示例分类", content)

    def test_youdao_lint_notes(self):
        t.youdao_write_note("AI笔记/示例分类/笔记A.md", "# 笔记A\n\n正文\n")
        t.youdao_append_index_entry("AI笔记", "示例分类", "笔记A", "摘要")
        r = t.youdao_lint_notes("AI笔记")
        self.assertTrue(r["ok"])
        self.assertEqual(r["unindexed_notes"], [])
        self.assertEqual(r["index_orphans"], [])
        self.assertIn("stale_index", r["not_checked"])
        # 新增未收录笔记 -> 被检出
        t.youdao_write_note("AI笔记/示例分类/笔记B.md", "# 笔记B\n")
        r2 = t.youdao_lint_notes("AI笔记")
        self.assertEqual([x["note"] for x in r2["unindexed_notes"]], ["笔记B.md"])

    def test_parse_output_tolerates_surrounding_text(self):
        self.assertEqual(t._youdao_parse_output('提示: {"a": 1} 结束'), {"a": 1})
        self.assertEqual(t._youdao_parse_output(""), {})

    def test_normalize_and_title_key(self):
        self.assertEqual(t._youdao_title_key("标题.md"), "标题")
        self.assertEqual(t._youdao_title_key("  标题  "), "标题")
        self.assertEqual(t._normalize_newlines("a\r\nb\rc"), "a\nb\nc")


if __name__ == "__main__":
    unittest.main(verbosity=2)
