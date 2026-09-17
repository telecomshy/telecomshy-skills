---
id: REQ-0034
title: 证据硬化：grader 兼评评测集与抽取隐式主张、analyzer notes 落地、description 负向触发
skill: shy-skill-suite
status: done
iteration: 1
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0005, REQ-0007, REQ-0019, REQ-0030]
retroactive: true
---

# REQ-0034 证据硬化：grader 兼评评测集与抽取隐式主张、analyzer notes 落地、description 负向触发

## 问题与目标

**回溯补写（`retroactive: true`）：实现先于需求落盘。** 来源是三份对标调研
（`docs/shy-skill-suite/research/` 下的 `skill-creator.md` §4.1、`skill-forge.md` §4.1、
`skill-development-best-practices.md` §6）综合后筛出的 4 项"让证据更硬"的缺口：

1. **测不出东西的测试无人发现**：grader 只判断言，不质疑断言本身。一条"通过了但测不出东西"的断言，比没有更糟（skill-creator `agents/grader.md:9`）。
2. **断言之外的事实错误漏网**：产出里的隐式主张（如"用了 2023 年数据"）不在断言列表里，没人核验。
3. **analyzer 的结论只活在对话里**：不落盘、不进报告，等于没留证据。
4. **`description` 缺边界**：只有正向的"做什么 + 何时用 + 宁可 pushy"，没有"不适用于……"，邻域误触发无处约束。

目标：让复审的**证据链更硬**（测试集自身被审查、断言外主张被核验、分析结论可追溯），并给 `description` 一条负向边界手段。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 2 的 grader、Step 8 的 analyzer。
- 写 / 改 `description` 时（`writing-skills.md` §1）。

## 行为与步骤

1. **grader 增加两职责**：抽取并核验隐式主张 → `grading.json.claims[]`；兼评评测集本身（弱断言 / 遗漏结果 / 不可验证断言）→ `grading.json.eval_feedback[]`。
2. **analyzer 结论落盘**：写 `<iteration>/analyzer_notes.json`（`{"notes": [...]}`），并增加**恒过 / 恒败 / 技能反转**的断言模式分析。
3. **notes 进 benchmark 与报告**：`aggregate_benchmark.py` 自动读 `<iteration>/analyzer_notes.json`（`--notes` 可覆盖），并入 `benchmark.json.notes` 与 `benchmark.md`；`render_report.py` 渲染 notes。
4. **`description` 负向触发**：`writing-skills.md` §1 增"划边界（负向触发）"，**只在有真实误触发时加**（负向句同样占常驻预算）。

## 脚本与资源

- 改 `references/subagents.md`（grader / analyzer 两段）、`references/running-evals.md`（`grading.json` 字段 + `analyzer_notes.json`）、`references/writing-skills.md` §1。
- 改 `scripts/aggregate_benchmark.py`（`load_notes()` + `--notes` + `benchmark.json.notes` + markdown 段）、`scripts/render_report.py`（渲染 `benchmark.notes`）。
- 改 `scripts/run_checks.py`（注册本 REQ 的检查；并把 `req0030-validate-ok` 泛化为 `skill-validate-ok` 供多份 REQ 复用）。
- 不新增依赖、不抓取产出内容：只读 `<iteration>/analyzer_notes.json`。

## 降级与边界

- `analyzer_notes.json` 缺失 / 损坏 → notes 为空、**不报错**（向后兼容）。
- 文档类验收标准用**文本检查**（代理证据，确定但只证明"文档写了"）；行为类用**端到端 fixture**（真跑 `aggregate_benchmark.py` + `render_report.py`）。两者在验收标准里都能秒级跑。
- 脚本仍纯标准库；notes 只做搬运与渲染，不做语义判断（判断归 analyzer）。

## 验收标准

- [ ] `subagents.md` 的 grader 段含「隐式主张」与「评测集」两项职责，并指向 `claims[]` / `eval_feedback[]` — `check:req0034-grader-duties`
- [ ] `subagents.md` 的 analyzer 段含恒过 / 恒败与 `analyzer_notes.json` 落盘 — `check:req0034-analyzer-notes-doc`
- [ ] `running-evals.md` 记录 `claims[]` / `eval_feedback[]` / `analyzer_notes.json` 三个契约 — `check:req0034-schema-docs`
- [ ] **notes 端到端**：fixture 跑 `aggregate_benchmark.py` → `benchmark.json.notes` 有条目；跑 `render_report.py --no-open` → HTML 含该条 — `check:req0034-notes-pipeline`
- [ ] 无 `analyzer_notes.json` 时 notes 为空且退出码 0（向后兼容） — `check:req0034-notes-optional`
- [ ] `writing-skills.md` §1 含「负向触发」规则 — `check:req0034-negative-trigger`
- [ ] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不做 HTTP 服务器 / 反馈回写（`REQ-0019` 已决）。
- 不内嵌 run 原始产出（`REQ-0019` 已决）。
- 不引入自动 `description` 改写环（skill-creator 的 `run_loop.py`）。
- 不做打包 / 跨客户端分发（见后续决策）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | **回溯补写**：实现先于需求。落 4 项——grader 两职责、analyzer notes 落盘、`aggregate_benchmark.py` + `render_report.py` 支持 notes、`writing-skills.md` §1 负向触发；`run_checks.py` 注册 4+1 条检查（含 1 条端到端）；`req0030-validate-ok` 泛化为 `skill-validate-ok` | `run_checks.py --root . --skill shy-skill-suite` 全绿；端到端 fixture 产出 `benchmark.json.notes` 并在 HTML 渲染 | done |

## 备注 / 待办

- 来源：三份对标调研（`docs/shy-skill-suite/research/skill-creator.md`、`skill-forge.md`、`skill-development-best-practices.md`）中筛出的"可直接吸收"项。
- 与 `REQ-0030` 的关系：都服务于"复审省钱且证据更硬"；本 REQ 补的是**证据侧的三个细节** + description 边界，不动 Spec 轴流程。
- 待决策（不在本 REQ）：`.skill` 打包、跨客户端分发与平台矩阵、description 优化停止规则。
