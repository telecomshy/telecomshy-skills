---
id: REQ-0006
title: 无 REQ 时的回溯补写与 grill 抽取
skill: shy-skill-suite
status: done
kind: feature
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: []
---

# REQ-0006 无 REQ 时的回溯补写与 grill 抽取

## 问题与目标

三个缺口：
1. **grill 只服务闭环**：逼问内嵌在 `lifecycle.md` 阶段 0，只有走"开发/迭代闭环"才被路由到；用户直接"复审既有技能 / 补 REQ"时够不着。
2. **无 REQ 的处理矛盾且有循环风险**：`reviewing-skills.md` Step 0 说"无需求文档则**先补一份**"（没说从哪补），Step 3 却说"标 `no spec available`"。若"补一份"是读技能反推，Spec 轴就成了橡皮图章。
3. **grill 缺三个动作**：术语规范化、场景压测、与实现交叉核对（`domain-modeling` 的招，技能比代码轻量，只吸收动作、不引入其文件结构）。

目标：抽 `references/grilling.md`；统一"无 REQ"决策；加"回溯补写"规范。

## 触发与分支

- 复审一个**既有技能但没有 REQ**。
- 用户说"逼问 / 拷问这个技能该做什么 / 给这个技能补需求"。

## 行为与步骤

1. 新增 `references/grilling.md`：机制（设计树 + frontier + 每问带建议答案 + 事实自己查）、技能领域 6 问、**三动作**（术语规范化 / 场景压测 / 与实现交叉核对）、完成判据、可跳过规则、**回溯补写**（从意图、不从实现）。
2. `lifecycle.md` 阶段 0 改为**引用** `grilling.md`（正文不重复）。
3. `reviewing-skills.md` **Step 0** 改为决策：
   - 有 REQ → 直接用；
   - 无 REQ → 问用户能否说清意图：能 → 按 `grilling.md` **从意图**问出来，落一份**回溯补写**的 REQ，再复审；不能 → 记 `no spec available`；
   - **禁止读技能反推 REQ**（循环论证、橡皮图章）。
   **Step 3** 对齐：无 REQ 且未回溯补写 → 标 `no spec available`、跳过本轴（可降级做 `description` ↔ 实现的自洽检查并标注为降级）。
4. `writing-requirements.md`：加"可回溯补写"（从意图、frontmatter 标 `retroactive: true`）。
5. `SKILL.md`：资源列表加 `grilling.md`；路由加"逼问需求"入口。

## 脚本与资源

- 新增 `references/grilling.md`（纯文档）。
- 改 `references/lifecycle.md` / `reviewing-skills.md` / `writing-requirements.md` / `SKILL.md`。

## 降级与边界

- **不引入** `CONTEXT.md` / ADR 文件层（小套件过度工程；决策已由 REQ 承载）。
- 技能自包含：`grilling.md` 不引用仓库 `docs/`。
- 不新增脚本。

## 验收标准

- [x] `references/grilling.md` 含：机制 / 6 问 / 三动作 / 完成判据 / 可跳过 / 回溯补写。 — （episode）
- [x] `lifecycle.md` 阶段 0 引用 `grilling.md`，不再重复其正文。 — （episode）
- [x] `reviewing-skills.md` Step 0 给出"有 / 无 REQ"决策，且与 Step 3 不矛盾。 — （episode）
- [x] 明写"禁止读技能反推 REQ"。 — （episode）
- [x] `writing-requirements.md` 含"回溯补写"（从意图、`retroactive: true`）。 — （episode）
- [x] `SKILL.md` 资源列出 `grilling.md`，路由含逼问入口。 — （episode）
- [x] 自包含：`grilling.md` 不引用仓库 `docs/`。 — （episode）

## 范围外

- 不引入 `domain-modeling` 的 `CONTEXT.md` / ADR；不新增脚本；不做跨平台。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求 + 实现：抽 `references/grilling.md`（含三动作）；`lifecycle` 阶段 0 改为引用；`reviewing-skills` Step 0/3 统一"无 REQ"决策并禁止反推；`writing-requirements` 加回溯补写 + `retroactive`；`SKILL.md` 资源与路由同步 | 7/7 验收通过 | 收敛（done） |

## 备注 / 待办

- 参考：mattpocock 的 `grilling`（机制）与 `domain-modeling`（三动作）；`grill-with-docs` = 两者组合，我们**只吸收动作**。
