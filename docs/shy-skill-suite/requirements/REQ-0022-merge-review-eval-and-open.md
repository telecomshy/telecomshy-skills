---
id: REQ-0022
title: 复审与评测合并为单一入口 + 报告生成后自动打开
skill: shy-skill-suite
status: done
kind: refactor
iteration: 2
created: 2026-09-16
updated: 2026-09-17
blocked_by: []
related: [REQ-0019, REQ-0020, REQ-0023]
---

# REQ-0022 复审与评测合并为单一入口 + 报告生成后自动打开

## 问题与目标

用户诉求（2026-09-16 复审后提出）：`/shy-review` 与 `/shy-eval` 都"跑评测 + 出报告"，**边界不清**（复审 finding #6）；且报告生成后**不自动打开**（`REQ-0019` 曾把"不做浏览器自动打开"列为范围外）。

事实依据：
- `references/running-evals.md:3`：eval 是「复审 Step 1（触发）与 Step 2（有效性）的执行层」——eval 本就**属于**复审，不是并列流程。
- `commands/shy-review.md:5` 与 `commands/shy-eval.md:5` 的 body 都含"跑评测 + `render_report.py`"。

目标：**一个命令**跑完复审 + 评测，出一份 HTML 报告并**自动打开**。

## 触发与分支

- `/shy-review`（合并后唯一入口）。
- 用户说"复审并出报告 / 跑一遍看结果"。

## 行为与步骤

1. **删除 `commands/shy-eval.md`**；`commands/shy-review.md` 改为单一入口：加载技能 → 三轴复审（`reviewing-skills.md`）→ 评测（`running-evals.md`：触发率、with_skill vs baseline）→ 落 `findings.json`（有 benchmark 则一并）→ `render_report.py` 出报告并**自动打开** → **停下**（不落盘 REQ）。
2. `scripts/render_report.py`：生成后默认 `webbrowser.open(报告 file URI)`；新增 `--no-open` 关闭（headless / 脚本化）。
3. `references/running-evals.md`：HTML 报告节说明"默认自动打开 + `--no-open`"。
4. `references/lifecycle.md`「斜杠快捷」表：5 行 → 4 行（删 `/shy-eval`，注明 `/shy-review` 已含评测）。
5. **取代标注**：`REQ-0019` 的「范围外：不做浏览器自动打开」、`REQ-0020` 的"5 命令集"，各加一句指向本 REQ。
6. 单一事实源：命令→分支映射仍只在 `lifecycle.md` 表一处。

## 脚本与资源

- 改 `commands/shy-review.md`；删 `commands/shy-eval.md`；改 `scripts/render_report.py`（`--no-open` + 自动打开）。
- 改 `SKILL.md`（资源清单：命令 5 → 4；2026-09-17 复审补记）。
- 改 `references/running-evals.md`、`references/lifecycle.md`、`references/reviewing-skills.md`（Step 8 指针）。
- 改 `docs/.../REQ-0019-html-report.md`、`REQ-0020-slash-commands.md`（取代标注）。

## 降级与边界

- **headless / 无显示环境**：自动打开失败不得报错——`try/except` 包住 `webbrowser.open`，仍写出文件并打印路径。
- 无评测数据时仍出报告（评测区显示"无评测数据"）。
- 不引入服务器、不引入第三方依赖（`webbrowser` 属标准库）。
- 自动打开是**行为变化**，会取代 `REQ-0019` 的范围外声明。

## 验收标准

- [x] `commands/` 只剩 4 个：`shy-grill` / `shy-review` / `shy-apply` / `shy-next`；`shy-eval.md` 不存在。 — （episode）
- [x] `commands/shy-review.md` body 写清：复审 + 评测 + `findings.json` + 渲染报告 + **自动打开** + 停下。 — （episode）
- [x] `render_report.py --help` 含 `--no-open`；默认运行会打开报告（实测 `opened: true`）；`--no-open` 时不打开（实测 `opened` 缺失、调用数 0）。 — `check:render-report-ok`
- [x] 无显示环境（`webbrowser.open` 抛错）下仍 `status: success`、`opened: false`、退出码 0。 — `check:render-report-ok`
- [x] `references/running-evals.md` 说明默认自动打开与 `--no-open`。 — （episode）
- [x] `references/lifecycle.md` 斜杠快捷表为 4 行，注明 `/shy-review` 含评测。 — （episode）
- [x] `REQ-0019`/`REQ-0020` 各含指向本 REQ 的取代说明。 — （episode）
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。 — `check:skill-validate-ok`

## 范围外

- 不改 `render_report.py` 的报告内容结构（只加打开开关）。
- 不引入服务器 / 浏览器反馈回写。
- 不把 `/shy-grill`、`/shy-apply`、`/shy-next` 合并（它们职责不同）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（复审 finding #6 + 用户诉求：合并入口、自动打开） | — | 待开工 |
| 2 | 2026-09-16 | 实施：删 `commands/shy-eval.md`；`shy-review.md` 改为复审+评测单入口；`render_report.py` 加 `open_report` + `--no-open`；`running-evals.md`/`reviewing-skills.md`/`lifecycle.md`/`SKILL.md` 同步；REQ-0019/0020 加取代说明 | 命令 4 个无 shy-eval；桩测：默认 `opened: true`、`--no-open` 0 调用、headless `opened: false` 仍 rc 0；`--help` 含 `--no-open`；`validate_skill` ok | 收敛（done） |

## 备注 / 待办

- 来源：2026-09-16 复审 findings #6（eval/复审边界不清）+ 用户明确诉求（一个命令、自动打开）。
- 命令名决策：保留 **`/shy-review`** 作唯一入口（"复审"是伞概念，`running-evals.md:3` 已声明 eval 属复审），删除 `/shy-eval`。
- `REQ-0023` 的 findings 一致性修正与本 REQ 独立，可并行。
