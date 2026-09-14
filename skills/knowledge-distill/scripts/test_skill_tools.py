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
        self.assertTrue(cats["示例分类"]["has_index"])

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
        self.assertFalse(cats["空分类"]["has_index"])
        self.assertEqual(cats["空分类"]["notes"], [])

    def test_list_structure_missing_root(self):
        self.assertFalse(t.list_structure(str(self.sandbox / "不存在"))["exists"])

    # ------------------------------------------------------------ 索引读取
    def test_list_index_reads_content(self):
        _, cat = self._make_category()
        result = t.list_index(str(cat))
        self.assertTrue(result["exists"])
        self.assertIn("index", result["content"])

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
        cat = self.sandbox / "AI笔记" / "示例分类"
        cat.mkdir(parents=True)
        result = t.append_index_entry(str(cat), "示例笔记标题", "示例摘要")
        self.assertTrue(result["ok"])
        self.assertEqual(result["action"], "created")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("| 示例笔记标题 | 示例摘要 | [[示例笔记标题]] |", content)

    def test_append_index_entry_appends_row(self):
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_entry(str(cat), "笔记A", "摘要A")
        result = t.append_index_entry(str(cat), "笔记B", "摘要B")
        self.assertEqual(result["action"], "appended")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("| 笔记A | 摘要A | [[笔记A]] |", content)
        self.assertIn("| 笔记B | 摘要B | [[笔记B]] |", content)

    def test_append_index_entry_updates_existing(self):
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_entry(str(cat), "笔记A", "旧摘要")
        result = t.append_index_entry(str(cat), "笔记A", "新摘要")
        self.assertEqual(result["action"], "updated")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("新摘要", content)
        self.assertNotIn("旧摘要", content)
        self.assertEqual(content.count("| 笔记A |"), 1)

    def test_append_index_entry_unchanged(self):
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_entry(str(cat), "笔记A", "摘要")
        result = t.append_index_entry(str(cat), "笔记A", "摘要")
        self.assertEqual(result["action"], "unchanged")

    def test_append_index_entry_preserves_existing_content(self):
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        index = cat / "00-分类索引.md"
        index.write_text("---\ntags:\n  - 测试\n---\n\n# 分类索引 —— 分类\n\n"
                         "## 笔记导航\n\n| 笔记 | 主题摘要 | 链接 |\n| ---- | -------- | ---- |\n\n"
                         "## 已收录疑问\n\n- 疑问A → [[笔记A]]\n", encoding="utf-8")
        t.append_index_entry(str(cat), "笔记B", "摘要B")
        content = index.read_text(encoding="utf-8")
        self.assertIn("tags:", content)
        self.assertIn("## 已收录疑问", content)
        self.assertIn("- 疑问A → [[笔记A]]", content)
        self.assertIn("| 笔记B | 摘要B | [[笔记B]] |", content)

    def test_append_index_entry_missing_category(self):
        result = t.append_index_entry(str(self.sandbox / "不存在"), "标题", "摘要")
        self.assertFalse(result["ok"])

    # ------------------------------------------------------------ 表格转义
    def test_escape_table_cell_pipe_and_newline(self):
        self.assertEqual(t.escape_table_cell("含|竖线"), "含\\|竖线")
        self.assertEqual(t.escape_table_cell("第一行\n第二行"), "第一行 第二行")
        self.assertEqual(t.escape_table_cell("  空白  "), "空白")

    def test_append_index_entry_escapes_pipe_in_title_and_summary(self):
        """标题/摘要含竖线时不得破坏表格结构。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        result = t.append_index_entry(str(cat), "含|竖线的标题", "摘要含|竖线")
        self.assertTrue(result["ok"])
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        row = "| 含\\|竖线的标题 | 摘要含\\|竖线 | [[含\\|竖线的标题]] |"
        self.assertIn(row, content)
        # 该行应恰好有 4 个未转义竖线（3 个单元格的边界），未被内容中的竖线切碎
        data_line = [ln for ln in content.splitlines() if ln.startswith("| 含")][0]
        unescaped = data_line.count("|") - data_line.count("\\|")
        self.assertEqual(unescaped, 4)

    def test_append_index_entry_escapes_newline_in_summary(self):
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_entry(str(cat), "标题", "第一行\n第二行")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
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
        """脚本新建的索引应与模板结构一致（含章节与标题，但不自带 AIGC 标识）。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_entry(str(cat), "笔记A", "摘要A")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("## 笔记导航", content)
        self.assertIn("## 已收录疑问", content)
        self.assertIn("# 分类索引 —— 分类", content)
        self.assertNotIn("{{分类名}}", content)
        self.assertNotIn("（此处分点记录", content)
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

    def test_render_index_template_strips_injected_aigc(self):
        """模板被 hook 注入 AIGC 后，渲染结果仍不应携带该标识。"""
        injected = ("---\n"
                    "AIGC:\n"
                    "  ContentProducer: '001191110102MAD55U9H0F10002'\n"
                    "  ProduceID: 'deadbeef-dead-beef-dead-beefdeadbeef'\n"
                    "  Label: '1'\n"
                    "---\n\n"
                    "# 分类索引 —— {{分类名}}\n\n"
                    "## 笔记导航\n\n| 笔记 | 主题摘要 | 链接 |\n| ---- | -------- | ---- |\n\n"
                    "## 已收录疑问\n\n> AI生成\n")
        original = t.INDEX_TEMPLATE_PATH
        t.INDEX_TEMPLATE_PATH = self.sandbox / "被注入的模板.md"
        t.INDEX_TEMPLATE_PATH.write_text(injected, encoding="utf-8")
        try:
            rendered = t._render_index_template("测试")
            self.assertNotIn("AIGC", rendered)
            self.assertNotIn("ProduceID", rendered)
            self.assertNotIn("AI生成", rendered)
            self.assertIn("# 分类索引 —— 测试", rendered)
            self.assertIn("## 笔记导航", rendered)
        finally:
            t.INDEX_TEMPLATE_PATH = original

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

    def test_created_index_falls_back_when_template_missing(self):
        """模板文件缺失时应使用内置兜底模板，仍保证两个章节存在。"""
        original = t.INDEX_TEMPLATE_PATH
        t.INDEX_TEMPLATE_PATH = self.sandbox / "不存在模板.md"
        try:
            cat = self.sandbox / "AI笔记" / "兜底分类"
            cat.mkdir(parents=True)
            result = t.append_index_entry(str(cat), "笔记A", "摘要A")
            self.assertTrue(result["ok"])
            content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
            self.assertIn("# 分类索引 —— 兜底分类", content)
            self.assertIn("## 笔记导航", content)
            self.assertIn("## 已收录疑问", content)
            self.assertIn("| 笔记A | 摘要A | [[笔记A]] |", content)
        finally:
            t.INDEX_TEMPLATE_PATH = original

    def test_created_index_keeps_question_section_after_row(self):
        """追加行后「已收录疑问」章节仍位于表格之后。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_entry(str(cat), "笔记A", "摘要A")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertLess(content.index("| 笔记A |"), content.index("## 已收录疑问"))

    # ------------------------------------------------------------ 已收录疑问
    def test_append_index_question_creates_and_formats(self):
        """疑问条目必须统一为 `- 疑问 → [[笔记标题]]` 双链格式。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        result = t.append_index_question(str(cat), "示例疑问？", "示例笔记标题")
        self.assertTrue(result["ok"])
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("- 示例疑问？ → [[示例笔记标题]]", content)

    def test_append_index_question_appends_to_section(self):
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_question(str(cat), "疑问一", "笔记A")
        result = t.append_index_question(str(cat), "疑问二", "笔记B")
        self.assertEqual(result["action"], "appended")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("- 疑问一 → [[笔记A]]", content)
        self.assertIn("- 疑问二 → [[笔记B]]", content)
        # 两条疑问都应位于「已收录疑问」章节内
        self.assertLess(content.index("## 已收录疑问"), content.index("- 疑问一"))
        self.assertLess(content.index("- 疑问一"), content.index("- 疑问二"))

    def test_append_index_question_merges_multiple_links(self):
        """同一疑问指向不同笔记时**合并**链接：保留旧的、追加新的，不覆盖、不重复。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_question(str(cat), "同一个疑问", "笔记A")
        result = t.append_index_question(str(cat), "同一个疑问", "笔记B")
        self.assertEqual(result["action"], "updated")
        self.assertEqual(result["links"], ["笔记A", "笔记B"])
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("- 同一个疑问 → [[笔记A]]、[[笔记B]]", content)
        self.assertEqual(content.count("- 同一个疑问"), 1)

    def test_append_index_question_unchanged(self):
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_question(str(cat), "疑问", "笔记A")
        result = t.append_index_question(str(cat), "疑问", "笔记A")
        self.assertEqual(result["action"], "unchanged")

    def test_append_index_question_creates_missing_section(self):
        """索引缺少「已收录疑问」章节时自动补建。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        (cat / "00-分类索引.md").write_text(
            "# 分类索引 —— 分类\n\n## 笔记导航\n\n| 笔记 | 主题摘要 | 链接 |\n"
            "| ---- | -------- | ---- |\n", encoding="utf-8")
        result = t.append_index_question(str(cat), "新疑问", "笔记A")
        self.assertEqual(result["action"], "section_created")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("## 已收录疑问", content)
        self.assertIn("- 新疑问 → [[笔记A]]", content)

    def test_append_index_question_rejects_empty(self):
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        self.assertFalse(t.append_index_question(str(cat), "   ", "笔记A")["ok"])

    def test_append_index_question_missing_category(self):
        self.assertFalse(t.append_index_question(str(self.sandbox / "不存在"), "疑问", "笔记A")["ok"])

    def test_append_index_question_section_title_with_extra_spaces(self):
        """章节标题带多余空格时仍应识别为已有章节，而不是重复创建。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        (cat / "00-分类索引.md").write_text(
            "# 索引\n\n##  已收录疑问  \n\n- 旧疑问 → [[旧笔记]]\n", encoding="utf-8")
        result = t.append_index_question(str(cat), "新疑问", "笔记A")
        self.assertEqual(result["action"], "appended")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertEqual(content.count("已收录疑问"), 1)
        self.assertIn("- 新疑问 → [[笔记A]]", content)

    def test_append_index_question_flattens_newlines(self):
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_question(str(cat), "疑问\n换行", "笔记A")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("- 疑问 换行 → [[笔记A]]", content)

    def test_append_index_question_does_not_break_navigation(self):
        """疑问写入后，笔记导航表格结构保持完整。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_entry(str(cat), "笔记A", "摘要A")
        t.append_index_question(str(cat), "疑问一", "笔记A")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("| 笔记A | 摘要A | [[笔记A]] |", content)
        self.assertLess(content.index("| 笔记A |"), content.index("## 已收录疑问"))
        self.assertLess(content.index("## 已收录疑问"), content.index("- 疑问一"))

    def test_append_index_question_blank_line_before_trailing_quote(self):
        """疑问条目与末尾引用块之间必须有空行，避免 Markdown 渲染粘连。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        (cat / "00-分类索引.md").write_text(
            "# 索引\n\n## 已收录疑问\n\n> AI生成\n", encoding="utf-8")
        t.append_index_question(str(cat), "疑问一", "笔记A")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("- 疑问一 → [[笔记A]]\n\n> AI生成", content)

    def test_append_index_question_keeps_blank_between_entries_and_quote(self):
        """连续追加多条疑问时条目之间不插空行；已有引用块前保留空行。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        (cat / "00-分类索引.md").write_text(
            "# 索引\n\n## 已收录疑问\n\n> AI生成\n", encoding="utf-8")
        t.append_index_question(str(cat), "疑问一", "笔记A")
        t.append_index_question(str(cat), "疑问二", "笔记B")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("- 疑问一 → [[笔记A]]\n- 疑问二 → [[笔记B]]", content)
        self.assertIn("- 疑问二 → [[笔记B]]\n\n> AI生成", content)

    def test_append_index_question_next_section_with_extra_spaces(self):
        """后续章节标题带多余空格时仍应被识别为边界，疑问不得写入该章节。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        (cat / "00-分类索引.md").write_text(
            "# 索引\n\n## 已收录疑问\n\n- 旧疑问 → [[旧笔记]]\n\n"
            "##  其他章节  \n\n- 别的内容\n", encoding="utf-8")
        t.append_index_question(str(cat), "新疑问", "笔记A")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertLess(content.index("- 新疑问"), content.index("##  其他章节"))

    def test_append_index_question_merge_is_idempotent(self):
        """重复写入同一（疑问, 笔记）组合不应产生重复链接。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_question(str(cat), "疑问", "笔记A")
        t.append_index_question(str(cat), "疑问", "笔记B")
        result = t.append_index_question(str(cat), "疑问", "笔记A")
        self.assertEqual(result["action"], "unchanged")
        self.assertEqual(result["links"], ["笔记A", "笔记B"])
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertEqual(content.count("[[笔记A]]"), 1)

    def test_append_index_question_link_order_preserved(self):
        """合并链接时保持首次写入顺序，新链接追加在末尾。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_question(str(cat), "疑问", "笔记A")
        t.append_index_question(str(cat), "疑问", "笔记B")
        t.append_index_question(str(cat), "疑问", "笔记C")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("- 疑问 → [[笔记A]]、[[笔记B]]、[[笔记C]]", content)

    def test_append_index_question_warns_when_too_many_links(self):
        """一条疑问指向超过 3 篇笔记时给出 warning，但不拦截写入。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        for title in ("笔记A", "笔记B", "笔记C"):
            t.append_index_question(str(cat), "疑问", title)
        result = t.append_index_question(str(cat), "疑问", "笔记D")
        self.assertTrue(result["ok"])
        self.assertIn("warning", result)
        self.assertEqual(len(result["links"]), 4)

    def test_append_index_question_normalizes_legacy_plain_answer(self):
        """旧格式（→ 后是纯文本回答）命中时规范为链接格式，回答不再重复承载。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        (cat / "00-分类索引.md").write_text(
            "# 索引\n\n## 已收录疑问\n\n- 旧疑问？→ 这是一句旧回答。\n", encoding="utf-8")
        result = t.append_index_question(str(cat), "旧疑问？", "笔记A")
        self.assertEqual(result["action"], "updated")
        self.assertTrue(result["normalized"])
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("- 旧疑问？ → [[笔记A]]", content)
        self.assertNotIn("这是一句旧回答", content)

    def test_append_index_question_matches_legacy_arrow_without_space(self):
        """历史写法的 `？→ 回答`（箭头前无空格）也能被识别为同一疑问。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        (cat / "00-分类索引.md").write_text(
            "# 索引\n\n## 已收录疑问\n\n- 旧疑问？→ 旧回答\n", encoding="utf-8")
        t.append_index_question(str(cat), "旧疑问？", "笔记A")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertEqual(content.count("- 旧疑问？"), 1)

    # ------------------------------------------------------------ 疑问查重
    def test_list_questions_parses_questions_and_links(self):
        """list-questions 应解析出疑问原文与已并列的笔记链接。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_question(str(cat), "疑问一", "笔记A")
        t.append_index_question(str(cat), "疑问一", "笔记B")
        t.append_index_question(str(cat), "疑问二", "笔记C")
        result = t.list_questions(str(cat))
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["questions"][0]["question"], "疑问一")
        self.assertEqual(result["questions"][0]["links"], ["笔记A", "笔记B"])
        self.assertEqual(result["questions"][1]["links"], ["笔记C"])

    def test_list_questions_flags_legacy_entry_without_links(self):
        """旧格式条目的 links 为空，便于识别并迁移。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        (cat / "00-分类索引.md").write_text(
            "# 索引\n\n## 已收录疑问\n\n- 旧疑问？→ 旧回答\n", encoding="utf-8")
        result = t.list_questions(str(cat))
        self.assertEqual(result["questions"][0]["question"], "旧疑问？")
        self.assertEqual(result["questions"][0]["links"], [])

    def test_list_questions_missing_index(self):
        """分类目录存在但尚无索引文件时，返回空列表而非报错。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        result = t.list_questions(str(cat))
        self.assertTrue(result["ok"])
        self.assertFalse(result["exists"])
        self.assertEqual(result["count"], 0)

    def test_list_questions_missing_category(self):
        self.assertFalse(t.list_questions(str(self.sandbox / "不存在"))["ok"])

    def test_list_questions_ignores_template_placeholder(self):
        """模板占位行（以"（"开头）不应被当成真实疑问。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        (cat / "00-分类索引.md").write_text(
            "# 索引\n\n## 已收录疑问\n\n- （此处分点记录关键疑问）\n", encoding="utf-8")
        result = t.list_questions(str(cat))
        self.assertEqual(result["count"], 0)

    # ------------------------------------------------------------ 健康检查
    def _make_root(self):
        """建一个含单个分类的笔记根目录，返回 (root, cat)。"""
        root = self.sandbox / "AI笔记"
        cat = root / "分类A"
        cat.mkdir(parents=True)
        return root, cat

    def _write_index(self, cat, rows):
        """写入含指定笔记导航行的索引文件；rows 为 (标题, 链接目标) 列表。"""
        lines = ["# 分类索引", "", "## 笔记导航", "",
                 "| 笔记 | 主题摘要 | 链接 |", "| ---- | -------- | ---- |"]
        for title, target in rows:
            lines.append(f"| {title} | 摘要 | [[{target}]] |")
        lines.extend(["", "## 已收录疑问", ""])
        (cat / "00-分类索引.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_lint_notes_healthy_library(self):
        """索引与笔记一致、无断链时应报告 0 问题。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n内容\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
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
        self._write_index(cat, [("已删笔记", "已删笔记")])
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["index_orphans"]), 1)
        self.assertEqual(result["index_orphans"][0]["target"], "已删笔记")

    def test_lint_notes_detects_broken_link(self):
        """双链指向不存在的笔记 -> broken_links。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n见 [[不存在的笔记]]\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["broken_links"]), 1)
        self.assertEqual(result["broken_links"][0]["target"], "不存在的笔记")

    def test_lint_notes_detects_unindexed_note(self):
        """笔记存在但索引未收录 -> unindexed_notes。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        (cat / "笔记B.md").write_text("# 笔记B\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        names = [x["note"] for x in result["unindexed_notes"]]
        self.assertEqual(names, ["笔记B.md"])

    def test_lint_notes_detects_orphan_note(self):
        """无入链且未收录 -> orphan_notes（同时也会计入 unindexed_notes）。"""
        root, cat = self._make_root()
        (cat / "孤儿.md").write_text("# 孤儿\n", encoding="utf-8")
        self._write_index(cat, [])
        result = t.lint_notes(str(root))
        self.assertEqual([x["note"] for x in result["orphan_notes"]], ["孤儿.md"])
        self.assertEqual([x["note"] for x in result["unindexed_notes"]], ["孤儿.md"])

    def test_lint_notes_detects_question_orphan(self):
        """「已收录疑问」里的链接指向不存在的笔记 -> question_orphans。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        t.append_index_question(str(cat), "疑问一", "已删笔记")
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["question_orphans"]), 1)
        self.assertEqual(result["question_orphans"][0]["target"], "已删笔记")
        self.assertEqual(result["question_orphans"][0]["question"], "疑问一")

    def test_lint_notes_question_links_ok_not_reported(self):
        """疑问链接指向存在的笔记时不应报告问题。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        t.append_index_question(str(cat), "疑问一", "笔记A")
        result = t.lint_notes(str(root))
        self.assertEqual(result["question_orphans"], [])
        self.assertEqual(result["summary"]["issues"], 0)

    def test_lint_notes_detects_broken_markdown_question_link(self):
        """普通 Markdown 索引里的疑问链接失效也应被检出。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        (cat / "00-分类索引.md").write_text(
            "# 索引\n\n## 笔记导航\n\n| 笔记 | 主题摘要 | 链接 |\n"
            "| ---- | -------- | ---- |\n| 笔记A | 摘要 | [笔记A](笔记A.md) |\n\n"
            "## 已收录疑问\n\n- 疑问一 → [已删笔记](已删笔记.md)\n", encoding="utf-8")
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["question_orphans"]), 1)
        self.assertEqual(result["question_orphans"][0]["target"], "已删笔记")

    def test_lint_notes_question_orphan_counts_into_total(self):
        """question_orphans 应计入 summary.issues 总数。"""
        root, cat = self._make_root()
        self._write_index(cat, [])
        t.append_index_question(str(cat), "疑问一", "已删笔记")
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
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["orphan_notes"], [])

    def test_lint_notes_inlink_prevents_orphan(self):
        """有其它笔记双链指向、但未被索引收录 -> 不算孤立，但仍计入未收录。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n见 [[笔记B]]\n", encoding="utf-8")
        (cat / "笔记B.md").write_text("# 笔记B\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["orphan_notes"], [])
        self.assertEqual([x["note"] for x in result["unindexed_notes"]], ["笔记B.md"])

    def test_lint_notes_ignores_links_in_code(self):
        """行内代码与围栏代码块中的 [[...]] 是语法示例，不得误报断链。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n双链 `[[笔记名]]` 与 `[[笔记]]` 的写法：\n\n"
            "```\n[[代码里的链接]]\n```\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])

    def test_lint_notes_handles_alias_and_anchor(self):
        """[[目标|别名]] 与 [[目标#锚点]] 应按目标名判断，不算断链。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n[[笔记B|自定义文字]] 和 [[笔记B#章节]]\n", encoding="utf-8")
        (cat / "笔记B.md").write_text("# 笔记B\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A"), ("笔记B", "笔记B")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])

    def test_lint_notes_handles_category_prefixed_link(self):
        """[[分类/笔记名]] 形式应能正确解析出笔记名。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n[[分类A/笔记B]]\n", encoding="utf-8")
        (cat / "笔记B.md").write_text("# 笔记B\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A"), ("笔记B", "笔记B")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])

    def test_lint_notes_ignores_self_link(self):
        """自链接不计入入链，笔记未被索引收录时仍应算孤立。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n[[笔记A]]\n", encoding="utf-8")
        self._write_index(cat, [])
        result = t.lint_notes(str(root))
        self.assertEqual([x["note"] for x in result["orphan_notes"]], ["笔记A.md"])

    def test_lint_notes_index_file_not_treated_as_note(self):
        """索引文件本身不是笔记，不得计入 unindexed_notes 或孤立笔记。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["summary"]["notes"], 1)
        self.assertEqual(result["unindexed_notes"], [])

    def test_lint_notes_missing_index_counts_all_unindexed(self):
        """分类没有索引文件时，其中所有笔记都应计入未收录。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        result = t.lint_notes(str(root))
        self.assertFalse(result["unindexed_notes"][0]["has_index"])
        self.assertEqual(len(result["unindexed_notes"]), 1)

    def test_lint_notes_missing_root_fails(self):
        """笔记根目录不存在时返回 ok=False。"""
        result = t.lint_notes(str(self.sandbox / "不存在"))
        self.assertFalse(result["ok"])

    def test_lint_notes_does_not_modify_files(self):
        """健康检查是只读操作，不得改动任何文件内容。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n[[断链]]\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A"), ("幽灵", "幽灵")])
        before = {p: p.read_text(encoding="utf-8") for p in root.rglob("*") if p.is_file()}
        t.lint_notes(str(root))
        after = {p: p.read_text(encoding="utf-8") for p in root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_lint_notes_parses_index_without_link(self):
        """索引行未写双链时，退回第一列文本判断收录，避免误报未收录。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        (cat / "00-分类索引.md").write_text(
            "# 索引\n\n## 笔记导航\n\n| 笔记 | 主题摘要 | 链接 |\n"
            "| ---- | -------- | ---- |\n| 笔记A | 摘要 |  |\n", encoding="utf-8")
        result = t.lint_notes(str(root))
        self.assertEqual(result["unindexed_notes"], [])
        self.assertEqual(result["index_orphans"], [])

    def test_lint_notes_summary_counts(self):
        """summary 应正确统计分类数、笔记数、问题总数。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n[[断链]]\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A"), ("幽灵", "幽灵")])
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
        """普通 Markdown 下索引应生成标准链接，而非双链。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        result = t.append_index_entry(str(cat), "笔记A", "摘要A", fmt="markdown")
        self.assertTrue(result["ok"])
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("| 笔记A | 摘要A | [笔记A](笔记A.md) |", content)
        self.assertNotIn("[[笔记A]]", content)

    def test_append_index_question_markdown_format(self):
        """普通 Markdown 下疑问条目也应使用标准链接。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        result = t.append_index_question(str(cat), "如何排查？", "笔记A", fmt="markdown")
        self.assertTrue(result["ok"])
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn("- 如何排查？ → [笔记A](笔记A.md)", content)

    def test_append_index_question_markdown_multi_links(self):
        """普通 Markdown 下多链接也用标准链接，以顿号分隔。"""
        cat = self.sandbox / "AI笔记" / "分类"
        cat.mkdir(parents=True)
        t.append_index_question(str(cat), "如何排查？", "笔记A", fmt="markdown")
        t.append_index_question(str(cat), "如何排查？", "笔记B", fmt="markdown")
        content = (cat / "00-分类索引.md").read_text(encoding="utf-8")
        self.assertIn(
            "- 如何排查？ → [笔记A](笔记A.md)、[笔记B](笔记B.md)", content)

    def test_lint_notes_recognizes_markdown_links(self):
        """标准 Markdown 链接应被识别为入链，不误报断链或孤立。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        (cat / "笔记B.md").write_text(
            "# 笔记B\n\n见 [笔记A](笔记A.md)。\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A"), ("笔记B", "笔记B")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])
        self.assertEqual(result["orphan_notes"], [])
        self.assertEqual(result["unindexed_notes"], [])

    def test_lint_notes_markdown_index_parsed(self):
        """索引里的标准 Markdown 链接应被正确解析为收录条目。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        (cat / "00-分类索引.md").write_text(
            "# 索引\n\n## 笔记导航\n\n| 笔记 | 主题摘要 | 链接 |\n"
            "| ---- | -------- | ---- |\n| 笔记A | 摘要 | [笔记A](笔记A.md) |\n",
            encoding="utf-8")
        result = t.lint_notes(str(root))
        self.assertEqual(result["unindexed_notes"], [])
        self.assertEqual(result["index_orphans"], [])

    def test_lint_notes_detects_broken_markdown_link(self):
        """标准 Markdown 链接指向不存在的笔记时应报断链。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n见 [不存在的笔记](不存在的笔记.md)。\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
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
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])

    def test_lint_notes_ignores_markdown_link_in_code(self):
        """代码块里的标准 Markdown 链接是示例，不应报断链。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n```markdown\n[示例](不存在.md)\n```\n\n"
            "行内 `[示例](也不存在.md)` 同理。\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["broken_links"], [])

    def test_lint_notes_mixed_link_syntax(self):
        """同一笔记库混用双链与标准链接时都能识别。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n", encoding="utf-8")
        (cat / "笔记B.md").write_text(
            "# 笔记B\n\n[[笔记A]]\n\n[笔记A](笔记A.md)\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A"), ("笔记B", "笔记B")])
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
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["missing_frontmatter"]), 1)
        self.assertEqual(result["missing_frontmatter"][0]["missing"], ["frontmatter"])

    def test_lint_notes_missing_frontmatter_fields(self):
        """frontmatter 存在但缺必填字段时，列出缺哪些。"""
        t.save_config({"format": "obsidian"})
        root, cat = self._make_root()
        self._obsidian_note(cat, "笔记A.md", "# 笔记A\n",
                            fm="tags: [测试]\ncreated: 2026-01-01")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["missing_frontmatter"][0]["missing"], ["source"])

    def test_lint_notes_frontmatter_skipped_for_plain_markdown(self):
        """普通 Markdown 无 frontmatter 要求，不应误报。"""
        t.save_config({"format": "markdown"})
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n正文\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["missing_frontmatter"], [])

    def test_lint_notes_frontmatter_skipped_without_config(self):
        """未配置（setUp 状态）时不做 frontmatter 检查，避免误报。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n正文\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["missing_frontmatter"], [])

    def test_lint_notes_detects_empty_section(self):
        """有标题无正文的章节应被报出。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n## 空章节\n\n## 有内容\n\n正文\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual([e["section"] for e in result["empty_sections"]], ["空章节"])

    def test_lint_notes_empty_section_ignores_code_block(self):
        """代码块内的 # 行不算标题，且章节里有代码就不算空。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n## 章节\n\n```\n# 不是标题\n```\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["empty_sections"], [])

    def test_lint_notes_parent_section_with_subheading_not_empty(self):
        """父章节下紧跟子标题时不算空（子标题行本身就是内容）。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n## 父章节\n\n### 子章节\n\n正文\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual(result["empty_sections"], [])

    def test_lint_notes_empty_subsection_reported(self):
        """父章节有子标题、子标题下无正文时，只报子章节为空。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n## 父章节\n\n### 空子章节\n\n## 有内容\n\n正文\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        result = t.lint_notes(str(root))
        self.assertEqual([e["section"] for e in result["empty_sections"]], ["空子章节"])

    def test_lint_notes_detects_stale_index(self):
        """笔记比索引新 -> stale_index。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n正文\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        old = time.time() - 100
        os.utime(cat / "00-分类索引.md", (old, old))
        result = t.lint_notes(str(root))
        self.assertEqual(len(result["stale_index"]), 1)
        self.assertEqual(result["stale_index"][0]["note"], "笔记A.md")

    def test_lint_notes_stale_index_ignored_for_unindexed(self):
        """未被索引收录的笔记不参与索引时效检查。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text("# 笔记A\n\n正文\n", encoding="utf-8")
        (cat / "笔记B.md").write_text("# 笔记B\n\n正文\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A")])
        old = time.time() - 100
        os.utime(cat / "00-分类索引.md", (old, old))
        result = t.lint_notes(str(root))
        self.assertEqual([s["note"] for s in result["stale_index"]], ["笔记A.md"])

    def test_lint_notes_summary_groups_and_total(self):
        """summary 给出结构/内容分组计数，且总数为两者之和。"""
        root, cat = self._make_root()
        (cat / "笔记A.md").write_text(
            "# 笔记A\n\n## 空章节\n\n## 有内容\n\n见 [[缺失笔记]]\n", encoding="utf-8")
        self._write_index(cat, [("笔记A", "笔记A"), ("已删笔记", "已删笔记")])
        result = t.lint_notes(str(root))
        summary = result["summary"]
        self.assertEqual(summary["issues"],
                         summary["structure_issues"] + summary["content_issues"])
        self.assertEqual(summary["content_issues"], 1)
        self.assertEqual(summary["structure_issues"], 2)

    # ------------------------------------------------------------ 内容地图（MOC）
    def _make_moc_lib(self):
        """建一个含两个空分类的笔记根目录，返回 (root, 分类A, 分类B)。"""
        root = self.sandbox / "AI笔记"
        a = root / "分类A"
        b = root / "分类B"
        a.mkdir(parents=True)
        b.mkdir(parents=True)
        return root, a, b

    def test_generate_moc_by_tag_cross_category(self):
        """按标签跨分类聚合，产出根目录 MOC-<主题>.md。"""
        root, a, b = self._make_moc_lib()
        self._obsidian_note(a, "共识算法.md", "# 共识算法\n\n正文\n",
                            fm="tags: [分布式]\ncreated: 2026-01-01\nsource: 对话总结")
        self._obsidian_note(b, "存储选型.md", "# 存储选型\n\n正文\n",
                            fm="tags: [分布式]\ncreated: 2026-01-01\nsource: 对话总结")
        self._obsidian_note(a, "无关笔记.md", "# 无关\n\n正文\n",
                            fm="tags: [其它]\ncreated: 2026-01-01\nsource: 对话总结")
        result = t.generate_moc(str(root), "分布式", tag="分布式")
        self.assertTrue(result["ok"])
        self.assertEqual(result["matched_notes"], 2)
        moc = root / "MOC-分布式.md"
        self.assertTrue(moc.exists())
        content = moc.read_text(encoding="utf-8")
        self.assertIn("[[共识算法]]", content)
        self.assertIn("[[存储选型]]", content)
        self.assertNotIn("无关笔记", content)
        self.assertEqual([g["category"] for g in result["groups"]], ["分类A", "分类B"])

    def test_generate_moc_by_keyword_in_body(self):
        """未给标签时按关键词在正文中命中。"""
        root, a, b = self._make_moc_lib()
        (a / "笔记X.md").write_text("# 笔记X\n\n讨论了分布式事务。\n", encoding="utf-8")
        (b / "笔记Y.md").write_text("# 笔记Y\n\n别的内容。\n", encoding="utf-8")
        result = t.generate_moc(str(root), "分布式")
        self.assertEqual(result["matched_notes"], 1)
        self.assertIn("[[笔记X]]", (root / "MOC-分布式.md").read_text(encoding="utf-8"))

    def test_generate_moc_no_match_still_writes_note(self):
        """无命中时仍生成文件，并注明暂无匹配笔记。"""
        root, a, b = self._make_moc_lib()
        (a / "笔记X.md").write_text("# 笔记X\n\n内容\n", encoding="utf-8")
        result = t.generate_moc(str(root), "不存在的主题")
        self.assertTrue(result["ok"])
        self.assertEqual(result["matched_notes"], 0)
        content = (root / "MOC-不存在的主题.md").read_text(encoding="utf-8")
        self.assertIn("暂无匹配笔记", content)

    def test_generate_moc_excludes_index_file(self):
        """分类索引文件不参与聚合，即使其内容命中关键词。"""
        root, a, b = self._make_moc_lib()
        (a / "00-分类索引.md").write_text(
            "# 索引\n\n## 笔记导航\n\n分布式\n", encoding="utf-8")
        result = t.generate_moc(str(root), "分布式")
        self.assertEqual(result["matched_notes"], 0)

    def test_generate_moc_category_filter(self):
        """--category 限定只聚合该分类。"""
        root, a, b = self._make_moc_lib()
        (a / "笔记X.md").write_text("# 笔记X\n\n分布式\n", encoding="utf-8")
        (b / "笔记Y.md").write_text("# 笔记Y\n\n分布式\n", encoding="utf-8")
        result = t.generate_moc(str(root), "分布式", category="分类A")
        self.assertEqual(result["matched_notes"], 1)
        self.assertEqual(result["groups"][0]["category"], "分类A")

    def test_generate_moc_missing_category_fails(self):
        """指定不存在的分类应失败。"""
        root, a, b = self._make_moc_lib()
        result = t.generate_moc(str(root), "分布式", category="不存在的分类")
        self.assertFalse(result["ok"])

    def test_generate_moc_missing_root_fails(self):
        """笔记根目录不存在应失败。"""
        result = t.generate_moc(str(self.sandbox / "没有这个目录"), "主题")
        self.assertFalse(result["ok"])

    def test_generate_moc_description_override(self):
        """自定义说明文字写入页面。"""
        root, a, b = self._make_moc_lib()
        (a / "笔记X.md").write_text("# 笔记X\n\n分布式\n", encoding="utf-8")
        t.generate_moc(str(root), "分布式", description="自定义说明ABC")
        self.assertIn("自定义说明ABC",
                      (root / "MOC-分布式.md").read_text(encoding="utf-8"))

    def test_generate_moc_refresh_idempotent_then_backs_up(self):
        """内容不变时刷新返回 unchanged；新增匹配笔记后覆盖并备份。"""
        root, a, b = self._make_moc_lib()
        (a / "笔记X.md").write_text("# 笔记X\n\n分布式\n", encoding="utf-8")
        first = t.generate_moc(str(root), "分布式")
        self.assertEqual(first["action"], "created")
        again = t.generate_moc(str(root), "分布式")
        self.assertEqual(again["action"], "unchanged")
        (b / "笔记Y.md").write_text("# 笔记Y\n\n分布式\n", encoding="utf-8")
        third = t.generate_moc(str(root), "分布式")
        self.assertEqual(third["action"], "overwritten")
        self.assertTrue(third["backup"])

    # ------------------------------------------------------------ 全文检索
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
        """表格场景转义竖线；列表场景（MOC）保留竖线（双链别名语义）。"""
        self.assertEqual(t.render_note_link("含|竖线", "obsidian"), "[[含\\|竖线]]")
        self.assertEqual(t.render_note_link("含|竖线", "obsidian", table_safe=False),
                         "[[含|竖线]]")

    # ------------------------------------------------------------ MOC 摘要提取
    def test_note_summary_prefers_quote_over_paragraph(self):
        """开头概述引用优先于正文段落（技能生成笔记的固定结构）。"""
        body = ("# 标题\n\n> 本篇记录技能的完整设计过程。\n\n## 一、章节\n\n"
                "- 列表项\n\n某段正文说明。\n")
        self.assertEqual(t._note_summary(body), "本篇记录技能的完整设计过程。")

    def test_note_summary_uses_paragraph_without_quote(self):
        """没有可用引用时取普通段落，不取标题或列表项。"""
        body = "# 标题\n\n## 章节\n\n- 列表项一\n- 列表项二\n\n这是正文段落。\n"
        self.assertEqual(t._note_summary(body), "这是正文段落。")

    def test_note_summary_skips_callout_and_meta_quote(self):
        """callout 标记行与"创建/来源"元信息行不作为摘要。"""
        body = "# 标题\n\n> [!note] 提示\n> 创建：2026-01-01　来源：对话总结\n\n正文段落。\n"
        self.assertEqual(t._note_summary(body), "正文段落。")

    def test_note_summary_skips_code_block(self):
        """代码块内容不作为摘要。"""
        body = "# 标题\n\n```python\nprint('x')\n```\n\n真正的正文。\n"
        self.assertEqual(t._note_summary(body), "真正的正文。")

    def test_note_summary_empty_when_nothing_usable(self):
        """只有标题与列表时返回空，不硬凑。"""
        self.assertEqual(t._note_summary("# 标题\n\n- 列表项\n"), "")

    def test_note_summary_clips_at_punctuation(self):
        """超长摘要在标点处收尾。"""
        body = "第一句话很短。第二句话也不长。\n"
        self.assertEqual(t._note_summary(body, limit=8), "第一句话很短。")

    def test_generate_moc_uses_sentence_summary(self):
        """生成的 MOC 里摘要应来自正文句子，而非列表项。"""
        root, a, b = self._make_moc_lib()
        (a / "笔记X.md").write_text(
            "# 笔记X\n\n## 章节\n\n- 列表项一\n\n分布式事务的正文说明。\n", encoding="utf-8")
        t.generate_moc(str(root), "分布式", keyword="分布式")
        content = (root / "MOC-分布式.md").read_text(encoding="utf-8")
        self.assertIn("分布式事务的正文说明。", content)
        self.assertNotIn("列表项一", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
