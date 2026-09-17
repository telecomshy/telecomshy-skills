---
id: REQ-0041
title: 实现 → 必审门 + 分层取证（门设在呈现，不设在修复）
skill: shy-skill-suite
status: done
iteration: 2
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0018, REQ-0024, REQ-0030, REQ-0040]
---

# REQ-0041 实现 → 必审门 + 分层取证

## 问题与目标

2026-09-17 复审（`iteration-1/findings.json`）行为轴 **P1**：`lifecycle.md:52` 写着"每完成一个增量就进入复审"，但阶段 2 的**完成判据**（`:58`）只要求 `validate_skill` 通过 + 验收标准有证据——**没有一条要求"复审跑过"**。所以实现完可以直接收工，复审不跑没人拦。本轮即活例：改了一大轮技能文件却没复审，workspace 里长期没有 `findings.json`。

**设计难点（用户提出的两难）**：
- 若"完成必审"做成**全自动闭环** → 变成 skill-forge 式的自动流水线，与"迭代式、人机协作"初衷冲突；
- 若做成**全手动触发** → 可靠性更差（技能已经是 model-invoked，再加"必须用户发命令"等于把可靠性压在人记性上），且证据纪律会被静默绕过；
- 且担心重新陷入 **审 → 发现 → 修 → 审** 循环。

**目标（本 REQ 的取舍）**：**门设在"取证 + 呈现"，不设在"修复"**。
- 强制的是"实现完必须产出 `findings.json` 并呈现"，**不是**"修到过"——所以不会自动循环（循环的燃料——重读散文——已被 `run_checks` + P2 不阻断 + 自洽项不复扫掐断）。
- **分层取证**控成本：任何改动跑**秒级门**；行为相关 / 里程碑才加**行为 eval**。
- 审后**即停**，回写 / 修复仍由人触发（呈现门禁不变）。

## 触发与分支

- 任何技能改动进入"实现完成"判定时（`lifecycle.md` 阶段 2 → 3）。
- 复审 Step 0 的立靶与规模判断。

## 行为与步骤

1. **`lifecycle.md` 阶段 2 完成判据**：加"**且已进入阶段 3——已产出 `findings.json` 并呈现（可为空）**"；写明"实现完成 ≠ 改完代码，而是过了校验 + 审过一轮"。
2. **`lifecycle.md` 阶段 3**：加**分层取证**——① 任何改动（默认）跑秒级门：`validate_skill.py` + `run_checks.py` + `selftest.py`，据此产出 `findings.json`（空 = 可合入）；② 行为相关改动 / 里程碑：再加 Step 1 / Step 2 的行为 eval（触发率、with/baseline delta，分钟级）。并写明**跳过**：用户明确说"别审 / 跳过复审"时可不跑，但须在结论注明"未做复审"。
3. **`SKILL.md` 共用原则**：加"**实现 → 必审（取证）**"，指向阶段 3。
4. **`scripts/run_checks.py`**：注册本 REQ 的检查。

## 脚本与资源

- 改 `references/lifecycle.md`（阶段 2 / 阶段 3）、`SKILL.md`（共用原则）。
- 改 `scripts/run_checks.py`（注册 `req0041-*`）。
- 不改 `reviewing-skills.md` 的 Step 流程（分层是"跑到哪一步"的规模旋钮，不是新步骤）。

## 降级与边界

- **强制的是"取证 + 呈现"，不是"修复"**：`findings.json` 可以为空（无 P0/P1 即可合入）。这是与"全自动修复闭环"的根本区别。
- **不引入状态戳**：是否"审过"由这一轮是否产出 `findings.json` 判断，不留永久字段。
- **轻量门不等于免行为轴**：行为相关改动仍必须跑行为 eval，不能用秒级门替代。
- 跳过须**在结论里注明**，不做静默豁免。

## 验收标准

- [x] `lifecycle.md` 阶段 2 完成判据含"findings.json / 已进入阶段 3" — `check:req0041-stage2-gate`
- [x] `lifecycle.md` 阶段 3 含分层（"秒级门"与"行为 eval"并存）+ 跳过须注明 — `check:req0041-layered`
- [x] `SKILL.md` 共用原则含"实现 → 必审" — `check:req0041-skill-rule`
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不做全自动"修复 → 再修 → 再审"闭环（明确否决）。
- 不改 `reviewing-skills.md` 的三轴与 Step 结构。
- 不在本 REQ 修 P2 findings（token 缺失 / baseline 方法论 / `__pycache__` / 计数漂移）——那些见 `iteration-1/findings.json`，另议。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求并实施（阶段 2 加必审门；阶段 3 加分层取证；`SKILL.md` 加"实现 → 必审"；`run_checks.py` 注册 3 条检查） | `run_checks.py` + `validate_skill` 全绿 | 待用户确认（呈现门禁） |
| 2 | 2026-09-17 | **回写**：实现 + 秒级门绿（`run_checks` 31/31、`validate` ok），无 P0/P1 → 自动回写 `done`。按新规则：机械记账（勾验收 / 记迭代 / 改 status）不必停下等确认；只有发现新事项才停。 | `run_checks` 31 通过 / 0 失败；`validate` ok | **done** |

## 备注 / 待办

- 来源：2026-09-17 复审 P1（`iteration-1/findings.json`）+ 与用户的方案论证。
- **淘汰的候选**（逐条考虑，不进建议）：
  1. **全自动闭环（自动修 + 自动再审）**——与迭代式初衷冲突，且会把判断权从人手里拿走 → 否决。
  2. **全手动触发（必须用户发命令才审）**——可靠性更差、证据纪律可被静默绕过 → 否决。
  3. **每次都跑全轴复审**——行为 eval 分钟级，太贵 → 改为分层。
- 与 `REQ-0018` 的关系：呈现门禁不变（本 REQ 只是把"进入复审"变成硬门）。