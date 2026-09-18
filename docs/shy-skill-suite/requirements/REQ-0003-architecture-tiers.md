---
id: REQ-0003
title: 架构分层判据（轻量版）
skill: shy-skill-suite
status: done
kind: feature
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: [REQ-0004]
---

# REQ-0003 架构分层判据（轻量版）

## 问题与目标

设计期需要一个"技能要不要拆成套件"的判据；但完整版（独立 `architecture.md` + 路由表 + 命名约定 + Tier 脚本）决策频率低、纯文档，有变成"没人读的文档"（sediment）的风险。故只做**轻量版**：在 `lifecycle.md` 阶段 1 加一小段判据（3–5 行 + 正/反例）。完整版记录为 `REQ-0004`（deferred）。

## 触发与分支

- `lifecycle.md` 阶段 1「落需求」评估改动规模时。
- 用户问"这技能该拆成几个 / 要不要做套件"。

## 行为与步骤

1. 在 `lifecycle.md` 阶段 1 增一小节"要不要拆成套件？"，含：
   - **升级信号**（满足其一才升 Tier 3/4）：子流程有**独立触发词**、需要并行或子 agent、需要对外发布。
   - **反向判据**：没人手动调用、无独立触发、一个上下文窗口装得下 → 停在 Tier 1/2。
   - 一个**正例**与一个**反例**。
2. 不改动其它文件（技能内不引用仓库 `docs/`）。

## 脚本与资源

- 只改 `references/lifecycle.md`；无脚本。

## 降级与边界

- 是判据，不是强制；小技能不因"看起来专业"而分层。

## 验收标准

- [x] `lifecycle.md` 阶段 1 含"要不要拆成套件？"小节。 — （episode）
- [x] 含"升级信号"与"反向判据"两组。 — （episode）
- [x] 含至少一个正例与一个反例。 — （episode）
- [x] 未新增 `architecture.md`、未新增脚本。 — （episode）

## 范围外

- 独立 `architecture.md`、路由表格式、子技能命名约定、Tier 自动化脚本、自动重构 —— 见 `REQ-0004`（deferred）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（缩水版）；在 `lifecycle.md` 阶段 1 加"要不要拆成套件？"判据（升级信号 + 反向判据 + 正/反例） | 4/4 验收通过 | 收敛（done） |

## 备注 / 待办

- 完整版见 `REQ-0004-architecture-full.md`（`status: deferred`）。
