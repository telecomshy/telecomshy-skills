---
id: REQ-0064
title: agent 模式下 --description 会静默失效，改成直接报错拒绝
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-19
updated: 2026-09-19
blocked_by: []
related: [REQ-0047, REQ-0063]
---

# REQ-0064 agent 模式下 --description 会静默失效，改成直接报错拒绝

## 问题与目标

2026-09-19 实测发现：`optimize_description.py --runner opencode --description "<候选>"` 的候选描述**根本不会生效**——`build_predictor` 在 agent 模式下只跑 `opencode run "{prompt}"`，描述由客户端加载；`--description` 只影响 heuristic 分支。工具却照常输出分数，**静默给出无意义的对照**（本轮的一次"候选批"因此白跑 16 分钟）。

目标：agent 模式下传入与现描述不同的 `--description` 时**显式报错**，提示先部署候选描述再跑（或改用 heuristic）；`--help` 写清该限制。

## 触发与分支

- `optimize_description.py` 的一切 agent 模式运行。
- 用户/agent 想比较两版 description。

## 行为与步骤

1. `scripts/optimize_description.py`：`runner != heuristic` 且 `--description` 与现描述不同 → 返回 `{"error": "agent 模式不读取 --description…"}`（退出码 1）。
2. `--help` 与脚本示例标注：候选描述仅 heuristic 生效；agent 模式要先部署。
3. 不改评分口径与 heuristic 行为。

## 脚本与资源

- 改 `scripts/optimize_description.py`。

## 降级与边界

- 相同描述的 `--description`（等于现文）不报错（等价于没传）。
- agent 模式的候选对照流程 = 临时部署描述 → 跑 → 对比 → 回退（写在 `REQ-0047` 的迭代记录里）。

## 验收标准

- [x] agent 模式 + 不同 `--description` → 非 0 且错误信息可行动；相同描述不报错 — （语义）实测 rc=1 + 可行动错误
- [x] `--help` 写明该限制 — （语义）已落
- [x] `validate_skill` / `run_checks` / `selftest` 仍全绿 — `check:skill-validate-ok` / `check:skill-selftest`（34/34、26/26）

## 范围外

- 不实现"自动注入候选描述到客户端"（各客户端机制不同）。
- 不改评测集与阈值。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-19 | 实现：agent 模式 + 不同 `--description` → 显式报错（rc=1）；`--help` 标注 | 实测 rc=1 + 可行动错误信息；Gate 34/34、selftest 26/26 | 收敛 |
