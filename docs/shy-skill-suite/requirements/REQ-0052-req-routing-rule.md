---
id: REQ-0052
title: REQ 路由规则（只收行为改动，卫生项进 cleanup）
skill: shy-skill-suite
status: done
kind: docs
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0050, REQ-0051]
---

# REQ-0052 REQ 路由规则（只收行为改动，卫生项进 cleanup）

## 问题与目标

`writing-requirements.md` §1 的口径是"当讨论出一个要做的技能改动（新功能 / 重构 / 修复）并达成一致后，落盘一份需求文档"——读起来"凡改动都开 REQ"。而真正的路由规则（只有改变行为 / 接口的改动才开 REQ；纯自洽 / 卫生 → `cleanup.md`）只写在**冻结的设计说明** §4.3，**不随技能分发**。

后果：删一个没人读的字段（`source`）也会被当成"需要 REQ 的改动"；历史上 4 张 `kind: hygiene` REQ（`REQ-0015` / `0023` / `0028` / `0032`）就是这类过度开单，也是复审循环的来源之一。

目标：把路由规则写进部署的技能文件。agent 落盘前先路由——**行为改动 → REQ；卫生 / 自洽 / 删死字段 → `cleanup.md`**。

## 触发与分支

- `writing-requirements.md` §1「用途与何时写」——agent 准备为某改动落 REQ 之前。
- 用户说"这也要开 REQ 吗 / 这个小改要落单吗"。

## 行为与步骤

1. 在 `writing-requirements.md` §1 加一条路由规则：只有改变行为 / 接口的改动才开 REQ；纯卫生 / 自洽（订正数字、去重、删死字段、不改行为的措辞）→ 记 `cleanup.md`，**不开 REQ**。
2. 判据给成一句可问的话：**"删掉 / 改写它，技能的行为会变吗？"** 不会 → 卫生项。
3. 与 §4「自洽项不进验收标准」交叉引用，不重复其正文（单一事实源）。

## 脚本与资源

- 只改 `references/writing-requirements.md`。无脚本改动。

## 降级与边界

- 不改变 `cleanup.md` 的字段与关闭路径（见 `reviewing-skills.md` Step 8）。
- 不追溯改写历史 `kind: hygiene` REQ（已冻结）。

## 验收标准

- [x] `writing-requirements.md` §1 给出 REQ / cleanup 的路由规则，且不与 §4 重复 — （语义）已落：§1 新增「先路由再落盘」一条；§4「自洽项不进验收标准」正文未复制，仅以指针引用
- [x] 用删 `source` 做一次验证：它被判为卫生项、只登记 `cleanup.md`、未开 REQ — （语义）已验证：`cleanup.md` `CL-0029`（fixed），未为它开 REQ；Gate 台账 fixed 20→21

## 范围外

- 不改 `cleanup.md` 的字段与写权（另见 `CL-0023`）。
- 不改 `track_requirements.py` 对 `source` 的读取（死代码，留卫生批）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 实现：`writing-requirements.md` §1 加「先路由再落盘」；以删 `source` 验证卫生项路由（`cleanup.md` `CL-0029`） | Gate：`validate` ok、`run_checks` 27/27（`（语义）` 14→16、台账 fixed 20→21）、`selftest` 20/20，`untagged 0`、`converged true` | 收敛 |

## 备注 / 待办

- 来源：2026-09-18 与用户讨论"是否所有改动都要落 REQ"。
- 删 `source` 作为本规则的验证用例，登记 `cleanup.md` `CL-0029`（卫生项，不开 REQ）。
