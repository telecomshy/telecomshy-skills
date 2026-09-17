---
id: REQ-0037
title: 跨客户端分发（.agents/skills 约定）与平台差异矩阵
skill: shy-skill-suite
status: deferred
iteration: 1
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0011, REQ-0020, REQ-0036]
defer_reason: 技能当前只面向 opencode / TeleAgent；是否扩到 Claude Code / Codex 是路线选择，未决。等确定要跨客户端发布再开。
---

# REQ-0037 跨客户端分发（.agents/skills 约定）与平台差异矩阵

> **状态：deferred（暂不做）。** 本条只是把调研结论落盘，避免遗忘；不在 frontier、不算 done。

## 问题与目标

一手来源（`agentskills.io/client-implementation/adding-skills-support`）指出 `.agents/skills/` 是"跨客户端技能共享的广泛采用约定"；同时各客户端认领的 frontmatter 字段不同（开放标准 6 个基础字段、Claude Code 追加约 13 个扩展且 `description` 列表截断于 1536 字符、opencode 只认 5 个、Codex 另有 `agents/openai.yaml` 与 `metadata.short-description`）。

shy 现状（证伪结果）：全技能 grep `Codex|when_to_use|1536|context: fork` → **0**；`.agents/skills` 仅出现在 `validate_skill.py:159` 的 `--help` 示例里，**不是部署约定**。`writing-skills.md` 只写了 opencode 一条路线。

> 来源：`docs/shy-skill-suite/research/skill-development-best-practices.md` §6.1 候选 C/D、§4 分歧 2。

目标（待启动时）：给出**平台差异矩阵**（标准 / Claude Code / opencode / Codex 各自认领的字段与限制），并决定是否采用 `.agents/skills/` 作为跨客户端部署路径。

## 触发与分支

- 用户说"部署到别的客户端 / Claude Code / Codex 也能用吗 / 跨客户端"。
- 写 `description` 或 frontmatter、需判断某字段是否可移植时。

## 行为与步骤

（待启动时细化）

1. 在 `references/writing-skills.md`（或新增 `references/platforms.md`）落一份**平台差异矩阵**：认领字段、长度限制、触发机制（模型判断 vs 词法选择器）、部署路径。
2. 决定并记录 `.agents/skills/` 是否纳入部署说明。
3. 若扩平台：给出各平台的降级路径（如不认 `disable-model-invocation` 时怎么办）。

## 脚本与资源

（待启动时确定）

## 降级与边界

- **不做**跨平台自动转换器（skill-forge `convert_skill.py` 那类）——先只做"写清楚差异"。
- 不改变 opencode / TeleAgent 的主路径。

## 验收标准

（待启动时按 `writing-requirements.md` §4 逐条写成可执行检查；当前为草稿，故未标 `check:`。）

- [ ] 平台差异矩阵覆盖标准 / Claude Code / opencode / Codex，每个字段有出处。
- [ ] `writing-skills.md` 指向该矩阵，且 opencode 路线不被破坏。
- [ ] 若采纳 `.agents/skills`，部署说明含该路径；不采纳则写明理由。

## 范围外

- 自动跨平台转换器（skill-forge 的 `convert`）。
- 各平台专属机制（hooks / `context: fork` 等）的落地实现。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落盘（deferred）：记录跨客户端分发候选与"平台差异矩阵"缺口 | 全技能 grep `Codex\|when_to_use\|1536` → 0 | 暂不做 |

## 备注 / 待办

- 恢复条件：确定要跨客户端发布，或有人反馈"在某客户端不生效"。
- 参考：`agentskills.io/specification`、`code.claude.com/docs/en/skills`、`opencode.ai/docs/skills/`、`openai/codex` 源码。
- 与 `REQ-0036` 的关系：打包（0036）与分发路径（0037）相邻但独立；本 REQ 不依赖它。
