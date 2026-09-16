---
name: shy-skill-suite
description: 技能开发套件：为「技能」这一产物提供全流程操作规范——写技能需求文档（REQ-NNNN 命名、结构、验收标准），在 AI 生成/改写技能后复审技能（触发可靠性、行为有效性、结构预算、脚本与安全），把复审结果回写成需求并持续迭代。触发：要新建或修改一个技能并落盘需求文档；说"写需求/需求文档/这个改动要做什么"；AI 生成或改写 SKILL.md 后要复审、评估技能、检查触发准不准、提改进意见；推进技能开发的迭代闭环、回写需求。
metadata:
  name_cn: 技能开发套件
  description_cn: 技能全流程操作规范：写技能需求文档，以及生成/改写后复审技能、提出改进并迭代。
  create_source: super-agent-skill-creator
---

# 技能开发套件

覆盖一个技能的**开发生命周期**：逼问 → 落需求 → 实现 → 复审 → 回写需求 → 迭代。各分支按用户意图进入对应规范文件。

## 分支路由

| 用户意图 | 进入 |
| --- | --- |
| 开发 / 迭代一个技能的闭环（逼问 → 落需求 → 实现 → 复审 → 回写需求 → 下一轮） | [`references/lifecycle.md`](references/lifecycle.md) |
| 逼问需求 / 拷问一个技能该做什么（含给既有技能回溯意图） | [`references/grilling.md`](references/grilling.md) |
| 怎么写技能 / `SKILL.md` 怎么写 / 把技能写对 | [`references/writing-skills.md`](references/writing-skills.md) |
| 只写 / 改需求文档；"写需求""需求文档""这个改动要做什么" | [`references/writing-requirements.md`](references/writing-requirements.md) |
| 只做复审；"评估这个技能""检查技能""触发准不准""提改进意见" | [`references/reviewing-skills.md`](references/reviewing-skills.md) |
| 跑评测取证据（触发率、有/无技能对照） | [`references/running-evals.md`](references/running-evals.md) |

## 共用原则（各分支都遵守）

- **单一事实源**：一个含义只在一处写；需求文档、`SKILL.md`、`references/` 之间不重复。
- **技能必须自包含**：技能文件（`SKILL.md` / `scripts/` / `references/` / `assets/`）只引用技能自身（相对技能根的路径），不引用仓库级 `docs/` 等外部路径——技能会被单独复制部署，外部引用就是悬空指针。
- **先删后加**：能删的不要改，能改的不要加。
- **证据优先**：没有真实执行轨迹或对照证据的判断，只能标"待验证"，不能当结论。

## 资源

- `references/lifecycle.md` — 开发生命周期与迭代环：逼问 → 落需求 → 实现 → 复审 → 回写需求 → 下一轮。
- `references/grilling.md` — 逼问：设计树 + frontier、技能领域 6 问、三动作（术语规范化 / 场景压测 / 与实现核对）、回溯补写。
- `references/writing-skills.md` — 写好一个技能的 lever（description 指针、信息层级、leading word、剪枝、完成判据、拆分）；复审的 lever 定义以它为准。
- `references/writing-requirements.md` — 技能需求文档（活文档）的用途、命名、结构、写作原则、状态词表、迭代记录与模板。
- `references/reviewing-skills.md` — 复审流程与三轴判据（行为 / 需求一致性 Spec / 标准）、改进意见写法与反模式。
- `references/subagents.md` — 复审外派子 agent 的角色与窄 brief（executor / grader / spec-reviewer / analyzer / comparator）、派发 vs 内联。
- `references/running-evals.md` — 复审的执行层：评测脚本、工作区布局与产物 schema、opencode / TeleAgent 适配。
- `scripts/` — `scaffold_skill.py`（轻量起骨架：只生成 `SKILL.md`）、`validate_skill.py`（结构与规范校验）、`generate_eval_set.py`（生成起手评测集）、`optimize_description.py`（描述打分与选优）、`agent_runner.py`（跑 agent 并检测触发）、`aggregate_benchmark.py`（聚合 benchmark）、`track_requirements.py`（算 REQ frontier、查悬空阻塞边）。

## 范围外

不负责被开发技能的具体领域实现；只负责技能开发全流程的规范：逼问、需求、实现、复审、评测与迭代。
