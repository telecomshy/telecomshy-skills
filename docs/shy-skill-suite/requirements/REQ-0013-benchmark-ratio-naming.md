---
id: REQ-0013
title: benchmark 比率字段命名修正（token/time savings 语义反向）
skill: shy-skill-suite
status: ready
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: []
---

# REQ-0013 benchmark 比率字段命名修正（token/time savings 语义反向）

## 问题与目标

复审（2026-09-16，标准轴 P2）：`aggregate_benchmark.py` 产出两个名字与语义**相反**的字段。

- 证据（读源码）：`token_savings_ratio = round(with_tokens / base_tokens, 2)`、`time_savings_ratio = round(with_dur / base_dur, 2)`。
  这是 **with / baseline** 的比值：`1.3` 表示带技能**多花** 30% token，而不是"省了 30%"。
- 放大效应：`benchmark.md` 的表头只写 `Ratio`，读者看到 `1.3x` 极易读反。

目标：字段名与数值方向一致，读报告不再需要反推。

## 触发与分支

- 复审 Step 8 读 `benchmark.json` / `benchmark.md` 做汇总裁决时。
- 用户说"这个 benchmark 数字怎么读 / 1.3x 是省了还是多了"。

## 行为与步骤

1. 二选一（实现轮次决定，倾向 A）：
   - **A（改名不改算法）**：`token_savings_ratio` → `token_ratio`、`time_savings_ratio` → `time_ratio`；`benchmark.md` 表头 `Ratio` → `With/Baseline`。
   - **B（改算法不改名）**：改为 `base / with`（>1 才表示省），并在 `benchmark.md` 表头写清 `Savings`。
2. 无论选哪个，`benchmark.md` 的表头都要能自解释（不出现裸 `Ratio`）。
3. 保持 `improvement_ratio`（通过率 with/baseline）不变——它命名与方向本来就一致。

## 脚本与资源

- 只改 `scripts/aggregate_benchmark.py`（字段名或算法 + `benchmark.md` 表头）。
- 不改 `references/`、不改其它脚本。

## 降级与边界

- 改字段名是**破坏性变更**（下游若已按旧名解析会失效）。当前仓库内没有消费方，且技能尚未对外发布，故按 A 处理；若发现消费方，改用"新增 `token_ratio` 并保留旧名一版"的 expand–contract（见 `lifecycle.md` 阶段 1）。

## 验收标准

- [ ] `benchmark.json` 的 summary 中不再有语义反向的 `*_savings_ratio` 字段（或该字段方向已与名字一致）。
- [ ] `benchmark.md` 的 token / time 行表头不再是裸 `Ratio`，读者无需反推方向。
- [ ] 构造一组 with 比 baseline 多花 token 的假数据 → 报告里的数值 > 1 且表头语义与之一致。
- [ ] `improvement_ratio`（通过率）行为不变。
- [ ] 对同一份假数据，脚本输出仍为合法 JSON、退出码 0。

## 范围外

- 不改评测流程、不改工作区布局、不改其它指标（通过率 / 方差 / 回归比较）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（复审 P2），未实施 | — | 待开工 |

## 备注 / 待办

- 来源：2026-09-16 复审报告，标准轴 P2。
