---
id: REQ-0047
title: 复测「差不多」的误触发（每条至少 5 次，分清真误触发和噪声）
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0010, REQ-0024, REQ-0039, REQ-0044]
---

# REQ-0047 复测「差不多」的误触发（每条至少 5 次，分清真误触发和噪声）

## 问题与目标

`iteration-3` 复审（2026-09-18）行为轴 P1（待验证）：`description` 的 near-miss 误触发结论**互相打架**——

```
REQ-0039：同一批 near-miss，旧/新描述都是 0/3（判为单跑噪声）
REQ-0044：同一批 near-miss 用 --trials 3 跑出 #101/#103 触发率 0.667（2/3）
```

两处都基于 **n=3** 的小样本，谁也没说服谁；而 `reviewing-skills.md` Step 1 的判据是负例触发率必须 < 0.5。结论不定，就无法判断该不该给 `description` 补负向边界。

目标：用**每条 ≥5 次**的复测，把 near-miss 分成「稳定误触发（≥0.5）」与「噪声（<0.5）」两类，并据此决定是否补边界。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 1 触发审查 / description 优化环。
- 用户说"触发准不准 / 跑一遍触发评测 / 把触发边界收一下"。

## 行为与步骤

1. 用技能自带评测集 `evals/evals.json`（随技能入库，见 `REQ-0049`）的 near-miss 子集，真跑
   `optimize_description.py <skill_dir> --eval-set evals/evals.json --runner opencode --detect shy-skill-suite --trials 5`。
2. 记录**每条**的触发率（0–1）。稳定 > 0.5 的判为真误触发。
3. 对真误触发项：按 `writing-skills.md` §1 补一句负向边界（`不适用于……`），再重测**正例**确认没有把该触发的漏掉；若正例触发率下降，回退该句。
4. 对 < 0.5 的项：在 `REQ-0044` 的迭代记录里把「0.667」更正为噪声，并写明本次样本量。

## 脚本与资源

- 复用 `scripts/optimize_description.py`（`--trials`）、`scripts/agent_runner.py`。
- 评测集 `evals/evals.json`（`REQ-0049` 入库）。
- 可能改 `SKILL.md` 的 `description`（仅当步骤 3 成立）。

## 降级与边界

- **无 runner**（本机无 opencode / TeleAgent 非交互 CLI）时保持 `ready`、**不臆测**结论——`REQ-0039` 已因单跑噪声白改过一次。
- 负向句同样占 `description` 常驻预算，只加必要的、不过度列举。
- 不扩评测集规模、不改评测口径（那是 `REQ-0044`）。

## 验收标准

- [x] 每条 near-miss 至少跑 5 次、给出触发率（0–1），报告与命令写入迭代记录 — （行为）已落（见迭代记录 2–8 行；`--trials 5` 报告在 `desc-opt-nearmiss.json`）
- [x] 稳定误触发项处置 — （语义）**结论更新**：`#107` 的"稳定误触发"经 `REQ-0067` 的 `skill-line` 检测证实为**测量假象**（agent 只在回答里提到技能名，并未加载）；20/20 负例全 0.0，无需补边界；`REQ-0044` 的 0.667 已更正为噪声
- [x] `python skills/shy-skill-suite/scripts/validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`（2026-09-21 台账 CL-0037 结清：`check:skill-validate-ok` 已绿，原 `[ ]` 未勾为勾选漂移）

## 范围外

- 不扩评测集规模（仍用 `evals/evals.json` 的现有条目）。
- 不改 `optimize_description.py` 的评测口径与算法。
- 不做自动 description 改写环。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 落盘（`iteration-3` 复审 finding 3，用户分拣「以后修」） | `REQ-0039` 0/3 与 `REQ-0044` 0.667 矛盾、n=3 过小 | 待开工 |
| 2 | 2026-09-19 | 真跑（opencode，流式检测已先修）：near-miss 10 条 × 5 次，命令与报告见 `desc-opt-nearmiss.json` | 9 条 <0.5；**#107「把这个技能文档翻译成英文」= 3/5 = 0.6（稳定误触发）**；`REQ-0044` 的 #101/#103 0.667 **未复现**（<0.5，判噪声） | 处置 #107 |
| 3 | 2026-09-19 | 边界候选 A（「不适用于翻译、换语言或格式转换等不改变技能行为的内容处理任务」）临时部署 + 正例对照（11 条 × 5 次；跑完自动还原 `SKILL.md`） | 候选下 **#107 = 5/5 = 1.0（未被压制，反而升）**；正例无下降（`#1/#2/#3/#8` 升至 1.0；`#6` 0.6、`#7` 0.4 属抖动）；还原哈希 `C529CE89FEF5` 一致 | 边界 A **失败**，另择结构性写法 |
| 4 | 2026-09-19 | 候选 B（正向门槛 + description 分支）/ 候选 C（仅插分支）全量对照 | **结论作废**：共用 `--cwd` 被历次运行产物污染——同一负例 `#102` 在脏目录触发率 1.0、全新空目录 0/3；`REQ-0065` 已修隔离并重跑干净基线（`desc-opt-baseline2.json`） | 以干净数据重判 |
| 5 | 2026-09-19 | 聚焦电池（6 条 × 5 次，独立空 cwd） | **作废：环境漂移**——嵌套运行默认模型解析为 None、落到免费模型 `jev-1.13-free`，必触发用例也超时未加载技能，6 条全 0 | 钉模型后重跑（`REQ-0066`） |
| 6 | 2026-09-19 | **钉模型 + 隔离**复测（`--model deepseek/deepseek-flash`，6 条 × 5 次） | 干净结果：`#107` = **0.6**（稳定误触发）；`#104/#102` = 0.0；`#0` = 1.0；`#7` = 0.6；`#6` = 0.2 | 试候选 D |
| 7 | 2026-09-19 | 候选 D（"写或改技能的 SKILL.md"→"写或改技能的行为说明（SKILL.md）"）临时部署 + 同条件复测（跑完自动还原） | `#107` = 1.0（未压制）；`#7` = 0.4、`#6` = 0.6；还原哈希 `C529CE89FEF5` 一致 | 两次改法失败 |
| 8 | 2026-09-19 | `REQ-0067` 修好检测后全量复测（`skill-line` 检测、钉模型、4 并发、独立空 cwd、120s） | **20/20 负例全 0.0**；`#107` 单跑实测：agent 仅在回答中**提及**技能名（"可用技能里只有 shy-skill-suite…"）而未加载 → 裸子串误判；test 分 1.0 | **`#107` 撤销"误触发"结论**；REQ 收敛 |

## 备注 / 待办

- 来源：`skills/shy-skill-suite-workspace/iteration-3/findings.json` 行为轴 P1（verified: false）。
- 与 `REQ-0039` / `REQ-0044` 的关系：本 REQ 是那两次小样本结论的仲裁。
