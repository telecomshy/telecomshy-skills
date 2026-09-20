---
id: REQ-0053
title: 让输出说人话：加术语表、报告面向人、砍掉过程字段
skill: shy-skill-suite
status: done
kind: docs
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0038, REQ-0019, REQ-0052]
---

# REQ-0053 让输出说人话：加术语表、报告面向人、砍掉过程字段

## 问题与目标

用户反馈（2026-09-18）：

1. **解释看不懂**：`REQ-0038` 已有"白话 + why"要求，但格式是"三字段都写成白话"，不是"一行专业 + 一行白话"成对；实际效果不好。
2. **报告内容太多**：HTML 每条 finding 渲染 问题 / 影响 / 建议 / 预期 / 证伪 / 证据 六项。**证伪 / 证据是 agent 自己的判断过程，用户不需要看**。用户只需要：这条意见**干什么**、**为什么要改**、**改了有什么好处 / 影响**。
3. **术语漂移**：套件自造的词（Gate / Discovery / 不变量 / episode …）没有单一准绳；解释时用户看不懂，开发中同一概念可能前后叫法不同。

目标：**HTML 复审报告是给人看的，不是给 agent 看的。**

- 解释与报告统一为「一行专业（术语 / 位置）+ 一行白话（这是什么 → 为什么改 → 改后好处）」。
- 报告只渲染人需要的四字段，过程字段不进报告。
- 建立**套件词汇**（技能内）与被开发技能的**领域词表**（`docs/<skill>/`），吸收 mattpocock `domain-modeling` 的"术语表 + `_Avoid_` + 定下即落盘"思路（不照搬 `CONTEXT.md`）。

## 触发与分支

- 复审 Step 8（报告生成与汇报）、任何"解释某个问题 / 结论"的对话。
- 用户说"看不懂 / 用白话 / 报告太长 / 这个词是什么意思"。
- 逼问（`grilling.md`）术语规范化动作落盘。

## 行为与步骤

1. **新建 `references/glossary.md`**：套件自身词汇（Gate / Discovery / 不变量 / episode / 迁移债 / frontier / 台账 / converged / 三轴 / 分拣），每条 = `术语` + 一行白话 + `_避免_`。
2. **`SKILL.md` 共用原则「输出面向人」**：改成"一行专业 + 一行白话 + 报告不放过程字段"，指向 glossary。
3. **`reviewing-skills.md` Step 8**：报告格式改为四问（问题 → 为什么要改 → 建议怎么改 → 改后好处）；明确 `falsification` / `evidence` 是过程字段，留 `findings.json`、不进 HTML。
4. **`grilling.md` 术语规范化**：加"定下即落盘"——套件词 → `references/glossary.md`；被开发技能的词 → `docs/<skill>/glossary.md`（按需创建）。
5. **`writing-requirements.md`**：一句话说明领域词表位置。
6. **`render_report.py`**：`render_finding` 只渲染 `problem` / `impact` / `suggestion` / `expected`；摘要行不再显示"被证伪"。

## 脚本与资源

- 改 `references/glossary.md`（新增）、`SKILL.md`、`references/grilling.md`、`references/writing-requirements.md`、`references/reviewing-skills.md`、`scripts/render_report.py`。
- 改 `scripts/run_checks.py`：注册 `req0053-report-human`、`req0053-glossary`。
- 不改 `findings.json` 字段集合（`falsification` / `evidence` 保留供审计）。
- 不改 `assets/report-template.html`（模板通用，字段由渲染器决定）。

## 降级与边界

- 过程字段仍然要**产出**（先证伪、附证据是复审规则），只是**不呈现**给人。
- 「一行专业 + 一行白话」是表达要求，不改变 finding 的判定与优先级。
- 无 findings 的纯评测报告只受"报告给人看"约束，术语表不适用。

## 验收标准

- [x] HTML 报告渲染 存在问题 / 白话解释 / 修改建议 三字段，且不出现 `falsification` / `evidence` 的值 — `check:req0053-report-human`（2026-09-18 订正：原「问题 / 为什么要改 / 建议 / 改后好处」四字段由 `REQ-0057` 合并为三字段）
- [x] `references/glossary.md` 存在且 ≥5 条术语 — `check:req0053-glossary`（实测 10 条）
- [x] `SKILL.md` 共用原则与 `reviewing-skills.md` Step 8 写明"一行专业 + 一行白话"、报告不放过程字段 — （语义）已落：`SKILL.md` 共用原则「输出面向人」改写；Step 8 报告格式改为三字段
- [x] `grilling.md` 术语规范化含"定下即落盘"与两层词表位置 — （语义）已落：`grilling.md` 动作 1 加了落盘规则；`writing-requirements.md` §2 加了 `docs/<skill>/glossary.md`

## 范围外

- 不改 `findings.json` 的字段集合与优先级判定。
- 不改 benchmark 区与评测口径。
- 不做多语言 / 语气风格库。
- 不建仓库级 `CONTEXT.md`（技能必须自包含）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 实现：新建 `references/glossary.md`（10 条）；`SKILL.md` / Step 8 / `grilling.md` / `writing-requirements.md` 落「一行专业 + 一行白话」与两层词表；`render_report.py` 只渲染人四字段、摘要去掉"被证伪"；`run_checks.py` 加 2 条 check | Gate：`validate` ok；`run_checks` 29/29（`（行为）8`；`（语义）18`）；`selftest` 20/20；`untagged 0`、`converged true` | 收敛 |

## 备注 / 待办

- 依据：`domain-modeling` 的术语表机制（术语 + `_Avoid_` + 定下即落盘 + 对照挑错）；`writing-for-agents` 的 context pointer / two loads。
- 与 `REQ-0038` 的关系：`REQ-0038` 立了"白话 + why"，本 REQ 修正其格式并**做减法**（砍报告字段）。
- 自包含：套件词表在技能内；被开发技能的领域词表在 `docs/<skill>/`，不随技能分发。
- 2026-09-18（`iteration-6` 立即修）：`glossary.md` 的「不变量」定义放宽——机器能判的写成 `check:`，不能机器判的以（行为）/（语义）每轮判，与 Step 3 的范围口径一致。
