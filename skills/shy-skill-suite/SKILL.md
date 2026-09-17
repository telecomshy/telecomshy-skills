---
name: shy-skill-suite
description: 技能开发套件：面向「技能」这一产物的开发全流程操作规范。当你在逼问 / 澄清某个技能该做什么、新建或修改一个技能、为技能写需求文档（REQ-NNNN 命名 / 结构 / 验收标准）、复审某个技能（触发可靠性、行为有效性、结构预算、脚本与安全）、写或改技能的 SKILL.md、校验技能结构、或推进技能开发的迭代闭环并回写需求时使用。
compatibility: 需要 Python 3（仅标准库，实测 3.14）。scripts/ 只在校验、评测、需求跟踪、生成报告时用到；无 Python 3 时跳过脚本，按 references/ 的规范手工执行。
metadata:
  name_cn: 技能开发套件
  description_cn: 技能全流程操作规范：写技能需求文档，以及生成/改写后复审技能、提出改进并迭代。
  create_source: super-agent-skill-creator
---

# 技能开发套件

覆盖一个技能的**开发生命周期**：逼问 → 落需求 → 实现 → 复审 → **呈现** →（用户确认）回写需求 → 迭代。各分支按用户意图进入对应规范文件。

## 分支路由

| 用户意图 | 进入 |
| --- | --- |
| 开发 / 迭代一个技能的闭环（逼问 → 落需求 → 实现 → 复审 → 呈现 → 回写需求 → 下一轮） | [`references/lifecycle.md`](references/lifecycle.md) |
| 逼问需求 / 拷问一个技能该做什么（含给既有技能回溯意图） | [`references/grilling.md`](references/grilling.md) |
| 怎么写技能 / `SKILL.md` 怎么写 / 把技能写对 | [`references/writing-skills.md`](references/writing-skills.md) |
| 只写 / 改需求文档；"写需求""需求文档""这个改动要做什么" | [`references/writing-requirements.md`](references/writing-requirements.md) |
| 只做复审；"评估这个技能""检查技能""触发准不准""提改进意见" | [`references/reviewing-skills.md`](references/reviewing-skills.md) |
| 跑评测取证据（触发率、有/无技能对照） | [`references/running-evals.md`](references/running-evals.md) |

## 共用原则（各分支都遵守）

- **单一事实源**：定义见 `references/writing-skills.md` §7。
- **技能必须自包含**：定义与检查见 `references/reviewing-skills.md` Step 7。
- **先删后加**：能删的不要改，能改的不要加。
- **证据优先**：没有真实执行轨迹或对照证据的判断，只能标"待验证"，不能当结论。

## 资源

- `references/lifecycle.md` — 开发生命周期与迭代环：逼问 → 落需求 → 实现 → 复审 → 呈现 → 回写需求 → 下一轮。
- `references/grilling.md` — 逼问：设计树 + frontier、技能领域 6 问、三动作（术语规范化 / 场景压测 / 与实现核对）、回溯补写。
- `references/writing-skills.md` — 写好一个技能的 lever（description 指针、信息层级、leading word、剪枝、完成判据、拆分）；复审的 lever 定义以它为准。
- `references/writing-requirements.md` — 技能需求文档（活文档）的用途、命名、结构、写作原则、状态词表、迭代记录与模板。
- `references/reviewing-skills.md` — 复审流程与三轴判据（行为 / 需求一致性 Spec / 标准）、改进意见写法与反模式。
- `references/subagents.md` — 复审外派子 agent 的角色与窄 brief（executor / grader / spec-reviewer / analyzer / comparator）、派发 vs 内联。
- `references/running-evals.md` — 复审的执行层：评测脚本、工作区布局与产物 schema、HTML 报告生成、opencode / TeleAgent 适配。
- `scripts/` — `scaffold_skill.py`（轻量起骨架：只生成 `SKILL.md`）、`validate_skill.py`（结构与规范校验）、`generate_eval_set.py`（生成起手评测集）、`optimize_description.py`（描述打分与选优）、`agent_runner.py`（跑 agent 并检测触发）、`aggregate_benchmark.py`（聚合 benchmark）、`track_requirements.py`（算 REQ frontier、查悬空阻塞边、报回归债）、`render_report.py`（把迭代工作区渲染成单文件 HTML 报告）。
- `assets/report-template.html` — HTML 报告模板（内联样式、无外部资源）。
- `commands/` — opencode 斜杠命令模板（`shy-grill` / `shy-review` / `shy-apply` / `shy-next`；`shy-review` 已含评测）；复制到 `~/.config/opencode/commands/` 生效，复制说明见 `lifecycle.md` 的「斜杠快捷」。

## 范围外

不负责被开发技能的具体领域实现；只负责技能开发全流程的规范：逼问、需求、实现、复审、评测与迭代。
