---
id: REQ-0018
title: 复审门禁后移 + 结构化 findings（评估后只呈现、不自动落盘）
skill: shy-skill-suite
status: done
iteration: 2
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: [REQ-0019, REQ-0020]
---

# REQ-0018 复审门禁后移 + 结构化 findings（评估后只呈现、不自动落盘）

## 问题与目标

现状：复审/评测一结束就**自动落盘并进入优化**，用户没有先看结果再决定的机会。

- 证据（读源码）：`references/lifecycle.md:47-55` 阶段 4「复审后**必须**把结果折回 REQ，而不是只留一份报告」；`references/reviewing-skills.md:143` Step 8 完成判据「**并把结果回写需求文档**（勾选验收、追加迭代记录…）」。
- 影响：用户看到的是"已经改完了"，而不是"这是结果与建议，要不要落盘"。

目标：复审/评测后**只呈现并停下**；落盘 REQ、优化、回写状态一律由用户**显式触发**（`/shy-apply` 或明确说"落盘/回写"）。同时，为 HTML 报告（`REQ-0019`）定义一份**结构化 `findings.json`** 作为"修改意见"的数据源。

## 触发与分支

- 走 `lifecycle.md` 阶段 3 → 阶段 4 之间（复审收工后）。
- 走 `reviewing-skills.md` Step 8（汇总裁决）收工后。
- 用户说"先别改，给我看结果 / 这些意见先别落盘"。

## 行为与步骤

1. **定义 `findings.json` 契约**（写给 `reviewing-skills.md`，供 `render_report.py` 消费）：

   ```json
   {
     "skill": "<skill-name>",
     "iteration": 1,
     "generated_at": "<ISO-8601>",
     "verdict": "可合入 | 改后可合入 | 需重做",
     "summary": {"candidates": 0, "passed": 0, "falsified": 0},
     "findings": [
       {
         "axis": "行为 | 需求 | 标准",
         "priority": "P0 | P1 | P2",
         "location": "file:line",
         "problem": "我看到 X",
         "impact": "...",
         "suggestion": "改哪里、改成什么、预期行为怎么变",
         "expected": "预期行为变化",
         "falsification": "推翻它要跑的命令 / 原文",
         "evidence": "已跑结果",
         "verified": true
       }
     ]
   }
   ```

   位置：工作区 `<skill>-workspace/iteration-N/findings.json`；纯复审无 eval 时放 `<skill>-workspace/findings.json`。

2. **`reviewing-skills.md` Step 8** 完成判据改为：产出分轴 findings + 三档结论 + `findings.json`，**呈现给用户后停止，等待显式触发**；删掉"回写需求"这一强制动作（改为指针到阶段 4）。
3. **`lifecycle.md` 阶段 4** 由「复审后必须回写」改为「**默认不回写**；仅当用户显式触发（`/shy-apply` 或明确说"落盘/回写"）才回写」。把"回写"明确标注为 `REQ-0018` 引入的**门禁**。
4. **门禁规则单一事实源**：写进 `lifecycle.md` 阶段 3→4 之间（新增「呈现门禁」句），`reviewing-skills.md` Step 8 只留一句指针，不重述。
5. 不改脚本；不改 `REQ-0010`/`REQ-0011` 的调用方式结论。

## 脚本与资源

- 改 `references/lifecycle.md`（阶段 4 改语义 + 新增「呈现门禁」）、`references/reviewing-skills.md`（Step 8 完成判据 + `findings.json` 契约）。
- 不改脚本；HTML 渲染见 `REQ-0019`。

## 降级与边界

- **不改**"先证伪再提意见"（`reviewing-skills.md §3`）——门禁动的是"何时落盘"，不是"如何提意见"。
- 用户显式触发后，回写流程仍按 `lifecycle.md` 阶段 4 原有的勾选/追加/改 `status` 执行，不简化。
- `findings.json` 是**呈现层的中间产物**，不取代 REQ；是否把它归档由用户触发后决定。

## 验收标准

- [x] `lifecycle.md` 阶段 4 不再出现"必须把结果折回 REQ"；改为"仅当用户在上一步显式触发后，才把结果折回 REQ"（`grep "必须.*折回"` → 0 命中）。
- [x] `lifecycle.md` 有且仅有一处「呈现门禁」规则句（`grep "只呈现、不落盘"` → 1 命中，`lifecycle.md:47`）；另两处为指针（`lifecycle.md:75`、`reviewing-skills.md:143`）。
- [x] `reviewing-skills.md` Step 8 完成判据含"呈现给用户；然后停下 / 回写要等用户显式触发"，且不再含"必须回写需求文档"。
- [x] `reviewing-skills.md` 含 `findings.json` 契约，字段名与 `REQ-0019` 的消费字段一致（`axis/priority/location/problem/impact/suggestion/expected/falsification/evidence/verified` + `verdict/summary`）。
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。

## 范围外

- 不实现 HTML 渲染（`REQ-0019`）、不建斜杠命令（`REQ-0020`）。
- 不改脚本成功路径行为；不改 `grilling.md`。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（用户诉求：评估后先呈现、不自动优化） | — | 待开工 |
| 2 | 2026-09-16 | 实施：`lifecycle.md` 阶段 3 补「呈现门禁」、阶段 4 改「仅显式触发才回写」、表项与一句话对齐；`reviewing-skills.md` Step 8 完成判据改「呈现并停下」+ 落 `findings.json` 契约；`writing-requirements.md` 两处「每轮回写」改「用户确认后回写」 | `grep "只呈现、不落盘"` → 1；`grep "必须.*折回"` → 0；`validate_skill.py` → ok；字段与 REQ-0019 对齐 | 收敛（done） |

## 备注 / 待办

- 来源：2026-09-16 用户诉求（对标 skill-creator 的"人看结果再决定"闭环）；本次决策问答：报告范围=评测+复审合一、落盘入口=`/shy-apply`+自然语言。
- **实施时范围补充**（复核发现两处漏网的无条件回写，已一并改）：`writing-requirements.md:14`「每轮复审后回写」、`:59`「每轮复审后的回写」；另 `lifecycle.md:3`（闭环图补「呈现」）、`:11`（findings 位置改 `findings.json`）、`:75`（一句话加门禁指针）。
- 与 `REQ-0019`/`REQ-0020` 的分工：本 REQ 定**数据契约与门禁**，后两者分别做**渲染**与**触发入口**。
