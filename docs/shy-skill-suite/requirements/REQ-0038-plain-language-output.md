---
id: REQ-0038
title: 让复审输出面向人：用白话解释并说明为什么
skill: shy-skill-suite
status: done
kind: docs
iteration: 1
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0018, REQ-0019, REQ-0024]
---

# REQ-0038 让复审输出面向人：用白话解释并说明为什么

## 问题与目标

复审的产物（`findings.json` / HTML 报告 / 对话里的结论）**是给人看的**，但现行报告格式只规定结构行：

```
[轴] [优先级] 位置(file:line) — 问题（附证据）→ 影响 → 建议改动 → 预期行为变化
```

术语与 `file:line` 对作者有用，对用户是噪音。用户诉求（2026-09-17）：**用白话解释结论与优化建议，并说清"为什么"**。缺口（证伪：`reviewing-skills.md` grep `白话|说人话` → 0 命中）。

目标：把"面向人"写成硬规则——每条 finding / 建议除结构行外，必须用白话讲清 **① 不修会出什么问题 ② 为什么这么改**。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 8 的汇报与报告呈现。
- 用户说"看不懂 / 请用白话解释 / 为什么这么改"。

## 行为与步骤

1. **`references/reviewing-skills.md` Step 8**：加「说人话 + 说 why（报告是给人看的）」规则——`problem` / `impact` / `suggestion` 三字段都要写成能直接念给用户听的话；不许只给术语、`file:line` 或"建议优化"。
2. **`SKILL.md` 共用原则**：加一条「输出面向人」，指向 Step 8。

## 脚本与资源

- 改 `references/reviewing-skills.md`（Step 8）、`SKILL.md`（共用原则）。
- 改 `scripts/run_checks.py`（注册 `req0038-plain-language`）。
- 不改 `render_report.py`（它渲染 `problem`/`impact`/`suggestion`，字段含量决定可读性）。

## 降级与边界

- 这是**表达要求**，不改变 finding 的判定与优先级；不要求把技术细节删掉，只要求**同时**给出白话与 why。
- 无 `findings.json` 的纯评测报告（只有数字）不适用。

## 验收标准

- [ ] `reviewing-skills.md` Step 8 含「说人话 / 说 why / 白话」规则 — （episode）
- [ ] `SKILL.md` 共用原则含「输出面向人」 — （episode）
- [ ] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不改 findings 的 schema 字段（仍用 `problem` / `impact` / `suggestion`）。
- 不做多语言化 / 语气风格库。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求并实施：Step 8 加「说人话 + 说 why」；`SKILL.md` 共用原则加「输出面向人」；`run_checks.py` 注册 `req0038-plain-language` | `run_checks.py` 全绿 | done |

## 备注 / 待办

- 来源：2026-09-17 用户诉求（"审核结果的解释与优化建议是给人看的，要白话 + 说 why"）。
- 与 `REQ-0019` 的关系：报告载体（HTML）不变，本 REQ 管**文字内容**。
