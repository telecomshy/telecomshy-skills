---
id: REQ-0049
title: 触发评测集入库（evals/evals.json）与 REQ 引用修正
skill: shy-skill-suite
status: done
kind: fix
iteration: 2
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0024, REQ-0039, REQ-0044, REQ-0047]
---

# REQ-0049 触发评测集入库（evals/evals.json）与 REQ 引用修正

## 问题与目标

`iteration-3` 复审（2026-09-18）需求轴 P2：`REQ-0044` 的 `（行为）` 验收项勾了 `[x]`，但支撑它的证据**找不到**——

```
REQ-0039:66 引用工作区 raw 报告（iteration-1/raw/…）   → 文件不存在
REQ-0039/0044 引用「REQ-0024 的 evals.json」           → 文件不存在
工作区唯一的 evals.json（iteration-1）也不含被引用的题（#101「什么是 Agent Skills 标准」等）
```

根因：评测集与原始报告都躺在被 `.gitignore` 忽略的 `*-workspace/` 里，随工作区清理一起消失。REQ 是事实源，证据对不上号，行为结论就无法复核（Spec 轴的行为部分退化成橡皮图章）。

目标：把**评测集本身**放进版本库（随技能走），让触发结论可复现；并清掉指向不存在文件的引用。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 3 需求一致性审查（行为证据可追溯）。
- 用户说"这个结论怎么复现 / 证据在哪"。

## 行为与步骤

1. 把起手触发评测集落到技能内 `evals/evals.json`（相对技能根），**随技能入库**；工作区 `iteration-N/` 仍是不入库的生成物。
2. `references/running-evals.md` 写明评测集位置与「为什么入库」。
3. `SKILL.md` 资源清单补 `evals/evals.json`。
4. `REQ-0039` 的迭代记录删去指向幻影 raw 报告的路径，改为指向可复现命令与评测集。

## 脚本与资源

- 新增 `evals/evals.json`。
- 改 `references/running-evals.md`、`SKILL.md`。
- 改 `docs/shy-skill-suite/requirements/REQ-0039-description-boundary.md`（引用修正）。
- 注册检查 `req0049-evals-present` / `req0049-no-phantom-raw` / `req0049-running-evals-points`。

## 降级与边界

- **不改** `evals.json` 的题目内容（那会改变历史结论）；只把它从工作区搬进版本库。
- 历史那次真跑（`REQ-0044` 的 0.667）的**原始报告未保留**，本 REQ 不伪造它——只在 `REQ-0039` 里如实标注「原始 raw 报告未保留」，并把可复现命令写清。
- 评测集入库≠结论入库；后续重跑仍以 `REQ-0047` 的 ≥5 次为准。

## 验收标准

- [x] `skills/shy-skill-suite/evals/evals.json` 存在、可解析、含 should_trigger 正例与负例 — `check:req0049-evals-present`
- [x] 需求目录内 0 份 REQ 仍引用工作区 raw 报告路径 — （episode）
- [x] `references/running-evals.md` 指明评测集在 `evals/evals.json` 并随技能入库 — （episode）
- [x] `python skills/shy-skill-suite/scripts/validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不重建/补写历史评测集的题目（已丢失的无法还原）。
- 不改评测口径（`REQ-0044`）、不改 near-miss 结论（`REQ-0047`）。
- 不把整个 `*-workspace/` 入库。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 落盘（`iteration-3` 复审需求轴 P2，用户分拣「立即修」） | 实测 raw 报告与 evals.json 均不存在、引用题 0 命中 | 待实施 |
| 2 | 2026-09-18 | 实施：`evals/evals.json` 入库（复制工作区唯一现存的 20 条评测集）；`running-evals.md` 与 `SKILL.md` 补说明；`REQ-0039` 引用修正；注册 3 条检查 | 见下方「备注 / 待办」的门禁输出 | **done** |
| 3 | 2026-09-18 | `iteration-4` 立即修：删 `evals.json` 的 `skill_path`（个人绝对路径）与 `findings F19` 悬空来源；`generate_eval_set.py` 不再写 `skill_path` | `req0049-evals-present` PASS；全仓 0 条 `D:\code` 绝对路径 | done |

## 备注 / 待办

- 来源：`skills/shy-skill-suite-workspace/iteration-3/findings.json` 需求轴 P2。
- 残留：入库的评测集是工作区唯一现存的一份（20 条）；`REQ-0039/0044` 曾引用的另一份 10 条集已丢失，故那两个数字（0/3、0.667）仍不可独立复算——交由 `REQ-0047` 用现入库的集重测。
- 门禁证据（2026-09-18）：`run_checks.py --root . --skill shy-skill-suite` 全过、`req0049-*` 通过；`selftest.py` 20/20；`validate_skill.py` → `status: ok`。
