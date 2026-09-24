---
id: REQ-0079
title: 复审闸门精化：建议 3 轮、默认单轮、每次问子代理模型（默认主代理模型）
skill: shy-skill-suite
status: done
kind: feature
iteration: 1
created: 2026-09-24
updated: 2026-09-24
blocked_by: []
related: [REQ-0078]
---

# REQ-0079 复审闸门精化：建议 3 轮、默认单轮、每次问子代理模型（默认主代理模型）

## 问题与目标

`REQ-0078` 给复审加了「成本闸门 · 按需多跑」，但把兜底定成"默认 3 跑"、且未向用户说明多跑的价值与范围、也未提供子代理模型的选择。用户希望更轻、更透明：

- 复审时**明确提醒**用户"多跑能提升质量、建议 3 轮、只针对剪枝与有效性"；
- **跑几轮由用户定**；**用户不表态 → 单轮**（不擅自烧 token）；
- **询问子代理使用的模型**，**默认＝主代理模型**；
- **保持轻量**：不新增配置文件、不依赖 `shy-setup-models`。

目标：把闸门从"默认 3 跑"精化为"**建议 3 轮、默认单轮、每次问模型**"。

## 触发与分支

- 触发：复审开始、委派任何子代理之前（同 REQ-0078）。
- 分支：`references/reviewing-skills.md` 的「成本闸门 · 按需多跑」。

## 行为与步骤

1. 复审开始时**一次性问清三件事**（不分几次打扰）：
   - **说明价值与范围**：多跑能提升质量，但**只针对「剪枝（Step 4）+ 有效性内容发现（Step 2）」**；触发/安全单跑，Spec 机械。
   - **跑几轮**：**建议 3 轮**；可选 单轮 / 2 / 3。**用户不明确回答 → 单轮**。
   - **子代理模型**：**默认＝主代理模型**；用户可报模型 ID 覆盖；多跑时给了多个模型则逐跑轮换，否则同模型。
2. **免问例外**：用户本轮已明确要求「彻底 / 高可信 / 多跑」→ 直接按建议 3 轮跑，仅补报一句规模。
3. 多跑仍**必配独立裁判**（盲评，共识优先、独报标「需复核」）；并发降级不变。
4. **不新增配置文件、不读** `~/.config/opencode/shy-models.md`、不依赖 `shy-setup-models`。

## 脚本与资源

- 改 `references/reviewing-skills.md` 的闸门小节为新口径。
- 改 `SKILL.md` 共用原则的对应指针。
- 改 `scripts/run_checks.py`：`req0078-multi-run-gate` → 由 `req0079-review-gate` 取代（断言新口径）。
- `references/glossary.md` 不变（剪枝 / 多跑（并集）/ 独立裁判 仍适用）。

## 降级与边界

- 用户不表态 → 单轮（保守）。
- 不新增自有配置文件（保持轻量）；不读 `shy-models.md`。
- 触发轴 / 安全轴不提供多跑。
- 本 REQ **不含**"开发完成时提醒用户去复审"（用户本轮未要求）。

## 验收标准

- [x] `references/reviewing-skills.md` 闸门含新口径：建议 3 轮 / 默认单轮 / 每次问子代理模型（默认主代理模型）/ 只针对剪枝+有效性 / 必配独立裁判 / 不读 `shy-models.md` —— `check:req0079-review-gate`
- [x] `references/glossary.md` 含 剪枝 / 多跑（并集）/ 独立裁判 三条术语 —— `check:req0078-glossary-terms`
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok` —— 判定：跑该命令看输出（语义）
- [x] `python "skills/shy-skill-suite/scripts/track_requirements.py" --root .` → `status: ok` —— 判定：跑该命令看输出（语义）

## 范围外

- 新增/维护 `sub-models.md` 等自有配置文件。
- 依赖 `shy-setup-models` 或读 `shy-models.md`。
- "开发完成时提醒去复审"。
- 改触发轴 / 安全轴为多跑。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-24 | 落盘 REQ（逼问收敛：建议 3 轮 / 默认单轮 / 每次问模型默认主代理 / 保持轻量） | — | 实现 |
| 2 | 2026-09-24 | 实现：`reviewing-skills.md` 闸门改为"建议 3 轮 / 默认单轮 / 每次问子代理模型（默认主代理模型）"；`SKILL.md` 指针同步；`run_checks.py` 的 `req0078-multi-run-gate` → `req0079-review-gate`；REQ-0078 受影响验收标取代 | `validate_skill.py` → `status: ok`；`run_checks.py` 74/74（含 `req0079-review-gate`）；`selftest.py` 39/39；`track_requirements.py --root .` → `status: ok` | 全部验收过，转 done |

## 备注 / 待办

逼问：已过 2 轮（P1 用户不表态→单轮；P2 每次复审一次问清含模型；P3 新 REQ-0079）。
取代关系：**部分取代** `REQ-0078` 的闸门口径（默认 3 跑 → 建议 3 轮 + 默认单轮 + 问模型）；按 `writing-requirements.md §3`，不改写 REQ-0078 历史，改其受影响验收并记迭代。
