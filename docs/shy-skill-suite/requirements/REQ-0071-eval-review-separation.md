---
id: REQ-0071
title: 评测与复审分离（独立 /shy-eval + 证据指纹时效 + 复审降级）
skill: shy-skill-suite
status: done
kind: refactor
iteration: 2
created: 2026-09-20
updated: 2026-09-20
blocked_by: []
related: [REQ-0046, REQ-0067, REQ-0069]
---

# REQ-0071 评测与复审分离

## 问题与目标

**现状（事实核对）**：eval 被钉成复审的执行层——`running-evals.md:1` 标题即「运行评测（复审的执行层）」，`lifecycle.md:25` 写明「`/shy-review` 已含评测……故不单列 `/shy-eval`」，`commands/shy-review.md:1` 描述为「复审 + 评测」；复审的**完成判据**又强制要求触发率 / with-baseline delta 证据（`reviewing-skills.md:56/71/112`）。于是**只要触发 review 就要跑分钟级 eval**（REQ-0067 实测全量约 7 分钟）。

**内部矛盾（可证伪）**：`lifecycle.md:83` 说 eval「只在真需要时跑；日常轻改动不必」，`reviewing-skills.md:56/71/112` 又要求 review 不收工除非有 eval 证据。两条并存 = 事实上的「每次 review 必跑 eval」。且 `lifecycle.md:83` 与 `reviewing-skills.md:99` 的「里程碑 / 收敛点」给 agent 留了**自行触发 eval** 的口子。

**证据时效缺口（可证伪）**：`scripts/` 无任何 hash / 指纹 / 版本机制（grep 无命中）；`iteration-N` 只是目录编号。review 无法判断手上的 eval 数据测的是不是**当前技能版本**——「eval → 改功能 → review」会把**过期证据**当本轮证据。

**目标**：
1. eval 升为**独立、user-invoked** 的取证路径；review 不再强制绑 eval，缺证据**显式降级**。
2. 引入**技能指纹**判「本轮证据」，杜绝过期证据被引用。
3. eval **仅用户按需触发**，agent 不得自行触发（可建议）。

## 触发与分支

- `/shy-eval`：用户显式要跑评测取证据（触发率 / 有效性对照）。
- `/shy-review`：用户要复审找问题；默认静态，同目录存在**指纹匹配**的 eval 才引用。
- 用户说「评测太贵 / 不该每次都跑 / 证据过期 / 这次只审不测」。

## 行为与步骤

1. **新增独立入口 `/shy-eval`（user-invoked 命令）**：`/shy-eval <skill> [触发|有效性|两者]`，默认**两者**；内部调 `optimize_description.py` / `run_effectiveness.py`；**必须钉模型**（沿用 `running-evals.md` 硬要求）；产物落 `<skill>-workspace/iteration-N/`；渲染并打开 eval 报告。与 `/shy-review` **互不调用**。
2. **证据指纹（分轴）**：eval 跑完在 `iteration-N/` 写证据元数据（如 `evidence.json`）：
   - 触发指纹 = `hash(description)`；
   - 有效性指纹 = `hash(SKILL.md + references/ + scripts/ + assets/ + evals/effectiveness.json)`；
   - 同时记录所用模型 ID 与时间。
   粒度理由：改 `SKILL.md` 不作废触发证据，改 `description` 才作废。
3. **review 默认静态 + 按指纹引用**：
   - Step 1 / Step 2 默认做**静态审查**（description 措辞 / 硬约束 / 边界 / 指令是否买行为改变），触发率与 delta 结论一律标「（静态）待验证」。
   - 同技能 workspace 存在 eval 且**指纹匹配当前技能** → 可引用为该轴证据，报告标注证据来源。
   - 指纹**不匹配**（技能自 eval 后已改）→ 标「过期证据（技能已变更）」、行为轴降级，并**可**产出「待验证 + 建议跑 `/shy-eval`」的 finding——把「该取证」显式交给用户，不自己静默跑。
   - 完成判据去掉「必须有 delta 证据」的硬要求，改为「有证据则引用、无则显式标（静态）/ 过期」。
4. **eval 触发权收口**：仅用户按需触发；删除 `lifecycle.md:83` / `reviewing-skills.md:99` 的「里程碑 / 收敛点自动跑」表述，改写为「用户可选的取证时机（推荐点）」。
5. **术语边界**：`glossary.md` 加「评测（eval）」（独立取证据，只产触发率 / delta，不改技能、不提修复建议；`_避免_`：测试、跑分）与「复审（review）」（找问题 + 提建议，证据可选）；降级词「（静态）」「过期证据」。
6. **编号与留存**：保留单一 `iteration-N`（谁跑谁 +1、脚本兼容）；过期证据**不删**、留旧目录供追溯；review 按指纹挑最近一次匹配项。
7. `run_checks.py` 注册本 REQ 检查。

## 脚本与资源

- 新增 `commands/shy-eval.md`。
- 改 `commands/shy-review.md`（描述去掉「评测」或改「按需引用评测」）。
- 改 `references/lifecycle.md`（斜杠快捷表 + 阶段 3 + 完成判据）、`references/reviewing-skills.md`（Step 1/2/3 完成判据 + Step 8 报告降级条）、`references/running-evals.md`（新增「独立路径」与「指纹」节、命令）、`references/glossary.md`、`SKILL.md`（路由表加 eval 行）。
- 改 `scripts/`：指纹实现（`skill_utils.py` 加函数，或新增 `skill_fingerprint.py` CLI `--skill-dir <dir> --axis trigger|effectiveness`）；`agent_runner.py` / `optimize_description.py` / `run_effectiveness.py` / `aggregate_benchmark.py` 写证据元数据（含指纹 + 模型 ID）。
- 改 `scripts/run_checks.py`（注册 `req0071-*`）。

## 降级与边界

- **无指纹的旧证据 → 视为过期**（保守）。
- 分离**不改变 eval 的耗时本质**，只是把它移出 review 的强制路径。
- **`converged` 不受影响**：`run_checks.py:1075` 为 `status == "ok"`（机械判，与 eval 无关，已核）。
- 指纹对**任何**技能文件改动都敏感（有效性轴），会作废证据；这是刻意的保守取向，可后续按需放宽。
- 不做 eval 的自动改写环 / 自动重跑；不自动排期。

## 验收标准

- [x] `commands/shy-eval.md` 存在，含加载技能 + `$ARGUMENTS` + 参数说明（触发 / 有效性 / 两者） — `check:req0071-eval-command`
- [x] `references/glossary.md` 含「评测（eval）」「复审（review）」两条定义 + `_避免_`，含降级词「（静态）」「过期证据」 — `check:req0071-glossary-boundary`
- [x] `references/lifecycle.md` 斜杠快捷表含 `/shy-eval`，且**不再**出现「里程碑 / 收敛点」作为 eval 自动触发 — `check:req0071-no-auto-eval`
- [x] `references/reviewing-skills.md` Step 1/2/3 完成判据不再硬性要求触发率 / delta 证据，改为「有证据则引用、无则标（静态）待验证」 — `check:req0071-review-completion`
- [x] 指纹函数分轴存在：触发 = `hash(description)`、有效性 = `hash(SKILL.md + references + scripts + assets + evals/effectiveness.json)` — `check:req0071-fingerprint`
- [x] eval 跑完在 `iteration-N/` 写证据元数据（含指纹 + 模型 ID） — `check:req0071-evidence-meta`（自测造最小目录断言）
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`；`selftest.py` 退出码 0 — `check:skill-validate-ok` / `check:skill-selftest`
- [x] （语义）review 报告在「无指纹匹配 eval」时显示降级条、在匹配时标注证据来源；由复审时人工判读 — 已落 `reviewing-skills.md` Step 8「证据来源与降级条」+ Step 1/2/3 完成判据；复审时按此判读
- [x] （语义）`/shy-review` 命令描述不再声称「复审 + 评测」 — 已改为「复审（按需引用评测）」
- [x] （语义）用户触发 `/shy-eval` 能真跑出带指纹的触发率 / with-baseline delta 证据；由一次真跑 + 人工判读判定 — 机制已端到端（桩命令）验证：`optimize_description`/`run_effectiveness` → `evidence.json`（指纹 + 模型）→ `aggregate_benchmark` → `render_report`；**真跑**待用户在配好 `opencode` 模型的环境执行（本机无 `opencode` CLI）

## 范围外

- 不做 eval 的自动改写环 / 自动重跑 / 自动排期（与 REQ-0046 一致）。
- 不改三轴划分与 P0/P1/P2 定义。
- 不改 eval 脚本的并发 / 超时 / 检测等执行层参数（属 REQ-0067）。
- 不做实时 HTML 报告。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-20 | 落需求（未实现）：逼问 3 轮定下 eval 独立化、指纹时效、review 降级、仅用户触发 | — | 待实现 |
| 2 | 2026-09-20 | 实现：新增 `commands/shy-eval.md`（独立取证、钉模型、与 `/shy-review` 互不调用）；`skill_utils.py` 加分轴确定性指纹 + `merge_evidence`；新增 `skill_fingerprint.py` CLI；4 个 eval 脚本写 `evidence.json`（指纹 + 模型 + 时间）；`running-evals.md`/`lifecycle.md`/`reviewing-skills.md`/`glossary.md`/`SKILL.md`/`shy-review.md` 落「独立路径 + 指纹 + 静态降级」；`run_checks.py` 注册 6 条 `req0071-*` | `validate_skill.py` → ok；`run_checks.py` 44/44 通过（含 6 条 req0071）；`selftest.py` 31/31 通过 | 全绿、无 P0/P1 → done；真跑模型待用户环境（无 `opencode` CLI） |

## 备注 / 待办

逼问：已过 3 轮——设计树 frontier：Q1–Q4（问题定性 / 入口形态 / review 依赖 / eval 频率）→ I1–I3（指纹时效 / 粒度 / 编号）+ E–H（产物 / 术语 / review 默认 / 命令接口）→ Q4′（仅用户按需触发）；用户逐轮确认「按推荐」。

- 来源：2026-09-20 用户提案「eval 测评和审核是在一起的，两者目的不完全一样；eval 每次跑脚本很耗时，迭代时跑没必要」。
- 关联：`REQ-0046`（实现 / 评审两路分离）的延续——本次把「评测」也从评审路里分出去。
