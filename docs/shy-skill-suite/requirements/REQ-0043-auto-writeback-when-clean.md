---
id: REQ-0043
title: 呈现门禁改为「有事才停」：机械记账自动回写，判断项才停
skill: shy-skill-suite
status: out-of-scope
kind: docs
iteration: 2
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0018, REQ-0041, REQ-0042]
superseded_by: REQ-0046
---

# REQ-0043 呈现门禁改为「有事才停」

## 问题与目标

`REQ-0018` 的呈现门禁规定"复审收尾**只呈现、不回写 REQ**，回写要等用户显式触发"。这条出发点是好的（复审结论是**判断**，不该自动落），但它**一刀切**了：

- 对一个**已跑过门、无 P0/P1、无新发现**的实现类 REQ，停下来没有任何信息增量——用户没有可拍板的东西。
- 不自动回写反而制造脏状态：REQ 停在 `in-progress`、frontier 不空，正是我们一直防的"`status` 说谎"。

**用户诉求（2026-09-17）**："完成的 REQ 应该回写以后再停；只有发现新增的 REQ 才停下来问，因为那时候需要人拍板。"

目标：把门禁从"**总是停**"改成"**有事才停**"：
- **机械记账**（勾验收 / 记迭代 / 改 `status`）——秒级门绿、无 P0/P1、无新事项时**自动回写**，**不停**。
- **判断项**（有 P0/P1、发现新事项要新开 REQ、需求语义变化）——**停**，出 findings + HTML 报告，等人拍板。

顺带定死一个模糊地带：**HTML 报告什么时候出**。

## 触发与分支

- 复审收尾（`lifecycle.md` 阶段 3 → 4）。
- 用户说"完成的 REQ 直接回写就行 / 别老停下来"。

## 行为与步骤

1. **`lifecycle.md` 呈现门禁（阶段 3 → 4）**：改为两分支——无 P0/P1 且无新事项 → 不停、自动机械记账回写、**不必出 HTML**；有 P0/P1 或新事项 → 出 `findings.json` + **HTML 报告并打开**、停。
2. **`lifecycle.md` 阶段 4 触发**："仅当用户显式触发"→"**机械记账不需确认**；涉及判断才需确认"。
3. **`reviewing-skills.md` Step 8 完成判据**：删"**不**回写需求文档——回写要等用户显式触发"，改为"按呈现门禁：无 P0/P1 且无新事项 → 机械记账自动回写、不停；有 P0/P1 或新事项 → 出 HTML、停"。
4. **HTML 时机**：**有 findings（P0/P1 或行为轴结论）才出报告**；纯秒级门无发现不出——避免每改一行就弹浏览器。
5. **`run_checks.py`**：注册本 REQ 的检查。

## 脚本与资源

- 改 `references/lifecycle.md`（阶段 3 呈现门禁、阶段 4 触发）、`references/reviewing-skills.md`（Step 8 完成判据）。
- 改 `scripts/run_checks.py`（注册 `req0043-*`）。
- 不改 `REQ-0018` 的**判断项仍需人**这一内核（本 REQ 只把"机械记账"摘出）。

## 降级与边界

- **判断项仍然停下**：有 P0/P1 / 新 REQ / 语义变化 → 必须人拍板（`REQ-0018` 的内核保留）。
- **自动回写只做机械记账**：勾选、迭代记录、`status`/`iteration`/`updated`；**不**替用户决定"要不要改"。
- 回写后仍须 `track_requirements.py` `status: ok`。
- 不影响 `/shy-apply`：用户仍可显式要求回写 / 修复。

## 验收标准

- [ ] `lifecycle.md` 呈现门禁含"机械记账自动回写 / 不停"与"有 P0/P1 或新事项才停" — `check:req0043-auto-writeback`
- [ ] `lifecycle.md` 含 HTML 时机规则（有 findings 才出，纯秒级门不出） — `check:req0043-html-timing`
- [ ] `lifecycle.md` 阶段 4 含"机械记账不需确认" — `check:req0043-stage4-trigger`
- [ ] `reviewing-skills.md` Step 8 完成判据不再写"不回写需求文档 / 等用户显式触发"，改引呈现门禁 — `check:req0043-review-step8`
- [ ] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不改三轴与 Step 结构。
- 不引入"全自动修复"（判断项永远由人）。
- 不改 `/shy-apply` 的语义。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求并实施：呈现门禁改「有事才停」；阶段 4 机械记账自动；Step 8 同步；定死 HTML 时机 | `run_checks.py` + `validate_skill` 全绿 | **done**（按本 REQ 新规则：无新事项，自动回写） |

## 备注 / 待办

- 来源：2026-09-17 用户提案（实现的判断流程），推翻 `REQ-0018` 的"总是停"默认，保留其"判断项由人"内核。
- 与 `REQ-0041` 的关系：0041 建立"实现 → 必审"门；本 REQ 建立"审完何时停"门。
