---
id: REQ-0081
title: 台账 TTL 接线：按 Gate 次数逐条计龄，超期黄告警（不阻断）
skill: shy-skill-suite
status: done
kind: feature
iteration: 1
created: 2026-09-24
updated: 2026-09-24
blocked_by: []
related: [REQ-0080]
---

# REQ-0081 台账 TTL 接线：按 Gate 次数逐条计龄，超期黄告警（不阻断）

## 问题与目标

`state.json` 里有 `cleanup_ttl_gate_runs: 3`（本意：台账 open 项须在 N 次 Gate 内结清），但**没有任何脚本读它**，也没有"跑过几次 Gate"的计数——`cleanup.md` 的 22 条 `open` 因此只会堆积（来源：`cleanup.md` 备注 + 设计 §4.3；`CL-0020`/`CL-0023` 记录"未接线"）。

目标：把这条纸面规则接线——`run_checks.py` 维护"Gate 运行次数"与**逐条 open 项的年龄**，超过 TTL 的项**黄告警**（不阻断），让积压可见、可被处理。

## 触发与分支

- 触发：每次 Gate（`run_checks.py --root . --skill <skill>`）。
- 分支：`scripts/run_checks.py`（读 `cleanup.md` + `state.json`）。

## 行为与步骤

1. 读 `docs/<skill>/state.json` 的 `cleanup_ttl_gate_runs`（默认 3）与 `cleanup_age`。
2. 维护计数器 `gate_runs`（每跑一次 Gate +1）与逐条年龄 `cleanup_age`：每条 `open` 项年龄 = 上次年龄 + 1（新项从 0 起；已关闭项移除）。
3. 二者写回 `state.json`。
4. **超期** = 某条 `open` 项年龄 > TTL → 输出一行 `[warn] 台账超期（N 次 Gate 内未结清，gate_runs=K）：CL-…`；无超期输出 `[info]`。
5. **仅告警、不阻断**：不改 Gate 退出码、不影响 `converged`。
6. `cleanup.md` / `state.json` 缺失（技能单独部署）→ 跳过，返回 `None`，不报错。

## 脚本与资源

- 改 `scripts/run_checks.py`：新增 `cleanup_ttl()`、主流程接线与告警行、`req0081-ttl-wired` 检查。
- `docs/shy-skill-suite/state.json` 由 Gate 运行自动写入 `gate_runs` / `cleanup_age`。

## 降级与边界

- 无 `docs/`（部署场景）→ 跳过，不报错、不影响 Gate。
- 黄告警**不阻断**（用户决策）；不自动结清、不自动 `wontfix`。

## 验收标准

- [x] `run_checks.py` 读 `cleanup_ttl_gate_runs`、维护 `gate_runs` / `cleanup_age`、超期输出 `台账超期` 且注明「不阻断」 —— `check:req0081-ttl-wired`
- [x] 实跑 Gate：输出含 `台账 TTL` 或 `台账超期` 行，且退出码仍与 `converged` 一致 —— 判定：跑 `run_checks.py --root . --skill shy-skill-suite` 看输出（语义）
- [x] `state.json` 出现 `gate_runs` / `cleanup_age` 两个键 —— 判定：读 `docs/shy-skill-suite/state.json`（语义）
- [x] `python "skills/shy-skill-suite/scripts/track_requirements.py" --root .` → `status: ok` —— 判定：跑该命令看输出（语义）

## 范围外

- 自动结清 / 自动转 `wontfix`。
- 红门（阻断）；本次按用户决策只做黄告警。
- 台账写命令与 `dedup_key` 归一化（`CL-0023`，另有条目）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-24 | 落需求 + 实现接线（逐条计龄 / state.json 计数器 / 黄告警） | 待跑 | 实现 |
| 2 | 2026-09-24 | 实现：`run_checks.py` 新增 `cleanup_ttl()`（读 `cleanup_ttl_gate_runs`、维护 `gate_runs`/`cleanup_age`、超期黄告警「不阻断」）+ 主流程接线 + `req0081-ttl-wired` | `validate_skill` ok；`run_checks` **87/87**（含 req0081）；实跑输出 `[info] 台账 TTL：gate_runs=1，无超期（阈值 3）`；`state.json` 落 `gate_runs`/`cleanup_age`；`selftest` 39/39；`track` ok | 全部验收过，转 done |

## 备注 / 待办

逼问：已过 1 轮（Q1 逐条计龄；Q2 计数存 `state.json`；Q3 黄告警、不阻断）。
接线后 `CL-0020` 的「`cleanup_ttl_gate_runs` 无人读」部分消解（`converged` / `invariant_budget_growth` 仍未读）。
