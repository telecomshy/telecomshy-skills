---
id: REQ-0055
title: 复审范围收口（不把历史 REQ 散文当基准）
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0030, REQ-0053]
---

# REQ-0055 复审范围收口（不把历史 REQ 散文当基准）

## 问题与目标

2026-09-18 真实失败：iteration-4 复审里，一条 P2 finding 引用了 `REQ-0019:42`——那是该 REQ 的「行为与步骤」**历史散文**，不是现行契约；且它早已被 `REQ-0053` 修正。若照此修复，就会改动一个**没人再承诺**的旧说法，制造新问题。

**根因（我看到 X）**：`reviewing-skills.md` Step 3 的「文档-实现不一致」四条明说要去读 `REQ 的「触发与分支」/「范围外」/「脚本与资源」`——这些全是 REQ 散文。技能**自己**授权了审稿人读历史，与「历史 REQ 冻结、只跑不变量集」的模型冲突。

目标：复审只以**技能文件 + 各 REQ 的 `## 验收标准`**为基准；历史散文（问题与目标 / 行为与步骤 / 范围外 / 备注）冻结，过期不算 finding；候选 finding 的 `location` 必须落在技能文件或验收标准行。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 3 的一切判定与 finding。
- 派发 spec-reviewer 子 agent 时的 brief。

## 行为与步骤

1. Step 3 开头加范围收口：只读技能文件 + `## 验收标准`；历史散文冻结；`location` 限定。
2. 四类 finding 的措辞改成以**不变量 / 技能文件**为基准（删掉「REQ 的『触发与分支』/『范围外』/『脚本与资源』」这些散文引用）。
3. `subagents.md` 的 spec-reviewer 输入与禁令同步：**只看技能文件与验收标准**；引用历史散文的候选直接丢弃。
4. 不改 Step 0/1/2/4-8；不改历史 REQ。

## 脚本与资源

- 改 `references/reviewing-skills.md`（Step 3）、`references/subagents.md`（spec-reviewer）。
- 无脚本改动。

## 降级与边界

- 这是**范围收窄**，不减少不变量集的检查；`check:` / `（行为）` / `（语义）` / `（未定）` 照旧。
- 历史散文与现状冲突**不是** finding；要改现状，走新的 REQ。
- 不引入"再审反馈"的二次评审环——那正是要避免的循环。

## 验收标准

- [x] Step 3 写明「只读技能文件 + `## 验收标准`；历史散文冻结；`location` 限定」，且四类 finding 不再引用 REQ 散文 — （语义）已落：Step 3 加「范围收口（REQ-0055）」段；四类 finding 基准改为不变量 / 技能文件
- [x] `subagents.md` 的 spec-reviewer 输入限定技能文件与验收标准，并含"引用历史散文的候选丢弃" — （语义）已落：输入删去 REQ 全文，禁令加"引用历史散文的候选直接丢弃"
- [x] `REQ-0019` 的复查不再作为 finding 来源：用"引 `REQ-0019:42`"做反例，能引用 Step 3 规则把它判为越界 — （语义）规则已写明：`location` 必须落在技能文件或 `## 验收标准` 行

## 范围外

- 不新增自动检查脚本（范围判定是语义动作）。
- 不追溯清理历史 REQ 散文。
- 不做 findings 的二次复审子 agent（防循环）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 实现：`reviewing-skills.md` Step 3 加范围收口（基准=技能文件+验收标准；历史散文冻结；`location` 限定）；四类 finding 改基准；`subagents.md` spec-reviewer 输入与禁令同步 | Gate：`validate` ok；`run_checks` 31/31；`selftest` 20/20；`untagged 0`、`converged true` | 收敛 |

## 备注 / 待办

- 来源：2026-09-18 用户质疑"修了错误 finding 会造新问题；怎么彻底避免"。
- 与 `REQ-0030` 的关系：`REQ-0030` 管"扫不扫全量"；本 REQ 补"散文不是基准"。
