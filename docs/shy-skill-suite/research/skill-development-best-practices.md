# 调研：技能开发最佳实践（基于一手来源的综合）

> **后续进展（2026-09-17 补记）**：本报告写后技能已变更——新增**可执行验收标准**（`scripts/run_checks.py` + REQ 里 `check:` / `（行为）` / `（语义）` 三类标记）、「P2 不阻断」停止规则，以及 grader 兼评评测集（含恒过/恒败）/ 抽取隐式主张、analyzer notes 落地。本报告 §6.1/§6.2 的部分候选（如评测结果模式分析）已落地。现状见 `REQ-0030` 迭代记录与 `skills/shy-skill-suite/references/`。

> 范围：对「agent 技能」这一产物（含 `SKILL.md` + 可选 `scripts/` / `references/` / `assets/`，由 coding agent 按需加载）做一次**面向一手来源**的最佳实践综合，覆盖：技能是什么 / 渐进披露 / frontmatter 与触发 / 指令 vs 脚本 vs 参考 / 评测与迭代 / 上下文预算 / 分发与可移植 / 失败模式 / 平台差异。
> 方法：先读本仓库既有调研（`docs/shy-skill-suite/research/skill-creator.md`、`skill-forge.md`）与 `skills/shy-skill-suite/` 全部文本，划清"已覆盖"边界；再抓取一手来源逐条取证；最后对 `shy-skill-suite` 侧跑证伪命令（命令与结果内联于 §6）。**不重复** sibling 报告已点名的部分（`.skill` 打包、description 100–200 词、>300 行加 TOC、grader 兼评评测集），只指路（§7）。
> 来源政策：**只采用拥有该主张的一手来源**（Anthropic 官方文档与工程博客、Agent Skills 开放标准、Claude Code / opencode / OpenAI Codex 的官方文档或官方仓库源码）。二手/第三方来源（如 `AgriciDaniel/skill-forge`）只在有冲突时用作对照，并明确标注。
> 调研日期（access date）：**2026-09-17**。本机为 win32 / PowerShell 7，无 `rg`；所有命中统计用 `Select-String`，命令与结果见 §6。
> 限制：`developers.openai.com/codex/skills` 与 `platform.claude.com/.../agent-skills` 对本网络返回 403，其内容未能直接取回；Codex 侧改用 **`openai/codex` 官方仓库源码与官方示例技能**取证（一手），并在来源表注明。`docs.claude.com` 旧域名的 Agent Skills 页面改用 `code.claude.com/docs/en/skills`（Claude Code 官方文档）取回。

---

## 0. 结论速览（TL;DR）

1. **今天真正"拥有"技能规范的一手来源只有一处**：Agent Skills 开放标准（`agentskills.io`，Anthropic 起草、2025-12 作为开放标准发布，规范仓库 `agentskills/agentskills`；代码 Apache-2.0、文档 CC-BY-4.0）。Anthropic 的工程博客与 Claude Code / opencode / OpenAI Codex 文档是**客户端侧**的一手来源，各自扩展标准。
2. **三条强共识**（所有一手来源一致）：① **渐进披露三级**（metadata → `SKILL.md` 正文 → 资源，按需加载）；② **`description` 是唯一触发指针**（正文只在命中后进上下文）；③ **评测必须有 with-skill vs baseline 对照**，单跑不算证据。
3. **写作层的最佳实践本仓库几乎已全覆盖**：`<500 行 / <5k token`、description 祈使句/pushy/near-miss、剪枝、校准、gotchas、plan-validate-execute、脚本非交互与结构化输出——均在 `skills/shy-skill-suite/references/` 有对应条文（见 §3 各节 `file:line`）。
4. **缺口集中在两处**：① **分发 / 跨客户端**（开放标准推荐的 `.agents/skills/` 约定、平台字段差异矩阵）；② **评测结果的模式分析**（删/查"恒过/恒败"断言）。这两处本仓库 0 命中（§6 证伪 01–05）。
5. **一手来源之间确有分歧**：触发阈值（标准默认 0.5 vs 第三方 90%/5%）、frontmatter 可移植范围（标准 6 字段 vs Claude Code 追加约 13 个扩展字段 vs opencode 只认 5 个 vs Codex 另有 `agents/openai.yaml`）、自动触发机制（多数靠模型判断，Codex 另加**词法选择器**）。见 §4。
6. **候选淘汰数：24 个候选，10 个通过（4 可直接吸收 + 6 需改造），14 个被证伪**（10 个"本仓库已有/更强"、4 个"客户端专属或范围外"）。

---

## 1. 事实基础：技能是什么、怎么加载

### 1.1 定义与目录结构（一手：开放标准）

规范原文：技能是"一个至少含 `SKILL.md` 的目录"，可选 `scripts/`（可执行代码）、`references/`（按需加载的文档）、`assets/`（模板/图片/数据）。（来源：`agentskills.io/specification`，owner：agentskills/agentskills，2026-09-17 访问。）

Anthropic 工程博客用"给新员工写 onboarding guide"作类比，并给出首个真实例子（PDF 技能：`SKILL.md` 指向 `reference.md` 与 `forms.md`）。（来源：`anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills`，2025-10-16。）

### 1.2 渐进披露三级（一手：标准 + 博客 + 客户端实现指南）

开放标准把它拆成三阶段，并给了**量化 token 预算**：

| 级 | 加载内容 | 加载时机 | token 成本（一手原文） |
| --- | --- | --- | --- |
| 1 目录 | `name` + `description` | 会话启动 | 每技能约 **50–100 tokens** |
| 2 指令 | 完整 `SKILL.md` 正文 | 技能被激活 | **< 5000 tokens（推荐）** |
| 3 资源 | `scripts/` / `references/` / `assets/` | 指令引用到时 | 视文件而定 |

（来源：`agentskills.io/specification#progressive-disclosure`、`agentskills.io/client-implementation/adding-skills-support`。）

Blog 的表述是：元数据第一级、`SKILL.md` 正文第二级、被引用的附加文件"第三级及以后"；并指出"有文件系统与代码执行工具的 agent 不需要把整个技能读进上下文，因此技能能携带的上下文实际上是**无界的**"。（来源：Anthropic 工程博客。）

**本仓库现状**：`writing-skills.md:20-24` 已写"信息层级与按需披露"，要求只在部分分支需要的参考下放到 `references/` 并给"何时加载"的指针；主文件目标 `< 500 行 / < 5k token`（`writing-skills.md:23`）。`reviewing-skills.md:97-101`（Step 4）按同一套 lever 复审。**已实现**。

### 1.3 `SKILL.md` 的 anatomy（一手：标准 spec）

frontmatter 字段与约束（原文表格）：

| 字段 | 必需 | 约束 |
| --- | --- | --- |
| `name` | 是 | ≤64 字符；仅小写字母/数字/连字符；不以 `-` 开头或结尾；不含连续 `--`；**须与父目录同名** |
| `description` | 是 | **1–1024 字符**；非空；描述做什么 + 何时用 |
| `license` | 否 | 许可名或随附许可文件 |
| `compatibility` | 否 | ≤500 字符；环境要求（产品、系统依赖、网络等） |
| `metadata` | 否 | 字符串→字符串的映射；客户端可存自定义属性 |
| `allowed-tools` | 否 | 空格分隔的预批准工具串；**实验性**，各实现支持不一 |

正文无格式限制；规范建议的正文分节是 **分步指令 / 输入输出示例 / 常见边界**；并明确"agent 激活后会加载整个文件，故长内容应拆分到被引用文件中"。（来源：`agentskills.io/specification`。）

**本仓库现状**：`validate_skill.py:5-8,28-30` 的字段白名单 = `{name, description, license, compatibility, metadata, allowed-tools}` ∪ `{disable-model-invocation, argument-hint}`，并检查 `name` 与目录同名、kebab-case、≤64，`description` ≤1024；`writing-skills.md:10` 同。**已实现且更严**（额外查悬空引用、README 禁止、YAML 危险写法）。

---

## 2. 事实基础：触发（description 是唯一杠杆）

### 2.1 description 的写法（一手：优化描述指南）

一手指南给出四条原则（原文）：**用祈使句**（"Use this skill when..." 而非 "This skill does..."）；**聚焦用户意图而非实现机制**；**宁可 pushy**（显式列出适用场景，包括用户不直接点名域的情况）；**保持简洁**（几段到一小段，硬限 1024 字符）。（来源：`agentskills.io/skill-creation/optimizing-descriptions`。）

一个重要的机制细节（原文）："agents typically only consult skills for tasks that require knowledge or capabilities beyond what they can handle alone"——简单一步请求（如"read this PDF"）即使描述完全匹配也可能不触发。（同上。）

**本仓库现状**：`writing-skills.md:7-10`（祈使句、聚焦用户意图、一分支一触发、宁可 pushy、≤1024）；`reviewing-skills.md:43-54`（Step 1 触发审查）。**已实现**。

### 2.2 触发评测集与阈值（一手：优化描述指南）

一手指南的具体做法：

- **约 20 条查询**：8–10 条 should-trigger + 8–10 条 should-not-trigger。
- should-trigger 要在**措辞 / 显式度 / 细节量 / 复杂度**四轴变化；最有价值的是"技能有用但连接不显然"的查询。
- should-not-trigger 最有价值的是 **near-miss**（共享关键词/概念但任务不同）；明显无关（"写个斐波那契"、"今天天气"）"测不出任何东西"。
- **每条查询跑多次**（"3 is a reasonable starting point"），算 **trigger rate**；should-trigger 高于阈值即通过，**阈值 0.5 是合理默认**；should-not-trigger 反之。
- 真实性：带文件路径、个人背景、具体列名、口语/缩写/错别字。

（来源：`agentskills.io/skill-creation/optimizing-descriptions`。）

**本仓库现状**：`reviewing-skills.md:52` 要求"8–10 条 should-trigger 与 8–10 条 should-not-trigger（含 near-miss）各跑多次算触发率"，`:46` 强调 near-miss，`:54` 完成判据"触发率都过阈值（默认 0.5）"。`running-evals.md:9-12,56-63` 提供 `generate_eval_set.py` / `optimize_description.py` / `agent_runner.py`。**已实现**（本仓库另有标准未要求的真跑检测）。

### 2.3 防过拟合：train/validation 切分（一手：优化描述指南）

一手指南：切 **train ≈60% / validation ≈40%**，两层都要保持 should-trigger 与 should-not-trigger 的比例；**只用 train 的失败指导修改**，用 validation 判断是否泛化；**按 validation 通过率选最优轮**，并明确"最优的 description 可能不是最后产出的那个"；**通常 5 轮足够**；不要抄失败查询里的关键词（那是过拟合），要找它代表的类别；卡住时**换一种结构性的写法**而不是继续微调。（来源：`agentskills.io/skill-creation/optimizing-descriptions`。）

**本仓库现状**：`optimize_description.py:39` `train_ratio = 0.6`；`:173-190` 按 should_trigger 分层切分、`:181` 注释"改进建议只用 train 失败"、`:185-190` 按 `best_test_score` 保留较高 test 分（配 `--previous`）。`writing-skills`/`reviewing-skills.md:193` 有"泛化，别打补丁"。**已实现**。未落地的细节：明确的"5 轮上限"与"换结构性写法"提示（列入 §6 需改造 J）。

---

## 3. 事实基础：内容设计（指令 / 脚本 / 参考）

### 3.1 从真实专长出发（一手：best-practices）

一手指南点名的头号陷阱："asking an LLM to generate a skill without providing domain-specific context"→产出"handle errors appropriately"这类通用废话。两种取材法：**从一次真实任务里提取**（成功步骤、你做的纠正、输入输出格式、你提供的项目事实）；**从既有项目资产综合**（内部文档、runbook、API spec、code review 评论、版本历史里的 patch/fix、真实故障与修复）。（来源：`agentskills.io/skill-creation/best-practices`。）

值得单独引用的执行建议（原文）："Read agent execution traces, not just final outputs. If the agent wastes time on unproductive steps, common causes include instructions that are too vague..., instructions that don't apply to the current task..., or too many options presented without a clear default."（同上。）

**本仓库现状**：`reviewing-skills.md:64-65` 把它列为 Step 2 的检查项——"真实专长（AI 生成技能的头号风险）"与"gotcha 是否缺失"，并给出"整篇换成任何同类项目仍成立 = 通用废话"。**已实现**。

### 3.2 上下文花销：只写 agent 不知道的（一手：best-practices）

一手判据（原文）："Ask yourself about each piece of content: 'Would the agent get this wrong without this instruction?' If the answer is no, cut it."；并指出"过度全面的技能可能比不写更糟"（agent 抓不到重点、被不适用的指令带偏）；"Concise, stepwise guidance with a working example tends to outperform exhaustive documentation."（来源：`best-practices`。）

**本仓库现状**：`writing-skills.md §7 剪枝`（`writing-skills.md:38-43`）：cache / relevance·sediment / no-op，判据即"模型默认行为"；`reviewing-skills.md:62` Step 2 要求对每条指令追问"没有这句，agent 会做错吗？"。**已实现且更强**（本仓库额外有"先删后加"与单一事实源）。

### 3.3 校准控制力度（一手：best-practices）

一手指南：**按任务的脆弱度匹配具体度**——多解/容错处给自由并解释 why；脆弱/必须一致的处要 prescriptive（"Run exactly this sequence... Do not modify the command"）。三个模式：**给默认而非菜单**、**倾向 procedure 而非 declaration**（教一类问题的做法，而非某一个实例的答案）、**输出模板**是合理的"具体"例外。（来源：`best-practices`。）

**本仓库现状**：`writing-skills.md §9 校准`（`writing-skills.md:51-55`）逐条对应：写死 vs 解释 why、给默认而非菜单、教方法而非给答案（并明确"输出模板、格式约束这类'具体'是合理例外"）。**已实现**。

### 3.4 模式：gotchas / 模板 / 清单 / 验证回路 / plan-validate-execute / 固化脚本（一手：best-practices）

- **Gotchas**：一手称其为"许多技能里最高价值的内容"，必须是"反直觉的环境事实"（如软删除要 `WHERE deleted_at IS NULL`、同一 ID 三个服务三个叫法），并建议"agent 犯错被你纠正时，把纠正加进 gotchas"。（来源：`best-practices`。）
- **输出模板**：要 agent 产出特定格式时给模板比散文描述更可靠；短模板内联，长/条件性模板放 `assets/` 并由 `SKILL.md` 引用。（同上。）
- **Checklists**：显式清单帮 agent 跟踪进度、避免跳步，尤其步骤有依赖或验证门时。（同上。）
- **Validation loops**：do → run validator → fix → repeat until pass；参考文档也可充当 validator。（同上。）
- **Plan-validate-execute**：批量/破坏性操作先生成中间计划，用验证脚本对照 source of truth，再执行。（同上。）
- **Bundling reusable scripts**：若观察到 agent 每次都在重造同一段逻辑（画图、解析、校验），就写成脚本放进 `scripts/`。（同上；blog 亦述"code execution"的确定性与效率理由。）

**本仓库现状**：gotchas → `reviewing-skills.md:65`；模板 → `writing-skills.md:55`（作为"教方法"的合理例外）；验证回路与 plan→validate→execute → `writing-skills.md:49`；固化脚本 → `reviewing-skills.md:118`。**除"显式 checklist 进度清单"外均已实现**（checklist 列入 §6 需改造 H）。

### 3.5 代码该跑还是该读（一手：blog + 脚本指南）

Blog：某些操作"更适合传统代码执行"（排序用 token 生成远比跑算法贵），且"很多应用需要只有代码能提供的确定性可靠性"；并提醒"code can serve as both executable tools and as documentation. It should be clear whether Claude should run scripts directly or read them into context as reference."（来源：Anthropic 工程博客。）

脚本指南（一手）给出的 agentic 脚本设计要点：**避免交互式提示**（agent 在非交互 shell 里、会挂死）；**`--help` 是 agent 了解接口的主要途径**（简述 + flags + 示例）；**错误要可行动**（说清哪里错、期望什么、下一步试什么，而不是 `invalid input`）；**结构化输出**（JSON/CSV/TSV）；**数据走 stdout、诊断走 stderr**；**幂等**；**dry-run**；**有意义的退出码**；**安全默认**（`--confirm`/`--force`）；**输出规模可预测**（许多 harness 在约 **10–30K 字符**处截断，大输出应默认摘要并支持 `--offset` 或 `--output`）。（来源：`agentskills.io/skill-creation/using-scripts`。）

**本仓库现状**：`reviewing-skills.md:109-120` Step 6 逐条覆盖——非交互、`--help` 完整、错误可行动、结构化输出（数据 stdout / 诊断 stderr）、幂等、安全默认与输出规模（`--confirm`/`--force`、`--offset`/`--output`）、依赖与版本、该固化的逻辑。**已实现**。

### 3.6 脚本依赖与一次性命令（一手：脚本指南）

一手指南在"one-off commands"里给了明确做法：优先用 `uvx` / `pipx` / `npx` / `bunx` / `deno run` / `go run` 直接引用工具；**pin 版本**（`npx eslint@9.0.0`）让命令行为随时间稳定；**在 `SKILL.md` 里声明前置条件**，运行时级要求用 `compatibility` 字段。要复用逻辑时，可打包**自包含脚本**：Python 用 **PEP 723** 内联依赖（`# /// script`）配 `uv run`（或 `pipx run`），并可 `uv lock --script` 做可复现；Node 侧用 `npx pkg@ver` / Deno `npm:pkg@1.0.0` / Bun / Ruby `bundler/inline`。（来源：`agentskills.io/skill-creation/using-scripts`。）

**本仓库现状**：`reviewing-skills.md:117` 要求"脚本是否自包含或明确声明依赖、是否需要固定版本；技能是否需要 `compatibility` 声明运行前提"，但**没有** PEP 723 / `uv run` / pin 版本的具体落地法；全仓 grep `PEP 723|uvx|uv run|npx` **0 命中**（§6 证伪 02）。**缺口**（§6 可直接吸收 A）。

---

## 4. 共识 vs 分歧（一手来源之间对不上的地方）

> 规则：两边都列，并标明各自 owner。不替读者裁决。

### 分歧 1 · 触发阈值到底多少

- **一手（标准）**：should-trigger 的 trigger rate **高于 0.5 即通过**，"0.5 是合理默认"。（`agentskills.io/skill-creation/optimizing-descriptions`。）
- **第三方（skill-forge）**：`references/testing-guide.md:96-104` 给"触发准确率 90%+ / 误报 <5% / 完成率 95%+"。（`AgriciDaniel/skill-forge`，非标准持有者；仅二手对照。）
- **判断**：0.5 是**有 owner 的默认值**；90%/5% 在本仓库既有调研中已标为"更具体但无一手来源"（见 §8）。二者不必然矛盾（不同统计口径），但**不能把 90%/5% 当标准**。

### 分歧 2 · frontmatter 可移植范围

同一份 `SKILL.md` 在不同客户端可认字段不同：

| 客户端 | 认领字段（一手） | 来源 |
| --- | --- | --- |
| 开放标准 | `name` `description` `license` `compatibility` `metadata` `allowed-tools`(实验) | `agentskills.io/specification` |
| Claude Code | 标准字段 + **约 13 个扩展**：`when_to_use` `argument-hint` `arguments` `disable-model-invocation` `user-invocable` `allowed-tools` `disallowed-tools` `model` `effort` `context: fork` `agent` `background` `hooks` `paths`；且 `description`+`when_to_use` 在列表里**截断于 1536 字符** | `code.claude.com/docs/en/skills` |
| opencode | **只认 5 个**：`name`(必需) `description`(必需) `license` `compatibility` `metadata`；"Unknown frontmatter fields are ignored" | `opencode.ai/docs/skills/` |
| OpenAI Codex | `name`(≤64) `description`(必需) + `metadata.short-description`，另支持 **`agents/openai.yaml`** 描述界面（`display_name` / `icon` / `default_prompt`） | `openai/codex` 仓库源码与官方示例（见 §9） |

**判断**：标准"一份技能跨客户端"的说法成立，但**只有 5 个基础字段真正可移植**；扩展字段会被忽略（opencode）或按各自语义处理（Claude Code）。本仓库面向 opencode / TeleAgent，`writing-skills.md:16-18` 已正确指出"opencode 忽略 `disable-model-invocation`"。

### 分歧 3 · 技能是靠什么被"选中"的

- **多数一手实现**：靠模型读目录后自行判断（`client-implementation/adding-skills-support`："Most implementations rely on the model's own judgment as the activation mechanism, rather than implementing harness-side trigger matching or keyword detection."）。
- **但 OpenAI Codex 例外**：`codex-rs/ext/skills/src/dynamic_skill_selector.rs` 实现了多种**廉价的词法选择器**（fielded BM25、character n-gram、routing card、multi-query lexical 等），文档注释称其"Selects likely-relevant skills without changing the model-visible catalog"、可在每轮以 **shadow mode** 运行。
- **判断**：这是"描述里的具体关键词"为何仍重要的**一手反例**——存在检索式预选层时，`name`/`short_description`/`description` 会被当作检索文档。标准也要求 description"include specific keywords"（`specification#description-field`）。

### 分歧 4 · 评测的严格度

- **标准**：LLM grader 逐断言 PASS/FAIL + 证据；人工复核；两版比较建议 blind A/B。（`evaluating-skills`。）
- **本仓库**：额外要求 grader **盲**、不给 benefit of the doubt（`subagents.md:28`），comparator **两个顺序都跑**、且"盲测只是信号不是证据"（`subagents.md:50-53`），并把 Spec 轴与质量轴**分轴报告**（`reviewing-skills.md:17,148`）。
- **判断**：本仓库在评测纪律上**严于**一手标准；这不是需要追赶的缺口。

---

## 5. 反模式 / 失败模式（一手来源点名）

| # | 反模式 | 一手来源原话/要点 | 本仓库对应检查 |
| --- | --- | --- | --- |
| A1 | 让 LLM 凭空生成技能（无领域上下文） | "vague, generic procedures... rather than the specific API patterns"（best-practices） | `reviewing-skills.md:64`「真实专长」 |
| A2 | 过度全面的技能 | "can hurt more than they help"（best-practices） | `writing-skills.md §7`；`reviewing-skills.md:62` |
| A3 | 给菜单不给默认 | "too many options presented without a clear default"（best-practices） | `writing-skills.md:54` |
| A4 | 模糊、无完成判据的步骤 | 会诱发抢跑/提前收工（本仓库归纳） | `writing-skills.md:47-48` |
| A5 | 交互式脚本 | "will hang indefinitely"（using-scripts） | `reviewing-skills.md:111` |
| A6 | 弱断言 / 恒过断言 | "an assertion that passes but tests nothing is worse than none"（evaluating-skills 的 grader 元批评；本仓库 sibling 已记 skill-creator 版） | 本仓库 grader 只判断言，**不评断言集**（sibling 已列候选） |
| A7 | 用明显无关查询当负例 | "obviously irrelevant, tests nothing"（optimizing-descriptions） | `reviewing-skills.md:46` |
| A8 | 把失败查询的关键词抄进 description | "that's overfitting"（optimizing-descriptions） | `reviewing-skills.md:193` |
| A9 | 单跑无对照就宣称有效 | "只有 delta 才算证据，单跑不算"（本仓库；标准同：with/without） | `running-evals.md:101` |
| A10 | 从不可信来源装技能 | "install skills only from trusted sources... thoroughly audit it"（Anthropic 工程博客） | `reviewing-skills.md:124` |
| A11 | 静态打勾不跑 | "不看真实轨迹的复审，必然漏掉真正的失效"（本仓库归纳；标准："Read agent execution traces, not just final outputs"） | `reviewing-skills.md:203` |

---

## 6. 本仓库可吸收清单（三分）+ 证伪命令与结果

> 证伪方式：对每个候选先跑"能否推翻『本仓库已有该能力』"的命令，结果内联。命令均为 PowerShell `Select-String`，作用域 `skills/shy-skill-suite/`（排除 `__pycache__`）。**先写命令与结果，再给结论。**

```
# 统一证伪命令（在仓库根执行）
$files = Get-ChildItem -Recurse -File skills/shy-skill-suite -Exclude *.pyc
01  $files | Select-String -Pattern '\.agents/skills' -SimpleMatch          → 0
02  $files | Select-String -Pattern 'PEP 723|uvx|uv run|npx'               → 0
03  $files | Select-String -Pattern '恒过|恒败|always.pass|always.fail'    → 0
04  $files | Select-String -Pattern 'feedback\.json'                        → 0
05  $files | Select-String -Pattern 'Codex|when_to_use|1536|context: fork'  → 0
06  $files | Select-String -Pattern '--offset|--confirm|--force|dry-run'    → 8   （已覆盖）
07  $files | Select-String -Pattern 'train_ratio|0\.6'                      → 2   （已覆盖）
08  $files | Select-String -Pattern '0\.5'                                  → 2   （阈值已覆盖）
09  $files | Select-String -Pattern 'std|mean'                              → 63  （统计已覆盖）
```

### 6.1 可直接吸收（4）

| 候选 | 一手来源 | 为什么值得 | 证伪（命令 + 结果） |
| --- | --- | --- | --- |
| **A. 脚本依赖固定 / 自包含**（pin 版本；Python PEP 723 + `uv run`；`npx pkg@ver`） | `agentskills.io/skill-creation/using-scripts` | 本仓库脚本"纯标准库"目前成立，但一旦引入第三方（如画图、解析）没有版本约束就会漂移；一手来源给了可直接抄的落地格式 | 证伪 02 → **0 命中**（推翻"已有"失败，确认缺口） |
| **B. 评测结果模式分析：删/查恒过与恒败断言** | `agentskills.io/skill-creation/evaluating-skills#analyzing-patterns` | 本仓库 analyzer 只做"失败聚类、flaky、成本离群、TPR/FPR"（`subagents.md:40`），**没有**"恒过断言在两种配置都过 → 删""恒败 → 查断言本身或题目"这一步；而 sibling `skill-creator.md` 只落到 grader 的 `eval_feedback`，未落到 benchmark 分析 | 证伪 03 → **0 命中** |
| **C. 跨客户端分发：`.agents/skills/` 约定** | `agentskills.io/client-implementation/adding-skills-support` | 一手明言 `.agents/skills/` 是"widely-adopted convention for cross-client skill sharing"，其它合规客户端会自动可见；`AGENTS.md:21` 当前只部署到 `~/.config/TeleAgent/skills/`，跨客户端面窄 | 证伪 01 → **0 命中**（全仓无 `.agents/skills`） |
| **D. 平台差异矩阵（标准 / Claude Code / opencode / Codex）** | `code.claude.com/docs/en/skills` + `opencode.ai/docs/skills/` + `openai/codex` 源码 | 本仓库是"跨客户端部署的技能"，`writing-skills.md:16-18` 只写了 opencode 一条路线；Claude Code 的 `when_to_use`/1536 截断/`context: fork` 与 Codex 的 `agents/openai.yaml`、`metadata.short-description`、词法选择器**均无记录**；这会直接影响 description 与 frontmatter 的写法 | 证伪 05 → **0 命中** |

### 6.2 需改造后吸收（6）

| 候选 | 一手来源 | 改造点 | 证伪结果 |
| --- | --- | --- | --- |
| **F. 人工反馈的结构化回灌（`feedback.json`）** | `evaluating-skills#reviewing-results-with-a-human` | 一手把"人工反馈"作为迭代三类信号之一并落成逐用例文件；本仓库有**呈现门禁**（`lifecycle.md:64`）与 `findings.json`，但无"人工反馈→下一轮迭代输入"的结构化通道。改造：与 REQ-0019"不做服务器化反馈回写"的既定决策共存——只做**本地文件**（非 HTTP 回写），由人在报告后补写 | 证伪 04 → **0 命中** |
| **G. 输出模板（templates）强化** | `best-practices#templates-for-output-format` | 本仓库仅在 `writing-skills.md:55` 把模板列为"教方法"的例外，无"何时内联、何时放 `assets/`"的规则；可补一句"长模板/条件性模板放 `assets/` 并由 `SKILL.md` 引用" | 已有 `writing-skills.md:55`，**部分覆盖** |
| **H. Checklist 进度清单** | `best-practices#checklists-for-multi-step-workflows` | 本仓库用"每 step 完成判据"（`writing-skills.md:45-49`）替代；checklist 的价值是**跨步骤的连续进度**，可改造为在长流程技能里加一个 `- [ ]` 进度块 | 全仓 `checklist|清单` 仅命中"findings 清单"，**无进度清单模式** |
| **I. 迭代停止规则：5 轮上限 + 结构性改写** | `optimizing-descriptions#the-optimization-loop` | 本仓库已有 train/test 与按 test 选优，但未写"通常 5 轮足够""卡住就换结构性写法而非继续微调" | 证伪 07（train/test 已在）→ 仅缺停止规则 |
| **J. 描述关键词面向"检索式选择器"** | `openai/codex` `dynamic_skill_selector.rs` + `specification#description-field` | 共识是"聚焦用户意图"，但 Codex 的词法选择器说明**具体关键词**会被检索；可补一条"description 里保留可被检索的具体名词（文件格式、工具名、领域词），但不得抄失败查询" | 与 `writing-skills.md:7-10` 兼容，**需补** |
| **K. 目录 token 成本的量化** | `specification#progressive-disclosure`（每技能 50–100 tokens） | 本仓库已定性地写"每多一个技能就多一份常驻 description"（`writing-skills.md:60`），可补具体量级帮助决策"何时拆分" | 已有定性，缺量化 |

### 6.3 明确不吸收（4）

| 不吸收项 | 理由（含一手/本仓库依据） |
| --- | --- |
| **客户端职责类**：trust gating、context compaction 保护、activation 去重、permission allowlisting、技能目录 allowlist | 这些是"给 agent 加技能支持"的**客户端实现指南**（`client-implementation/adding-skills-support`）针对客户端作者的要求；`shy-skill-suite` 是技能、不是客户端，无落点 |
| **Claude 专属 frontmatter 机制**（`context: fork`、`hooks`、`model`、`effort`、`paths`、`background`） | 目标平台 opencode / TeleAgent 不认，且 `writing-skills.md:16-18` 已确立"用客户端 command 做人工入口"的 opencode 路线 |
| **HTTP 服务器 + 反馈回写 / 内嵌原始产出** | 本仓库 `REQ-0019` 已显式决策不做（sibling `skill-creator.md §4.3` 已列），本次不再重复 |
| **第三方数值阈值**（90% 触发准确率 / <5% 误报 / 95% 完成率 / 80% 错误恢复） | 仅见 `AgriciDaniel/skill-forge`（非标准持有者），且与一手标准的 0.5 默认冲突（§4 分歧 1）；无一手来源，不得当标准 |

### 6.4 被证伪：本仓库已有/更强（不重复吸收，10）与淘汰数

| 候选（来自一手） | 证伪依据（本仓库已实现） |
| --- | --- |
| 渐进披露三级 / 按需加载 | `writing-skills.md:20-24`；`reviewing-skills.md:97-101` |
| `SKILL.md < 500 行 / < 5k token` | `writing-skills.md:23` |
| frontmatter 约束（name≤64、desc≤1024 等） | `validate_skill.py:5-8,28-30`；`writing-skills.md:10` |
| description 祈使句/用户意图/pushy | `writing-skills.md:7-10`；`reviewing-skills.md:47` |
| 触发集 8–10 正 / 8–10 负 + near-miss + 0.5 阈值 | `reviewing-skills.md:46,52,54` |
| train/validation 60/40 + 按 validation 选优 | `optimize_description.py:39,181-190` |
| with-skill vs baseline + 干净上下文 + 旧版快照 | `running-evals.md:14-32`；`subagents.md:18-21` |
| grader 逐断言证据 / 盲 / 不给 benefit of the doubt | `subagents.md:26-28` |
| benchmark mean/std/min/max/delta | `aggregate_benchmark.py:92-103` |
| 脚本非交互 / `--help` / 结构化输出 / 幂等 / dry-run / `--offset`·`--confirm` | `reviewing-skills.md:109-120`；证伪 06 → 8 命中 |

**淘汰数：24 个候选，10 个通过（4 可直接吸收 + 6 需改造），14 个被证伪**（其中 10 个"本仓库已有/更强"，4 个"客户端专属或范围外"）。

---

## 7. 与既有调研的重叠（不重写，只指路）

- `.skill` 打包与发布、description 100–200 词目标、长 reference 加 TOC、grader 兼评评测集与抽取隐式主张、自动 description 改写环——**已在** `docs/shy-skill-suite/research/skill-creator.md`（§2.5/§2.7/§4.1）与 `skill-forge.md`（§2.6/§2.7/§2.9/§4.1/§4.2）覆盖，本报告不再列为候选。
- 三轴分离复审、需求活文档、先证伪再提建议、真跑触发检测——是本仓库相对对标物的**既定优势**，本报告只确认一手来源未与之冲突（§4 分歧 4）。
- `skill-forge` 的 `token_savings_ratio` 反向命名、review 双评分口径等坑——见 sibling `skill-forge.md §5`，与本报告 §9 的阈值分歧是两回事，别混。

---

## 8. 无一手来源的主张（单独列出，别混进正文）

> 以下均为"被广泛复述，但在拥有该主张的一手来源中未找到"的条目。本报告**不作为事实断言**。

| 主张 | 出处（仅见的来源） | 标注 |
| --- | --- | --- |
| 触发准确率 90%+ / 误报 <5% / 完成率 95%+ / 错误恢复 80%+ | `AgriciDaniel/skill-forge` `references/testing-guide.md:96-104`（第三方 OSS，非标准持有者） | **无一手来源**；与标准的 0.5 默认冲突（§4 分歧 1） |
| 技能会占用约 2% 上下文预算 | `AgriciDaniel/skill-forge` `references/skills-activation.md`（第三方）；Claude Code 官方页面取回部分未出现该数字 | **无一手来源** |
| 复合失败率 90%^5 ≈ 59%（"每步 90%，5 步累计 59%"） | `AgriciDaniel/skill-forge` `references/pro-agent.md:5-9`（第三方） | **无一手来源** |
| "技能数量应控制在 3–5 个" | 未在任何一手来源找到 | **无一手来源**（open 标准只说目录每技能约 50–100 tokens，未给数量上限） |

---

## 9. 来源清单（URL / 归属方 / access date / 一手 or 二手）

### 9.1 一手（拥有该主张）

| # | 来源 | 归属方（owner） | URL | access date | 说明 |
| --- | --- | --- | --- | --- | --- |
| P1 | Agent Skills 规范 | agentskills/agentskills（Anthropic 起草并作为开放标准发布） | `https://agentskills.io/specification` | 2026-09-17 | frontmatter、目录、渐进披露、文件引用 |
| P2 | Agent Skills 概览 | 同上 | `https://agentskills.io/`（`/home.md`） | 2026-09-17 | 三级加载、客户端展示 |
| P3 | 技能创作最佳实践 | 同上 | `https://agentskills.io/skill-creation/best-practices` | 2026-09-17 | 真实专长、上下文、校准、模式 |
| P4 | 优化技能 description | 同上 | `https://agentskills.io/skill-creation/optimizing-descriptions` | 2026-09-17 | 触发集、0.5 阈值、train/val 60/40 |
| P5 | 评测技能产出质量 | 同上 | `https://agentskills.io/skill-creation/evaluating-skills` | 2026-09-17 | 工作区、断言、grader、benchmark、模式分析、人评 |
| P6 | 在技能中使用脚本 | 同上 | `https://agentskills.io/skill-creation/using-scripts` | 2026-09-17 | one-off、PEP 723、脚本接口 |
| P7 | 给 agent 加技能支持 | 同上 | `https://agentskills.io/client-implementation/adding-skills-support` | 2026-09-17 | `.agents/skills`、信任、压缩保护 |
| P8 | 规范仓库 README | agentskills/agentskills | `https://github.com/agentskills/agentskills` | 2026-09-17 | 标准持有者、许可 |
| P9 | 工程博客《Equipping agents for the real world with Agent Skills》 | Anthropic | `https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills` | 2026-09-17（发布 2025-10-16） | anatomy、代码执行、评测建议、安全 |
| P10 | Claude Code 技能文档 | Anthropic（Claude Code） | `https://code.claude.com/docs/en/skills` | 2026-09-17 | 扩展 frontmatter、1536 截断、位置与优先级 |
| P11 | opencode 技能文档 | opencode（SST / Anomaly） | `https://opencode.ai/docs/skills/` | 2026-09-17 | 认领字段、name 正则、`<available_skills>`、权限 |
| P12 | Anthropic 示例技能仓库 | Anthropic | `https://github.com/anthropics/skills`（`template/SKILL.md`、`spec/agent-skills-spec.md`） | 2026-09-17 | 模板与"spec 已迁至 agentskills.io"；`license: null` |
| P13 | OpenAI Codex 仓库 | OpenAI | `https://github.com/openai/codex` | 2026-09-17 | 见 §9.1.1 具体文件 |

#### 9.1.1 从 P13 取证的具体文件（均为 openai/codex `main` 一手源码）

- `.codex/skills/code-review/SKILL.md` 等 —— 官方仓库内的真实技能（`name`/`description`/`metadata`）。
- `codex-rs/skills/src/assets/samples/openai-docs/SKILL.md` —— 官方示例技能，含 `metadata.short-description` 与"Do not use for..."负向触发。
- `codex-rs/skills/src/assets/samples/openai-docs/agents/openai.yaml` —— Codex 的 `interface`（`display_name`/`short_description`/`icon`/`default_prompt`）。
- `codex-rs/skills/src/parser.rs` —— `MAX_NAME_LEN = 64`、`description` 非空必需、`metadata.short-description`、容错式 frontmatter 修复。
- `codex-rs/ext/skills/src/loader/mod.rs` —— `SKILL.md`、`agents/openai.yaml`、`MAX_DESCRIPTION_LEN = 1024`、`MAX_SCAN_DEPTH = 6`、`MAX_SKILLS_DIRS_PER_ROOT = 2000`。
- `codex-rs/ext/skills/src/host_roots.rs` —— 扫描 `.agents/skills`、`$CODEX_HOME/skills`（repo/user 等 scope）。
- `codex-rs/ext/skills/src/dynamic_skill_selector.rs` —— 词法/BM25/n-gram 选择器，`CheapSkillSelector` trait。
- `docs/skills.md` —— 官方仓库把技能文档指向 `developers.openai.com/codex/skills`。

### 9.2 二手 / 未直接取回（明确标注）

| # | 来源 | 归属方 | URL | access date | 状态 |
| --- | --- | --- | --- | --- | --- |
| S1 | skill-forge | `AgriciDaniel`（第三方 OSS，非标准持有者） | `https://github.com/AgriciDaniel/skill-forge` | 2026-09-17（经本仓库 sibling `skill-forge.md` 的克隆记录） | **二手**；仅用于 §4 分歧 1 与 §8 对照 |
| S2 | OpenAI Codex 技能文档页 | OpenAI | `https://developers.openai.com/codex/skills` | 2026-09-17 | **未能直接取回**（403，curl / 代理 / archive 均失败）；改用其官方仓库源码取证（P13） |
| S3 | Claude Developer Platform Agent Skills | Anthropic | `https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview` | 2026-09-17 | **未能直接取回**（Transport error）；改用 `code.claude.com/docs/en/skills`（P10）与开放标准（P1） |
| S4 | `docs.claude.com/.../agent-skills/overview`（旧域名） | Anthropic | — | 2026-09-17 | 同上（Transport error） |

---

## 10. 一句话总结

一手来源对"技能开发"的共识是**渐进披露 + description 触发 + 对照式评测**；本仓库在**写作与评测纪律**上已达甚至超过一手标准，真正的空白在**跨客户端分发（`.agents/skills`）、平台差异矩阵、评测结果的恒过/恒败模式分析、脚本依赖固定**四处。**24 个候选，10 个通过（4 直接吸收 / 6 需改造），14 个被证伪。**
