---
id: REQ-0078
title: 复审按需多跑：默认 3 跑、只针对剪枝与有效性发现、必配独立裁判
skill: shy-skill-suite
status: done
kind: feature
iteration: 1
created: 2026-09-24
updated: 2026-09-24
blocked_by: []
related: []
---

# REQ-0078 复审按需多跑：默认 3 跑、只针对剪枝与有效性发现、必配独立裁判

## 问题与目标

技能复审（`references/reviewing-skills.md`）目前对每条轴只跑一个子代理，**没有成本闸门**，也不支持"多跑取并集"。实验（`docs/shy-skill-suite/research/skill-review-multi-run-experiment.md`，仅仓库内留档）显示：单跑对"真值"的覆盖——剪枝 ≈60%、有效性 ≈41%；而触发轴 8 条候选里 6 条是误报（且已有 `evals` 证据）。即：**部分轴的漏报可观、值得多跑；部分轴多跑只会产噪声。**

目标：给复审加一个**按需多跑**的成本闸门——默认跑 3 轮；只在**剪枝 + 有效性内容发现**两条轴生效；用主代理模型（**不依赖** `shy-models.md`）；**必须配独立裁判**；并把范围明确告知用户。

## 触发与分支

- 触发：用户主动触发复审（`/shy-skill-review` 或自然语言）；委派任何子代理之前。
- 分支：`references/reviewing-skills.md` 的 Step 2（有效性）与 Step 4（剪枝）；其余轴不适用。

## 行为与步骤

1. **一次性询问**（委派前）：要不要多跑？跑几轮？**默认 3 跑**；并**明确告知**：多跑只针对「剪枝（Step 4）+ 有效性内容发现（Step 2）」。
2. **免问例外**：用户本轮已明确要求「彻底 / 高可信 / 多跑」→ 视为已确认，直接按默认 3 跑，仅补报一句规模。
3. **范围**：多跑仅用于 剪枝 + 有效性内容发现；**触发轴、安全轴单跑**（触发轴不提供多跑选项）；Spec 轴走 `run_checks.py`，不涉及。
4. **模型**：用**主代理的模型**多跑；**不读** `~/.config/opencode/shy-models.md`（不依赖 `shy-setup-models`）。
5. **裁决**：**必须配独立裁判**——用主代理模型 + **盲评**（独立上下文、不看跑次标签）逐条复核；产出标**票数**，**共识优先采信、独报标「需复核」**。
6. **并发降级**：支持并发 → 并行；不支持 → **串行**（延迟 ×N，先告知）；子代理都不可派 → **内联**并标注「未隔离（独立性打折）」。

## 脚本与资源

- 改 `references/reviewing-skills.md`：新增「成本闸门 · 按需多跑」小节（在 Step 0 之前）；Step 2 / Step 4 的完成判据加一句指针。
- 改 `references/glossary.md`：新增术语 剪枝 / 多跑（并集）/ 独立裁判。
- 改 `SKILL.md`：共用原则加一条指针。
- 改 `scripts/run_checks.py`：新增 `req0078-multi-run-gate` / `req0078-glossary-terms`。
- **无** `scripts/` 逻辑改动、无命令改动。

## 降级与边界

- 不支持并发 → 串行；子代理不可派 → 内联 + 标注独立性打折（沿用 `subagents.md`）。
- 不读、不要求 `shy-models.md`；不因缺该文件而失败。
- 触发轴 / 安全轴不提供多跑（避免用户误选烧 token）。
- 实验结论（`docs/` 研究记录）**不进技能文件**（技能须自包含，`docs/` 不随部署）。

## 验收标准

- [x] ~~`references/reviewing-skills.md` 含「按需多跑」闸门：默认 3 跑、只针对剪枝+有效性、必配独立裁判、用主代理模型~~ **（已被 REQ-0079 取代：改为"建议 3 轮 + 默认单轮 + 每次问子代理模型"）** —— （episode）
- [x] `references/glossary.md` 含 剪枝 / 多跑（并集）/ 独立裁判 三条术语 —— `check:req0078-glossary-terms`
- [x] ~~复审闸门显式声明**不读** `shy-models.md`（不依赖用户级矩阵文件）~~ **（已由 REQ-0079 覆盖）** —— （episode）
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok` —— 判定：跑该命令看输出（语义）
- [x] `python "skills/shy-skill-suite/scripts/track_requirements.py" --root .` → `status: ok` —— 判定：跑该命令看输出（语义）

## 范围外

- 把触发轴 / 安全轴改为多跑。
- 依赖 `shy-models.md` 或要求安装 `shy-setup-models`。
- 把 `docs/` 研究记录作为技能运行时依赖（自包含约束）。
- 改 `run_effectiveness.py` / `optimize_description.py` 的评测逻辑。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-24 | 落盘 REQ（逼问收敛：默认 3 跑、仅剪枝+有效性、主代理模型、必配独立裁判盲评、并发降级） | — | 实现 |
| 2 | 2026-09-24 | 实现：`reviewing-skills.md` 新增「成本闸门 · 按需多跑」+ Step 2/4 判据加指针；`glossary.md` 加 剪枝/多跑（并集）/独立裁判；`SKILL.md` 共用原则加指针；`run_checks.py` 加 `req0078-*` 两条 | `validate_skill.py` → `status: ok`；`run_checks.py` 74/74（含 req0078 两条）；`selftest.py` 39/39；`track_requirements.py --root .` → `status: ok` | 全部验收过，转 done |
| 3 | 2026-09-24 | 闸门口径被 **REQ-0079** 精化（默认 3 跑 → 建议 3 轮 + 默认单轮 + 每次问子代理模型）；本 REQ 两条闸门验收改标「已被取代（episode）」，check 由 `req0079-review-gate` 承接 | 本轮 Gate 重跑绿 | 闸门部分由 REQ-0079 取代；术语与其余验收仍有效 |

## 备注 / 待办

逼问：已过 2 轮（D1 触发方式=委派前一次性问+免问例外；D2 模型=主代理模型、不读 shy-models.md；D3 范围=仅剪枝+有效性且明确告知；D4 跑数=默认 3、必配独立裁判）。
依据：`docs/shy-skill-suite/research/skill-review-multi-run-experiment.md`（仓库内留档；不进技能文件）。
