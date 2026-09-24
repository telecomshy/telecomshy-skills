---
id: REQ-0002
title: 子代理模型只认用户级矩阵——移除仓库级 docs/agents/subagent-models.md 的优先地位
skill: shy-setup-models
status: done
kind: fix
iteration: 1
created: 2026-09-24
updated: 2026-09-24
blocked_by: []
related: [REQ-0001, shy-code-review:REQ-0001]
---

# REQ-0002 子代理模型只认用户级矩阵——移除仓库级 docs/agents/subagent-models.md 的优先地位

## 问题与目标

4 个 shy 技能（`shy-code-review` / `shy-to-spec` / `shy-to-tickets` / `shy-improve-codebase-architecture`）解析子代理模型 ID 时，**优先读仓库级** `docs/agents/subagent-models.md`，用户级矩阵 `~/.config/opencode/shy-models.md` 排第二（现状见各 `SKILL.md` 的模型来源句）。

真实缺口：用户报告 `shy-code-review` 读模型时先读仓库级文件，"这个行为不对"。模型配置本应**跟人走**（换电脑 / 换项目不断），用户级矩阵才是 `shy-setup-models` 的标准流程产物；仓库级优先会让技能被某个项目的文件带跑，且与 `shy-setup-models` 作为唯一配置入口的定位冲突。

目标：把模型来源收敛为**用户级矩阵这唯一来源**，仓库级文件不再被任何技能读取，也不再作兜底。

## 触发与分支

- 触发：用户显式报告"模型解析优先读仓库级文件，行为不对"。
- 分支：`shy-setup-models` 的配置说明 + 4 个 shy 技能的模型矩阵段与降级边界。

## 行为与步骤

1. 4 个 shy 技能的模型来源句改为：只读用户级 `~/.config/opencode/shy-models.md`（由 `/shy-setup-models` 生成）。
2. 该文件缺失时：先问用户并建议跑 `/shy-setup-models`；问不出再**同模型凑满并标注**。
3. 任何技能都不再读仓库级 `docs/agents/subagent-models.md`——移除其优先与兜底地位。
4. `shy-setup-models` 的说明明确：本技能是这套模型矩阵的**唯一配置入口**。

## 脚本与资源

- 改动文件：`skills/shy-code-review/SKILL.md`、`skills/shy-to-spec/SKILL.md`、`skills/shy-to-tickets/SKILL.md`、`skills/shy-improve-codebase-architecture/SKILL.md`、`skills/shy-setup-models/SKILL.md`。
- 无 `scripts/` / `references/` / `assets/` 改动。

## 降级与边界

- 用户级矩阵缺失：问用户 → 同模型凑满并标注（沿用既有兜底，不新增来源）。
- 不引入第二来源：不读 opencode agent 级 `model:` 字段。
- 不删除目标项目里已有的 `docs/agents/subagent-models.md`，也不在技能里给弃用提示。

## 验收标准

- [x] 5 个技能文件的模型来源句一致：只指向用户级矩阵，并含"缺失先问用户 / 建议跑 `/shy-setup-models` / 同模型凑满标注" —— 判定：逐文件读该句（语义）
- [x] 技能文件不再引用仓库级来源：`grep -rn "subagent-models" skills/` 无输出 —— 判定：跑该命令看输出（语义）
- [x] `validate_skill.py` 对 5 个技能均 `status: ok` —— 判定：跑该命令看输出（语义）
- [x] `python "skills/shy-skill-suite/scripts/track_requirements.py" --root .` → `status: ok` —— 判定：跑该命令看输出（语义）

## 范围外

- 读取 opencode agent 级模型配置。
- 删除 / 迁移目标项目里的仓库级模型文件。
- 仓库级 ↔ 用户级自动同步。
- 改 `run_checks.py` 注册表（属 shy-skill-suite，范围外；沿用 `（语义）` + 判定命令先例，见 `shy-setup-models/REQ-0001` 备注）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-24 | 落盘 REQ（逼问 2 轮：顺序=用户级唯一来源 / 兜底=先问用户 / 范围=5 处全同步 / 新 REQ 归属 setup-models / 旧 REQ 标注不改写 / 不留弃用提示） | — | 实现 |
| 2 | 2026-09-24 | 实现：5 处技能表述改为用户级唯一来源（含 `shy-code-review`「按仓库约定」→「按用户级矩阵」）；标注两份旧 REQ（部分取代，不改写历史） | `grep -rn "subagent-models" skills/` 无输出；`validate_skill.py` 5/5 `status: ok`；`run_checks.py` 70/70（converged: true）；`selftest.py` 39/39；`track_requirements.py --root .` → `status: ok` | 全部验收过，转 done |

## 备注 / 待办

逼问：已过 2 轮（frontier 空、用户确认理解一致）。
