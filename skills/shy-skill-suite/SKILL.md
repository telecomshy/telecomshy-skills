---
name: shy-skill-suite
description: 技能开发套件：面向「技能」这一产物的开发全流程操作规范。当你在逼问 / 澄清某个技能该做什么、新建或修改一个技能（含搭骨架 / 脚手架）、为技能写需求文档（REQ-NNNN 命名 / 结构 / 验收标准）、调触发描述（description）与触发精度、复审某个技能（触发可靠性、行为有效性、结构预算、脚本与安全）、写或改技能的 SKILL.md、校验技能结构（含是否该拆分）、或推进技能开发的迭代闭环并回写需求时使用。
compatibility: 需要 Python ≥ 3.7（仅标准库，实测 3.12）。scripts/ 只在校验、评测、需求跟踪、生成报告时用到；Python 版本过低时跳过脚本，按 references/ 的规范手工执行。
metadata:
  name_cn: 技能开发套件
  description_cn: 技能全流程操作规范：写技能需求文档，以及生成/改写后复审技能、提出改进并迭代。
  create_source: super-agent-skill-creator
---

# 技能开发套件

覆盖一个技能的**开发生命周期**：逼问 → 落需求 → **实现**（静默门 → 回写 → 停）；**评审**由用户主动触发（报告 → 分拣 → 单次实施 → 停）。各分支按用户意图进入对应规范文件。

## 分支路由

| 用户意图 | 进入 |
| --- | --- |
| 开发 / 迭代一个技能的闭环 | [`references/lifecycle.md`](references/lifecycle.md) |
| 逼问需求 / 拷问一个技能该做什么（含给既有技能回溯意图） | [`references/grilling.md`](references/grilling.md) |
| 怎么写技能 / `SKILL.md` 怎么写 / 把技能写对 | [`references/writing-skills.md`](references/writing-skills.md) |
| 只写 / 改需求文档；"写需求""需求文档""这个改动要做什么" | [`references/writing-requirements.md`](references/writing-requirements.md) |
| 只做复审；"评估这个技能""检查技能""触发准不准""提改进意见" | [`references/reviewing-skills.md`](references/reviewing-skills.md) |
| 跑评测取证据（触发率、有/无技能对照）；"评测""跑一下触发率""这次只测不审" | [`references/running-evals.md`](references/running-evals.md) |

## 共用原则（各分支都遵守）

- **单一事实源**：定义见 `references/writing-skills.md` §7。
- **技能必须自包含**：定义与检查见 `references/reviewing-skills.md` Step 7。
- **先删后加**：见 `references/reviewing-skills.md` §1。
- **证据优先**：没有真实执行轨迹或对照证据的判断，只能标"待验证"，不能当结论。
- **输出面向人**：报告三字段（存在问题 / 白话解释 / 修改建议）与白话写作规则见 `references/reviewing-skills.md` Step 8；用词以 `references/glossary.md` 为准。
- **实现 / 评审 / 评测三路分离**：实现完只跑 **Gate**（绿了报完成、红了才说），**不自动评审**；**评审由用户触发**，出报告后**分拣**（立即修 / 以后修 / 丢弃），按所选实施一次即停；**评测独立**（`/shy-skill-eval`，仅用户按需触发），复审默认静态、有指纹匹配的 eval 才引用。详见 `references/lifecycle.md`。
- **复审按需多跑**：委派子代理前一次性问清三件事——**说明多跑能提质量且只针对「剪枝 + 有效性内容发现」**、**跑几轮（建议 3 轮，用户不表态则走单轮）**、**子代理模型（默认＝主代理模型）**；触发轴 / 安全轴单跑；**必配独立裁判**（盲评，共识优先、独报标「需复核」）；**不读** `shy-models.md`、不新增自有配置文件。详见 `references/reviewing-skills.md` 的「成本闸门 · 按需多跑」。

## 资源

只列路由表未覆盖的（其余见上表）：

- `references/glossary.md` — 套件自身词汇（术语 / 一行白话 / `_避免_`）；解释与报告的用词准绳。
- `references/subagents.md` — 复审外派子 agent 的角色与窄 brief（executor / grader / spec-reviewer / analyzer / comparator）、派发 vs 内联。
- `scripts/` — 纯标准库 CLI；接口见各脚本 `--help`，评测脚本清单与指纹见 `references/running-evals.md`；Gate 用 `validate_skill.py` + `run_checks.py` + `selftest.py`。
- `assets/report-template.html` — HTML 报告模板（内联样式、无外部资源）。**默认静态只读**；分拣控件只在 `--serve`（本机临时服务）下出现，末尾「提交给 agent」写 `triage.json`。
- `commands/` — opencode 斜杠命令模板（`shy-skill-start` / `shy-skill-grill` / `shy-skill-review` / `shy-skill-eval` / `shy-skill-reqs`）；复制到 `~/.config/opencode/commands/` 生效，说明见 `references/lifecycle.md` 的「斜杠快捷」。其中 `/shy-skill-start [<skill>]` 为**开始开发新技能**入口（逼问 → 落需求 → 起骨架，同一流程，技能名可选）；`/shy-skill-reqs <skill>` 为**单技能** REQ 报告（按 kind → status 分组、可折叠）。
- `evals/evals.json` — 随技能入库的起手触发评测集（复现触发结论用，见 `references/running-evals.md`）。
- `evals/effectiveness.json` — 随技能入库的行为轴对照用例集（with_skill vs baseline，任务式 prompt + 断言，见 `references/running-evals.md`）。

## 范围外

不负责被开发技能的具体领域实现；只负责技能开发全流程的规范：逼问、需求、实现、复审、评测与迭代。
