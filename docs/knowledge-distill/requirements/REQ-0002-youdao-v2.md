---
id: REQ-0002
title: 有道后端 v2（lint-notes；MOC 移除）
skill: knowledge-distill
status: done
created: 2026-09-16
updated: 2026-09-16
related: [REQ-0001]
---

# REQ-0002 有道后端 v2（lint-notes；MOC 移除）

## 问题与目标

有道后端 v1 已完成"写入闭环"（首次配置 / 保存 / 合并 / 索引 / 命名查重，以及检索与回退），但 `lint-notes`（健康检查）在有道下**直接报"暂不支持"**——用户在有道下无法体检笔记库。目标：补齐 `lint-notes`（受有道能力限制，带降级）。

同时**移除 MOC（`gen-moc`）**：REQ-0001 落地后根目录已有 `总目录.md`（全库分类 → 笔记 + 摘要），MOC 的"跨分类聚主题"在"分类≈主题"的库里与总目录重叠（且已被判断为鸡肋），保留两套近似导航只会增加维护与触发噪音。

## 触发与分支

- "检查笔记库 / 有没有断链 / 整理一下笔记库" →「健康检查」（有道下现报错，本次补齐）。
- "给 X 做个知识地图 / MOC" → **不再有该分支**（MOC 移除）。

## 行为与步骤

**lint-notes（有道）**——只做确定性检查：

- 可做：`index_orphans`（总目录收录但笔记不存在）、`unindexed_notes`（笔记未被总目录收录）、`question_orphans`（疑问链接指向不存在的笔记）、`empty_sections`（空章节）。
- 做不了（有道无对应能力）：`stale_index`（**无笔记时间戳**）、`missing_frontmatter`（无 frontmatter）、`orphan_notes` / `broken_links`（**无反链 API**，链接为纯文本）。输出用 `not_checked` 字段**如实列出**这四类，不误报。

**MOC 移除**：删除 `gen-moc` 命令、`generate_moc`、`MOC_PREFIX`、`_note_summary`/`_clip_summary`、相关测试与文档；`description` 去掉 MOC 触发。

## 脚本与资源

- `skill_tools.py`：新增 `youdao_lint_notes(note_root)`；`main()` 的 `lint-notes` 按后端分派；删除 MOC 相关代码与 `gen-moc` 命令。
- `references/youdao-best-practices.md`：能力表——lint 改为"支持部分（含降级说明）"，删除 MOC 行。
- `references/design-boundaries.md`：更新降级描述（lint 已支持、MOC 已移除）。
- `SKILL.md`：删除「生成内容地图（MOC）」一节与 MOC 触发；健康检查一节说明有道降级。
- `README.md`：删除 MOC 提及。

## 降级与边界

- lint 只覆盖"可确定性检查"的子集（见上），输出中如实标注未检查项。
- 依赖 REQ-0001 的索引结构（总目录 / 疑问）。

## 验收标准

- [x] 有道下 `lint-notes` 返回 `index_orphans` / `unindexed_notes` / `question_orphans` / `empty_sections`，且不因"无时间戳 / 无 frontmatter / 无反链"而报错或误报（未检查项在 `not_checked` 列出）。
- [x] MOC（`gen-moc` / `generate_moc` / MOC 文档与触发）已从技能移除。
- [x] mock 单测覆盖（`test_youdao_lint_notes` 等，不依赖真实账号）。

## 范围外

- 不补有道没有的能力（标签、反链、时间戳）。
- 不改本地（Obsidian / Markdown）的 lint 行为。

## 备注 / 待办

- **已实现**（2026-09-16）：`youdao_lint_notes` + 分派、MOC 全量移除、文档同步；170 测试全绿。
- `_youdao_id` / `_youdao_entries` 等防御式解析需真实 API Key 实测后收紧。
