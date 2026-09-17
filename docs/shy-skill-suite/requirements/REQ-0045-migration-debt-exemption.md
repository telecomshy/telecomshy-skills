---
id: REQ-0045
title: Step 3 完成判据给存量 done REQ 的未标条目一个迁移债出口
skill: shy-skill-suite
status: done
iteration: 2
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0030, REQ-0042, REQ-0044]
---

# REQ-0045 Step 3 完成判据给存量 done REQ 的未标条目一个迁移债出口

## 问题与目标

全量复审（`iteration-2`）需求轴 P2：Step 3 的完成判据要求"**本轮 diff 触碰过的 REQ 无未标条目**"，但本轮触碰过的 5 份已 `done` REQ（0024、0026–0029）验收标准**全是散文**、一条都没标 `check:` / `（行为）` / `（语义）`——共 **47 条**。

这是**规则与操作对不上**：一边要求"碰过的必须无未标"，一边收敛这些 REQ 时没标类。结果要么判据名存实亡，要么每次复审报"不合规"却不能真去改（那又变成迁移补课循环）。

目标：给存量一个明确出口——**已 `done` 的存量 REQ 的未标条目计为「迁移债」，只报数、不阻断**；只有本轮**新写 / 改写**的 REQ 才要求无未标。迁移债随"改到哪批补哪批"递减，**不集中补课**。

## 触发与分支

- 复审 Step 3 需求轴完成判据。
- 用户说"存量 REQ 的未标怎么算 / 迁移债怎么办"。

## 行为与步骤

1. **`references/reviewing-skills.md` Step 3 完成判据**：把"本轮 diff 触碰过的 REQ 无未标条目"收窄为"**本轮新写 / 改写验收标准的 REQ 无未标**"；补一句"已 `done` 的存量 REQ 的未标 = **迁移债**，只报数、不阻断（`run_checks.py` 的 `untagged` 计数即其可见面）"。
2. **`scripts/run_checks.py`**：`untagged` 输出已有；如可行，区分"本轮触碰 REQ 的未标"与"全库存量未标"（可选）。
3. **`run_checks.py`**：注册本 REQ 检查。

## 脚本与资源

- 改 `references/reviewing-skills.md`（Step 3）、`scripts/run_checks.py`。
- 不改 `writing-requirements.md` 对**新** REQ 的"默认按三类标注"要求。

## 降级与边界

- **新 REQ 仍严格**：新写 / 改写的验收标准必须标三类之一（`check:` / `（行为）` / `（语义）`）。
- **存量宽容**：`done` 的旧 REQ 未标不阻断，但**可见**（`untagged` 数字）。
- 不自动改写历史 REQ 的验收标准。

## 验收标准

- [x] `reviewing-skills.md` Step 3 完成判据含"迁移债 / 只报数、不阻断"，且限定为"本轮新写 / 改写的 REQ" — `check:req0045-migration-debt`
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不批量给历史 REQ 补标（那是迁移补课，明确不做）。
- 不改 `untagged` 的定义。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落盘（全量复审 iteration-2 需求轴 P2） | 触碰的 done REQ 未标 47 条 | 待实施 |
| 2 | 2026-09-17 | **回写**：`reviewing-skills.md` Step 3 完成判据收窄为「本轮**新写 / 改写**的验收标准无未标」；存量 `done` REQ 的未标 = **迁移债，只报数、不阻断**；`lifecycle.md` 阶段 5 同步；`run_checks.py` 注册 1 条。 | `run_checks` 45 通过 / 0 失败；`validate` ok | **done** |

## 备注 / 待办

- 来源：`skills/shy-skill-suite-workspace/iteration-2/findings.json` 需求轴 P2。
- 与 `REQ-0030` 的关系：0030 建立三类标记与全量 Spec 扫；本 REQ 补"存量迁移债不阻断"的出口。