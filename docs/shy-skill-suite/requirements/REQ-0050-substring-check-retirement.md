---
id: REQ-0050
title: 文档措辞子串 check 退休为 episode（迁移试点）
skill: shy-skill-suite
status: done
kind: fix
source: retro
iteration: 2
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0046, REQ-0048, REQ-0049]
---

# REQ-0050 文档措辞子串 check 退休为 episode（迁移试点）

## 问题与目标

`iteration-3` 复审 + 独立评估确认：`run_checks.py` 里一批 `check:` 是**"某文档含某词"的子串检查**（不是行为 / 接口）。它们**一改措辞就假警报**，是"复审→修复→新问题"循环的主要来源之一。设计说明 [`../design/ticket-contract-redesign.md`](../../design/ticket-contract-redesign.md) §4.2 的准入把它们排除出不变量集。

目标：先在**一份 REQ（`REQ-0046`）**上做迁移试点——退休 4 条子串 check、保留行为不变量，**用实验证明**退休后假警报归零、真回归仍被抓。这是设计说明 §6 step 0，试点不过就不推进后续迁移。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 3 / Step 4；迁移（设计说明 §6 step 0）。
- 用户说"按设计做试点 / 先把子串 check 退休"。

## 行为与步骤

1. `REQ-0046` 的 4 条文档措辞标准（`req0046-two-paths` / `user-triggered` / `triage` / `skill-rule`）改标 **`（episode）`**——一次性事实，冻结、**不进 Gate**。
2. `run_checks.py` 删掉这 4 条 check 的注册；新增 **`（episode）` 识别与计数**（不再算"未标"）。
3. 试点脚本 `docs/shy-skill-suite/design/pilot-0046.py`（隔离副本）：迁移后跑 基线 → 无害措辞打磨 → 注入真回归。

## 脚本与资源

- 改 `scripts/run_checks.py`（删 4 条 check、加 `EPISODE_RE` + 计数）。
- 改 `docs/.../REQ-0046-implement-review-separation.md`（4 条标准改 `（episode）`）。
- 新增 `docs/shy-skill-suite/design/pilot-0046.py`（试点脚本）。

## 降级与边界

- **只做 `REQ-0046` 一份**，不做全量迁移（全量是后续 step 3）。
- 退休的 check 不迁移进任何"不变量集"——它们本就不是不变量。
- 其余三类（`check:` / `（行为）` / `（语义）`）的语义与计数不变。
- 本次不改复审范围（Step 3 仍全量），只改"这批 check 不再每轮跑"。

## 验收标准

- [x] `REQ-0046` 的 4 条子串 check 已退休：`run_checks.py` 不再注册它们，`REQ-0046` 内标了 4 个 `（episode）` — `check:req0050-retired`
- [x] `run_checks.py` 识别并单独计数 `（episode）`（不再算未标） — `check:req0050-episode-recognized`
- [x] 试点 `pilot-0046.py` 通过：(a) 无害措辞打磨 0 假警报、(b) 注入真回归仍被抓 — （行为）
- [x] `python skills/shy-skill-suite/scripts/validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不全量迁移 227 条散文（后续 step 3）。
- 不建 `cleanup.md` / `state.json`（后续 step 1/2）。
- 不改复审 Step 3 的扫描范围（后续 step 5）。
- 不动 `REQ-0046` 的 `req0046-superseded`（meta 类，另一批）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 落盘（设计说明 §6 step 0） | — | 待实施 |
| 2 | 2026-09-18 | 实施：4 条子串 check 退休为 `（episode）`；`run_checks.py` 删注册、加 `EPISODE_RE` 与计数；试点脚本落盘 | `pilot-0046.py`：基线 48/48 → 措辞打磨 **48/48（0 假警报）** → 注入回归 **FAIL（被抓）**；`run_checks` 全绿；`validate` ok | **done** |
| 3 | 2026-09-18 | **A4 真实复审（验收契约）**：真仓库改 `references/lifecycle.md` 一处无害同义措辞（diff：`-收工判据` / `+收尾判据`）→ 跑 Gate → 复原 | `run_checks --root . --skill shy-skill-suite`：**26/26 通过 / 0 失败**、`exit 0`、**无 FAIL**、无「措辞 → 回归」类 finding；改动已复原 | **验证通过** |

## 备注 / 待办

- 来源：`skills/shy-skill-suite-workspace/iteration-3/findings.json` + 独立评估；设计说明 §4.2 / §6 step 0。
- 与 `REQ-0046` 的关系：`REQ-0046` 是这 4 条 check 的出处，本次把它的标准改标 `（episode）`。
- 试点是**单 REQ 样本**，不是全量证明；是否推进 step 1–6 由用户按试点结果决定。
