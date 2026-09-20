---
id: REQ-0003
title: 把触发评测入库并补上负向边界
skill: knowledge-distill
status: done
kind: feature
iteration: 1
created: 2026-09-19
updated: 2026-09-19
blocked_by: []
related: [REQ-0001, REQ-0002]
---

# REQ-0003 把触发评测入库并补上负向边界

## 问题与目标

2026-09-19 复审（行为轴 P2，待验证）：`knowledge-distill` 的 `description` 覆盖 5 个分支，但**没有任何负向边界**，也未入库 `evals/`。与「对话 → 文档」类相邻技能（`to-spec` / `handoff` / `research`）存在真实 near-miss 风险——用户说「把这段对话整理成文档」时，多个技能都可能抢答。触发错了，技能等于不存在；当前触发率无任何证据。

目标：把触发评测集入库，真跑出触发率，并据结果决定是否需要给 `description` 补负向边界。

## 触发与分支

- 复审 Step 1（触发审查）时运行；不进技能运行时分支，只改 `description` 与评测集。

## 行为与步骤

1. 入库 `skills/knowledge-distill/evals/evals.json`：≥8 条 should-trigger（覆盖 5 个分支的口语/不点名说法）+ ≥8 条 near-miss（含 `to-spec` / `handoff` / `research` / 普通写作等相邻场景）。
2. 用 `optimize_description.py --runner cmd --cmd '<opencode run --model <id> "{prompt}">' --detect knowledge-distill --trials 5 --isolate-cwd` 真跑，按触发率判定（阈值 0.5），**钉住模型 ID 并记录**。
3. 若 near-miss 命中或正例漏触发：改 `description` 措辞 / 补「不适用于……」负向句，用 train/validation 两半验证泛化（只据 train 失败改、用 validation 判泛化），最多 5 轮。

## 脚本与资源

- 新增 `skills/knowledge-distill/evals/evals.json`（随技能入库；工作区 `knowledge-distill-workspace/` 不入库）。
- 可能改 `skills/knowledge-distill/SKILL.md` 的 `description`（仅在评测显示需要时）。
- 用套件脚本：`generate_eval_set.py`（起手集，需人工复核）、`optimize_description.py`（打分 / 真跑）。

## 降级与边界

- 启发式（`heuristic` runner）分数**不是证据**，只能用于排序候选。
- 真跑依赖客户端非交互命令与可用模型；采不到 token 时不得据此下结论。
- 无真实误触发就不加负向句（负向句同样占常驻 `description` 预算）。

## 验收标准

- [x] `skills/knowledge-distill/evals/evals.json` 存在，含 ≥8 条 should-trigger + ≥8 条 near-miss，且覆盖相邻技能场景。 — （语义）判定：10 正例 + 10 near-miss（含 spec / handoff / research / 写作 / 待办 等）
- [x] 真跑触发率：正例与负例均 ≥ 0.5，且所用模型 ID 记录在案。 — （行为）v2：train 12/12、test 8/8，precision/recall = 1.0；模型 `hubeitelecom/deepseek-v4-flash`（见迭代记录）
- [x] 若存在 near-miss 误触发，`description` 已补负向边界并复测泛化（train 改、validation 验）。 — （行为）v1 暴露「待办误触发 1.0」+「回退漏触发 0.33」；v2 补负向边界与回退口语后 20/20
- [x] 评测集随技能入库、工作区产物不入库（`git status` 无 `knowledge-distill-workspace/`）。 — （语义）`evals/evals.json` 已入库；工作区被 `.gitignore` 的 `*-workspace/` 排除

## 范围外

- 不改保存 / 检索 / 健康检查等运行时行为。
- 不做 with/baseline 有效性对照（那是复审 Step 2，另行触发）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-19 | 入库 evals（10 正 + 10 near-miss）；v1 真跑暴露回退漏触发 / 待办误触发；补 description 负向边界与回退口语 → v2 | 模型 `hubeitelecom/deepseek-v4-flash`；v1 train 0.917 / test 0.875；**v2 train 1.0 / test 1.0（20/20）**；产物 `knowledge-distill-workspace/iteration-1/desc-opt-v2.json` | 收敛（done） |

## 备注 / 待办

- 来源：2026-09-19 `knowledge-distill` 复审报告，行为轴 P2（待验证）。
- 逼问：跳过（依据：agent 提案，自带问题与目标 / 范围外 / 验收，无真实分叉）。
