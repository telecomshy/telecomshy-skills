---
id: REQ-0004
title: 判断技能该分几层的完整方案（架构文档 + 路由表 + 命名约定）
skill: shy-skill-suite
status: deferred
kind: feature
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
defer_reason: 决策频率低、纯文档，易成无人读的文档；先用轻量版 REQ-0003 覆盖日常判断，待真正需要（出现多技能 / 子技能拆分需求）时再补全。
related: [REQ-0003]
---

# REQ-0004 判断技能该分几层的完整方案（架构文档 + 路由表 + 命名约定）

## 问题与目标

完整记录"架构分层"应包含的内容，供未来需要时实现。当前**延后**（见 `defer_reason`），日常判断由 `REQ-0003` 的轻量版覆盖。

## 触发与分支

- 当套件真的长到需要 Tier 3/4（多技能 / 子技能）时。
- 用户说"要拆套件 / 设计子技能架构"。

## 行为与步骤（未来实现）

1. 新增 `references/architecture.md`，含 **Tier 1–4 判定信号表**（Tier 1 单 `SKILL.md`；Tier 2 +`scripts/`/`references/`；Tier 3 orchestrator + 子技能；Tier 4 +`agents/` 或需发布）。
2. 升级信号 + 反向判据（带反例）。
3. Tier 3+ 的**路由表**格式与**子技能命名**约定（`<parent>-<function>`，kebab-case）。
4. 与 REQ 拆分联动：跨 Tier 改动拆成多个 REQ + `blocked_by`。
5. `lifecycle.md` 阶段 1 指向 `architecture.md`；`SKILL.md` 资源同步。

## 脚本与资源

- 新增 `references/architecture.md`（纯文档）。
- 可选：Tier 判定脚本（待观察是否真需要）。

## 降级与边界

- 设计期指导，非强制；不自动重构、不跨平台转换。

## 验收标准（未来）

- [ ] `references/architecture.md` 含 Tier 1–4 判定信号表。
- [ ] 含"何时拆子技能"与"何时别拆"两组判据（后者带反例）。
- [ ] Tier 3+ 有路由表格式与子技能命名约定。
- [ ] `lifecycle.md` 阶段 1 有指向 `architecture.md` 的指针。

## 范围外

- 自动重构、跨平台转换、发布。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 记录完整版需求；延后（见 `defer_reason`） | — | 延后 |

## 备注 / 待办

- 恢复时：`status: deferred → ready`，并在迭代记录记一句。
