---
id: REQ-0070
title: 校验器放行 TeleAgent 扩展字段 + 修代码示例误报
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-19
updated: 2026-09-19
blocked_by: []
related: [REQ-0002, REQ-0011]
---

# REQ-0070 校验器放行 TeleAgent 扩展字段 + 修代码示例误报

## 问题与目标

2026-09-19 复审 `knowledge-distill`（标准轴 P1）实测两处让 Gate 常红：

1. 该技能 frontmatter 顶层使用 TeleAgent 客户端字段 `name_cn` / `description_cn` / `create_source`，而 `validate_skill.py` 把它们判为"多余字段"、退出码 1。技能会被复制到 `~/.config/TeleAgent/skills/` 部署（TeleAgent 是本仓库的部署目标），照现状**实现路的 Gate 永远红**。
2. `validate_skill.py` 的引用检查把**代码示例里的链接**当成真引用：行内代码（如 `` `[标题](标题.md)` ``）与围栏内示例（`plain-markdown-best-practices.md`）被误报"悬空引用"，同样让 Gate 红。

目标：放行 TeleAgent 扩展字段，并让引用检查跳过代码（围栏 + 行内），使技能文档里的链接示例不再误报；同时保持"未列入字段仍报错""真悬空引用仍报错"的收紧语义。

## 触发与分支

- `lifecycle.md` 阶段 2 收尾、阶段 3 之前跑 `validate_skill.py` 时。
- 校验任何使用 TeleAgent 客户端字段的 `SKILL.md` 时。

## 行为与步骤

1. `scripts/validate_skill.py` 的 `EXTENSION_FIELDS` 追加 `name_cn`、`description_cn`、`create_source`；同步模块 docstring 的允许集说明。
2. `scripts/validate_skill.py` 的引用检查改为先 `strip_code()`：按行开关去围栏代码块（容忍行内出现的 ```）、逐行去行内代码，再匹配链接。
3. `scripts/run_checks.py` 的 `validate-rejects-bad` 夹具由 `name_cn: 坏` 改为中性未知字段 `bogus_field: 坏`，保持"未知字段被拒"的断言有效。
4. 订正受影响的旧 REQ 契约文本：`REQ-0002`（行为与步骤的示例、验收标准、备注）、`REQ-0011`（`EXTENSION_FIELDS` 定义、验收标准）。
5. 不改字段取值校验（沿用"只查结构与规范"的定位）。

## 脚本与资源

- 改 `scripts/validate_skill.py`、`scripts/run_checks.py`。
- 改 `docs/shy-skill-suite/requirements/REQ-0002-skill-validator.md`、`REQ-0011-invocation-lever-and-validator-fields.md`。

## 降级与边界

- 只放行这三个 TeleAgent 字段；不引入任意未知字段的放行。
- `BASE_FIELDS` 仍对齐 `agentskills.io` 基础集，不收紧也不额外放宽。
- 不校验这些字段的取值合法性。

## 验收标准

- [x] `validate_skill.py` 对 `skills/knowledge-distill` → `status: ok`、退出码 0（`name_cn` / `description_cn` / `create_source` 不再报"多余字段"）。 — （语义）判定：跑 `python "<SKILL_DIR>/scripts/validate_skill.py" skills/knowledge-distill` 看 `status`
- [x] `validate_skill.py` 对 `skills/shy-skill-suite` → `status: ok`、退出码 0（回归）。 — `check:skill-validate-ok`
- [x] `validate_skill.py` 对含未知字段（`bogus_field`）的技能仍报"多余字段"、退出码 1。 — `check:validate-rejects-bad`
- [x] `validate_skill.py` 不再把代码示例里的链接报成悬空引用：对 `skills/knowledge-distill` → `status: ok`（此前 10 条误报，含行内代码与围栏示例）。 — （语义）判定：跑 `validate_skill.py skills/knowledge-distill` 看 `errors` 为空
- [x] `validate_skill.py` 对**真**悬空引用仍报错（如 `references/nope.md`）。 — （语义）判定：临时造一个引用不存在文件的技能跑校验，看 `errors` 非空
- [x] `validate_skill.py` 源码 `EXTENSION_FIELDS` 含 `name_cn` / `description_cn` / `create_source`。 — （语义）
- [x] 受影响的旧 REQ（`REQ-0002` / `REQ-0011`）验收与示例已当轮订正，无残留"`name_cn` 应被拒"的过期文字。 — （语义）

## 范围外

- 不校验扩展字段取值；不改其它校验规则；不做跨平台字段转换。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-19 | `EXTENSION_FIELDS` 加 TeleAgent 字段；引用检查加 `strip_code()`（围栏+行内）；`validate-rejects-bad` 夹具改 `bogus_field`；订正 `REQ-0002`/`REQ-0011` 过期契约 | `validate_skill.py skills/knowledge-distill` → `status: ok`（此前 10 条误报全消）；`skills/shy-skill-suite` → ok；`run_checks.py` 相关 check 绿 | 收敛（done） |

## 备注 / 待办

- 来源：2026-09-19 `knowledge-distill` 复审报告，标准轴 P1。
- 逼问：跳过（依据：复审 finding 自带问题与目标 / 范围外 / 验收，改动机械且无真实分叉）。
