---
id: REQ-0073
title: 删掉 /shy-apply 命令，实施闸门留在开发生命周期里
skill: shy-skill-suite
status: done
kind: refactor
iteration: 2
created: 2026-09-20
updated: 2026-09-20
blocked_by: []
related: [REQ-0046, REQ-0072]
---

# REQ-0073 删掉 /shy-apply 命令，实施闸门留在开发生命周期里

## 问题与目标

**现状**：`/shy-apply` 是薄封装——加载技能 → 按 `lifecycle.md` 阶段 4，只实施分拣的「立即修」项、回写 REQ、「以后修」落新 REQ、「丢弃」不留痕、单次实施即停。**能力上等价于跟 agent 说"把分拣结果实施掉"**，边际价值只有"稳定入口 + 强制协议"。

**删除理由**：① 薄封装，不值一个命令；② 命令越多越易**副本陈旧**——`/shy-eval` 看不到正是命令副本没同步导致（见 2026-09-20 排查），少一个命令少一个坑；③ 套件原则**先删后加**。

**目标**：删除 `/shy-apply` 命令，但**"用户显式点头后才改"这个闸门不丢**——它落在 `lifecycle.md`（单一事实源）：仅在用户确认分拣后、按分拣单次实施、不自动再审。

## 触发与分支

- 用户完成复审分拣后，直接说"实施这些 / 按分拣改"（不再需要专门命令）。
- 路由调整：`lifecycle.md` 斜杠快捷表去掉 `/shy-apply`；`/shy-review` 收尾从"等 `/shy-apply`"改为"等你确认后实施"。

## 行为与步骤

1. 删除 `commands/shy-apply.md`。
2. `references/lifecycle.md`：斜杠快捷表删 `/shy-apply` 行；阶段 3 收尾、阶段 4 的表述去掉对 `/shy-apply` 的引用，改为"**用户确认分拣后**按所选实施一次即停，不自动再审"（保留原闸门语义）。
3. `commands/shy-review.md`：收尾句改为"**只呈现、不回写、不自动修改——等你确认分拣后实施**"。
4. `SKILL.md` 资源区命令清单去掉 `shy-apply`（与 REQ-0072 改名后的 `shy-reqs` 一并生效）。
5. `run_checks.py` 注册本 REQ 检查。

## 脚本与资源

- 删除 `commands/shy-apply.md`。
- 改 `references/lifecycle.md`、`commands/shy-review.md`、`SKILL.md`。
- 改 `scripts/run_checks.py`。

## 降级与边界

- **闸门保留**：删除的是命令，不是"实施前需用户确认"的规则；该规则留在 `lifecycle.md`。
- 不改复审报告 / 分拣 UI / `triage.json` 机制。
- 不自动实施、不自动再审（与 REQ-0046 一致）。

## 验收标准

- [x] `commands/shy-apply.md` 不存在；`lifecycle.md` 斜杠快捷表与正文不再引用 `/shy-apply` — `check:req0073-apply-removed`
- [x] `lifecycle.md` 保留"用户确认后按分拣单次实施、不自动再审"的表述 — `check:req0073-gate-preserved`
- [x] `commands/shy-review.md` 收尾为"等用户确认分拣后实施"，不指向 `/shy-apply` — `check:req0073-review-closing`
- [x] `SKILL.md` 资源区命令清单不含 `shy-apply` — `check:req0073-skill-commands`
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`；`selftest.py` 退出码 0 — `check:skill-validate-ok` / `check:skill-selftest`

## 范围外

- 不改分拣 UI / `triage.json` / 复审报告。
- 不引入替代命令。
- 不改"以后修 → 落 `ready` REQ"的规则。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-20 | 落需求（未实现） | — | 待实现 |
| 2 | 2026-09-20 | 实现：删除 `commands/shy-apply.md`；`lifecycle.md` 斜杠快捷表删 `/shy-apply`、阶段 3 收尾改为「用户确认分拣后按所选实施一次即停，不自动再审」；`commands/shy-review.md` 收尾改为「等确认分拣后实施」；`SKILL.md` 命令清单去掉 `shy-apply`；顺带清 `commands/shy-eval.md` 与 `SKILL.en.md` 的悬空引用；`run_checks.py` 注册 4 条 `req0073-*` | `validate_skill.py` → ok；`run_checks.py` 44/44（含 4 条 req0073）；`selftest.py` 35/35 | done |

## 备注 / 待办

逼问：已过 3 轮——G 节点（`/shy-apply` 去留）用户确认「删」。

- 来源：2026-09-20 用户质疑「`/shy-apply` 说明是实施 REQ，感觉用处不大，直接让 agent 实施不就行了」。
- 与 REQ-0072 同改 `lifecycle.md` 斜杠快捷表与 `SKILL.md` 命令清单，实现时注意避免同文件冲突。
