---
id: REQ-0002
title: 有道后端 v2（lint-notes + gen-moc）
skill: knowledge-distill
status: ready
created: 2026-09-16
updated: 2026-09-16
related: [REQ-0001]
---

# REQ-0002 有道后端 v2（lint-notes + gen-moc）

## 问题与目标

有道后端 v1 已完成"写入闭环"（首次配置 / 保存 / 合并 / 索引 / 命名查重，以及检索与回退），但 `lint-notes`（健康检查）与 `gen-moc`（内容地图）在有道下**直接报"暂不支持"**——用户在有道下无法体检笔记库、无法生成内容地图。目标：补齐这两项（受有道能力限制，带降级）。

## 触发与分支

- "检查笔记库 / 有没有断链 / 整理一下笔记库" →「健康检查」（有道下现报错）。
- "给 X 做个知识地图 / MOC / 聚拢散落笔记" →「生成内容地图（MOC）」（有道下现报错）。

## 行为与步骤

**lint-notes（有道）**——只做确定性检查：

- 可做：`index_orphans`（索引收录但笔记不存在）、`unindexed_notes`（笔记未收录）、`question_orphans`（疑问链接指向不存在的笔记）、`empty_sections`（空章节）。
- 做不了（有道无对应能力）：`stale_index`（**无笔记时间戳**）、`missing_frontmatter`（无 frontmatter）、`orphan_notes` / `broken_links`（**无反链 API**，链接为纯文本）。

**gen-moc（有道）**：

- 按关键词在标题 / 正文匹配，跨分类聚合成一篇 MOC 笔记，写到根目录（`MOC-<主题>.md`）。
- 降级：有道**无原生标签**，不能按 `--tag` 精确匹配，只能按关键词。

## 脚本与资源

- `skill_tools.py`：`main()` 移除对 `lint-notes` / `gen-moc` 的"有道不支持"拦截，改为分派到有道实现；新增 `youdao_lint_notes(note_root)`、`youdao_generate_moc(...)`。
- `references/youdao-best-practices.md`：更新「能力对照与降级」表（移除 "lint / MOC 暂不支持"）。
- `SKILL.md`：移除「健康检查」「生成内容地图（MOC）」两节的"有道下暂不支持"提示。

## 降级与边界

- lint 只覆盖"可确定性检查"的子集（见上），输出中如实标注"有道下不检查 X"。
- MOC 只按关键词匹配，无标签匹配。
- 依赖 REQ-0001 的索引结构（lint 的索引对齐检查、MOC 的聚合范围）。

## 验收标准

- [ ] 有道下 `lint-notes` 返回 `index_orphans` / `unindexed_notes` / `question_orphans` / `empty_sections`，且不因"无时间戳 / 无 frontmatter / 无反链"而报错或误报。
- [ ] 有道下 `gen-moc "<主题>"` 在根目录生成 `MOC-<主题>.md`，聚合命中笔记。
- [ ] 两项在有道下的降级在输出与文档中如实说明。
- [ ] mock 单测覆盖（不依赖真实账号）。

## 范围外

- 不补有道没有的能力（标签、反链、时间戳）。
- 不改本地（Obsidian / Markdown）的 lint / MOC 行为。

## 备注 / 待办

- 依赖 REQ-0001（索引结构）先落地或同步设计。
- `_youdao_id` / `_youdao_entries` 等防御式解析需真实 API Key 实测后收紧。
