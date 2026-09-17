---
name: shy-skill-suite
description: 技能开发套件：面向「技能」这一产物的开发全流程操作规范。当你在逼问 / 澄清某个技能该做什么、新建或修改一个技能、为技能写需求文档（REQ-NNNN 命名 / 结构 / 验收标准）、复审某个技能（触发可靠性、行为有效性、结构预算、脚本与安全）、写或改技能的 SKILL.md、校验技能结构、或推进技能开发的迭代闭环并回写需求时使用。
compatibility: 需要 Python ≥ 3.7（仅标准库，实测 3.12）。scripts/ 只在校验、评测、需求跟踪、生成报告时用到；Python 版本过低时跳过脚本，按 references/ 的规范手工执行。
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
| 开发 / 迭代一个技能的闭环 | [`references/lifecycle.md`](references/lifecycle.md) |
| 逼问需求 / 拷问一个技能该做什么（含给既有技能回溯意图） | [`references/grilling.md`](references/grilling.md) |
| 怎么写技能 / `SKILL.md` 怎么写 / 把技能写对 | [`references/writing-skills.md`](references/writing-skills.md) |
| 只写 / 改需求文档；"写需求""需求文档""这个改动要做什么" | [`references/writing-requirements.md`](references/writing-requirements.md) |
| 只做复审；"评估这个技能""检查技能""触发准不准""提改进意见" | [`references/reviewing-skills.md`](references/reviewing-skills.md) |
| 跑评测取证据（触发率、有/无技能对照） | [`references/running-evals.md`](references/running-evals.md) |

## 共用原则（各分支都遵守）

- **单一事实源**：定义见 `references/writing-skills.md` §7。
- **技能必须自包含**：定义与检查见 `references/reviewing-skills.md` Step 7。
- **先删后加**：优先删，其次改，最后才加。
- **证据优先**：没有真实执行轨迹或对照证据的判断，只能标"待验证"，不能当结论。
- **输出面向人**：复审结论与改进建议用**白话 + why**讲给用户听（为什么会出问题、为什么这么改），不许只丢术语或 `file:line`；详见 `references/reviewing-skills.md` Step 8。
- **实现 → 必审（取证）**：改完技能文件**不等于完成**——必须跑一轮复审并产出 `findings.json`（轻量改动跑秒级门，行为改动加 eval），然后**停在呈现**等用户决定。详见 `references/lifecycle.md` 阶段 2 → 3。

## 资源

只列路由表未覆盖的（其余见上表）：

- `references/subagents.md` — 复审外派子 agent 的角色与窄 brief（executor / grader / spec-reviewer / analyzer / comparator）、派发 vs 内联。
- `scripts/` — 纯标准库 CLI：脚手架、校验、评测集生成与选优、跑 agent 检测触发、聚合 benchmark、需求跟踪、跑 REQ 可执行验收检查（`run_checks.py`）、渲染报告；`selftest.py` 是脚本自测（冒烟 / 契约，成功 + 失败路径）。各脚本 `--help` 有简述 / 参数 / 示例 / 退出码。
- `assets/report-template.html` — HTML 报告模板（内联样式、无外部资源）。
- `commands/` — opencode 斜杠命令模板（`shy-grill` / `shy-review` / `shy-apply` / `shy-next`）；复制到 `~/.config/opencode/commands/` 生效，说明见 `lifecycle.md` 的「斜杠快捷」。
- `scripts/__pycache__/` — 跑脚本时自动生成，**不进技能内容**；复制部署时排除（仓库 `.gitignore` 已忽略）。

## 范围外

不负责被开发技能的具体领域实现；只负责技能开发全流程的规范：逼问、需求、实现、复审、评测与迭代。
