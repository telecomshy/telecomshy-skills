---
id: REQ-0044
title: 触发评测每条多跑（3 次）对齐规范，消除单跑抖动
skill: shy-skill-suite
status: ready
iteration: 1
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0010, REQ-0024, REQ-0039]
---

# REQ-0044 触发评测每条多跑（3 次）对齐规范，消除单跑抖动

## 问题与目标

全量复审（`iteration-2`）行为轴 P2：触发评测的 near-miss 判定**单跑抖动**——

```
iteration-1：9/10，误触发 #101（什么是 Agent Skills 标准）
iteration-2：8/10，误触发 #103（本周工作周报）、#104（渐进式披露）
3×3 探针：旧/新 description 对 #101 均 0/3
```

**每次跑错的还是不同的题**。而技能自己的 `reviewing-skills.md` Step 1 与 `running-evals.md` 都要求"每条查询**跑 3 次**"——我们却一直只跑 1 次。

后果：拿**不合规样本**判断触发边界，差点又为噪声改 `description`（`REQ-0039` 已发生过一次）。

目标：把触发评测的执行口径对齐规范——**每条查询跑 ≥3 次**，算触发率 / 取多数；在跑够之前，不得据单次结果改 `description`。

## 触发与分支

- 复审 Step 1 触发审查 / description 优化环。
- 用户说"触发准不准 / 跑一遍触发评测"。

## 行为与步骤

1. **`scripts/optimize_description.py`**：加 `--trials N`（默认 **3**）；每条查询跑 N 次，`predicted_trigger` 取**多数**（或触发率 ≥ 0.5）；报告里给出每条的实际触发率。
2. **`scripts/agent_runner.py`**：如需要，支持一条 prompt 跑 N 次（或由 `optimize_description` 侧循环调用）。
3. **`references/running-evals.md`**：命令示例补 `--trials`，并写明"默认 3 次"。
4. **`scripts/run_checks.py`**：注册本 REQ 检查。

## 脚本与资源

- 改 `scripts/optimize_description.py`（主）、`references/running-evals.md`、`scripts/run_checks.py`。
- 不改 heuristic 打分算法本身；只改"每条跑几次"。

## 降级与边界

- 跑 3 次成本 ×3（真跑模式下 10 条 × 3 ≈ 5 分钟）；这是**必要的**，否则结论不可复现。
- heuristic 模式无随机性，`--trials` 只对真跑 runner 有意义；heuristic 下保持 1 次。
- 不追求 near-miss 100% 正确；只要求结论**可复现**（多次平均），并如实标注残留误触发率。

## 验收标准

- [ ] `optimize_description.py --help` 含 `--trials`，默认 3 — `check:req0044-trials`
- [ ] `running-evals.md` 命令示例含 `--trials` 并写明默认 3 次 — `check:req0044-doc`
- [ ] 真跑一次 `--trials 3`：报告里每条给出触发率（0–1），且不再单次定生死 — （行为）
- [ ] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不扩评测集规模（仍 5 正 + 5 near-miss）。
- 不改 `description` 内容（本 REQ 只改评测口径）。
- 不做自动 description 改写环。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落盘（全量复审 iteration-2 行为轴 P2） | 两轮失败项不同（#101 vs #103/#104） | 待实施 |

## 备注 / 待办

- 来源：`skills/shy-skill-suite-workspace/iteration-2/findings.json` 行为轴 P2。
- 与 `REQ-0039` 的关系：0039 已被证伪（前提是噪声）——本 REQ 正是那次教训的工具化。
