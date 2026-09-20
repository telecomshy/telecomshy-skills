# 调研：Agent Skill 的目录结构最佳实践

> **问题**：用 shy-skill-suite 开发一个新技能时，应该给用户创建怎样的**目录骨架**？要覆盖两层：① 单个技能包（skill package）的标准结构；② 技能开发项目（development project）的结构。
> **方法**：先读本机已装 `skill-creator` 与本仓库两个既有技能作为实例，再抓一手来源（Agent Skills 开放标准、Anthropic 工程博客、Claude Code 官方文档、`agentskills.io` 的 skill-creation / client-implementation 系列）逐条取证；每个结论附出处。
> **来源政策**：优先"拥有该主张的一手来源"（标准持有者 `agentskills/agentskills`、Anthropic、客户端官方文档）。查不到的写「未找到一手依据」，**不编**。
> **调研日期**：2026-09-20。
> **限制**：`opencode.ai/docs/skills/` 本次返回 Transport error，未能直接取回；opencode 侧只引用本仓库 `writing-skills.md` 的记录，并明确标注。`docs.claude.com/.../agent-skills/overview` 与 `platform.claude.com/.../agent-skills/overview` 对本网络区域不可用（返回 region 页），改用 `code.claude.com/docs/en/skills`。

---

## 0. 结论摘要

1. **技能包的最小结构只有一个文件**：一个目录 + 一个 `SKILL.md`。`scripts/`、`references/`、`assets/` 都是**可选**，目录内**允许任意额外文件/子目录**。（出处：`agentskills.io/specification`。）
2. **`SKILL.md` 的 frontmatter 只有两个字段必需**：`name`（≤64，小写字母/数字/连字符，无首尾或连续连字符，**须与父目录同名**）与 `description`（1–1024 字符）。`license` / `compatibility` / `metadata` / `allowed-tools` 可选；`allowed-tools` 标注为实验性。（出处：同上；`skill-creator/SKILL.md`。）
3. **可选目录各有明确职责**：`references/` 放按需加载的文档、`scripts/` 放可执行代码、`assets/` 放模板/图片/数据。（出处：`agentskills.io/specification`；`skill-creator/SKILL.md:75-84`。）
4. **`evals/` 与 `agents/` 不在标准目录清单里**，但两处一手来源把评测集放在**技能目录内**的 `evals/evals.json`；`agents/` 只见于 `skill-creator`（放外派子 agent 的指令）。（出处：`skill-creator/SKILL.md:145,461-465`；`agentskills.io/skill-creation/evaluating-skills`。）
5. **开发项目的骨架**由两处一手来源给出：技能包放在 `<project>/.<client>/skills/` 或跨客户端的 `<project>/.agents/skills/`（用户级为 `~/.<client>/skills/`、`~/.agents/skills/`）；评测/迭代产物放**技能目录同级**的 `<skill>-workspace/iteration-N/`。（出处：`agentskills.io/client-implementation/adding-skills-support`；`skill-creator/SKILL.md:167`；`agentskills.io/skill-creation/evaluating-skills`。）
6. **本仓库在此之上加了"需求 / 调研 / 台账"层**：`skills/<name>/`、`docs/<name>/requirements/REQ-NNNN-*.md`、`docs/<name>/research/`、`docs/<name>/glossary.md`、`docs/<name>/cleanup.md`，以及被 gitignore 的 `<name>-workspace/`。**这一层没有一手来源**——它是本仓库自己的约定（`AGENTS.md`、`writing-requirements.md`、`lifecycle.md`）。

---

## 1. 技能包（skill package）标准结构

### 1.1 必需：`SKILL.md`

规范原文：技能是"一个至少含 `SKILL.md` 的目录"。（出处：`agentskills.io/specification`，owner：`agentskills/agentskills`。）

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories
```

`skill-creator` 的 "Anatomy of a Skill" 给出同一张图，并明确 `SKILL.md` 必需、其余为 "Bundled Resources (optional)"。（出处：`C:\Users\admin\.agents\skills\skill-creator\SKILL.md:75-84`。）

**文件名大小写精确**：本仓库 `validate_skill.py:9,107-109` 强制 `SKILL.md` 精确大写；`agentskills.io/client-implementation/adding-skills-support` 也要求"文件名为**恰好** `SKILL.md`"。

### 1.2 `SKILL.md` frontmatter 字段

规范原表（出处：`agentskills.io/specification#frontmatter`）：

| 字段 | 必需 | 约束 |
| --- | --- | --- |
| `name` | **是** | ≤64 字符；仅小写字母/数字/连字符；不以 `-` 开头/结尾；不含连续 `--`；**须与父目录同名** |
| `description` | **是** | 1–1024 字符；非空；说清"做什么 + 何时用" |
| `license` | 否 | 许可名或随附许可文件 |
| `compatibility` | 否 | ≤500 字符；环境要求（产品 / 系统依赖 / 网络等） |
| `metadata` | 否 | 字符串→字符串的映射；客户端可存自定义属性 |
| `allowed-tools` | 否 | 空格分隔的预批准工具串；**实验性**，各实现支持不一 |

正文（frontmatter 之后）**无格式限制**；规范建议的分节是**分步指令 / 输入输出示例 / 常见边界**，并要求"agent 激活后会加载整个文件，长内容应拆到被引用文件"。（出处：同上。）

**最小可用示例**（规范原文）：

```markdown
---
name: skill-name
description: A description of what this skill does and when to use it.
---
```

`skill-creator` 补充：`compatibility` "optional, rarely needed"；`name` 是技能标识、`description` 是**唯一触发机制**（"when to use" 信息只放 `description`，不放正文）。（出处：`skill-creator/SKILL.md:62-69`。）

### 1.3 可选目录：`references/` / `scripts/` / `assets/`

规范对三者的定义（出处：`agentskills.io/specification#optional-directories`）：

- **`scripts/`** — 可执行代码。要求：自包含或明确声明依赖；有帮助的错误信息；优雅处理边界。语言取决于客户端实现（常见 Python / Bash / JS）。
- **`references/`** — 按需加载的文档。示例命名：`REFERENCE.md`（详细技术参考）、`FORMS.md`（表单模板/结构化数据）、领域文件（`finance.md` / `legal.md`）。要求**单个文件保持聚焦**——按需加载，文件越小越省上下文。
- **`assets/`** — 静态资源：模板（文档/配置模板）、图片（图、例）、数据文件（查找表、schema）。

`skill-creator` 的措辞一致：`scripts/` "Executable code for deterministic/repetitive tasks"、`references/` "Docs loaded into context as needed"、`assets/` "Files used in output (templates, icons, fonts)"。（出处：`skill-creator/SKILL.md:81-83`。）

`using-scripts` 补充脚本的**调用约定**：脚本从 `SKILL.md` 用**相对技能根的路径**引用（agent 自动解析，无需绝对路径），并在 `SKILL.md` 里列出"Available scripts"。（出处：`agentskills.io/skill-creation/using-scripts#referencing-scripts-from-skill-md`。）

### 1.4 其它目录：哪些是标准、哪些是工作流/客户端约定

规范在目录清单里写的是 `...`（"Any additional files or directories"），所以下列目录**不违反标准**，但都**不在标准枚举里**：

| 目录 | 性质 | 放什么 | 出处 |
| --- | --- | --- | --- |
| `evals/` | **去 facto 约定**（两处一手来源，未进 spec 目录清单） | `evals/evals.json`：触发/行为评测用例（prompt + expected_output + assertions） | `skill-creator/SKILL.md:145`；`agentskills.io/skill-creation/evaluating-skills`（"Store test cases in `evals/evals.json` inside your skill directory"） |
| `agents/` | `skill-creator` 独有 | 外派子 agent 的指令（`grader.md` / `comparator.md` / `analyzer.md`） | `skill-creator/SKILL.md:461-465` |
| `commands/` | **客户端约定** | 斜杠命令模板；Claude Code 已把 commands 合并进 skills，opencode 用 `~/.config/opencode/commands/<name>.md` | `code.claude.com/docs/en/skills`（"Custom commands have been merged into skills"）；本仓库 `writing-skills.md:19`、`skills/shy-skill-suite/commands/` |

本仓库 `knowledge-distill` 与 `shy-skill-suite` 都带 `evals/`（`evals/evals.json` + `evals/effectiveness.json`），`shy-skill-suite` 还带 `commands/`（`shy-grill` / `shy-review` / `shy-eval` / `shy-reqs`）与 `assets/`。**这些是实例，不是标准要求。**

> 注意：`evals/` 在标准里并非"技能包的一部分"，而是**开发期产物**。本仓库 `running-evals.md:77` 明确"评测集留在技能里（`evals/evals.json` 相对技能根）——行为结论要可复现，评测集就不能只躺在被 gitignore 的工作区里"。这是本仓库的取舍。

### 1.5 命名规则

- **技能目录名 / `name`**：小写字母、数字、连字符；≤64；无首尾或连续连字符；**`name` 必须等于父目录名**。（出处：`agentskills.io/specification#name-field`。）
- **`references/` 文件名**：规范未强制；示例用全大写（`REFERENCE.md`）或领域小写（`finance.md`）。
- **`scripts/` 文件名**：规范未强制。
- **`evals/` 文件名**：`evals.json`（评测集）、`effectiveness.json`（行为轴用例，本仓库扩展）；工作区里另有 `grading.json` / `timing.json` / `benchmark.json`，均由脚本产出、非手写。（出处：`skill-creator/references/schemas.md`；`running-evals.md:59-77`。）

### 1.6 渐进披露与文件引用（决定"放哪、拆不拆"）

三级加载（出处：`agentskills.io/specification#progressive-disclosure`；`agentskills.io/client-implementation/adding-skills-support` 量化）：

| 级 | 加载内容 | 时机 | token |
| --- | --- | --- | --- |
| 1 目录 | `name` + `description` | 会话启动 | 每技能约 **50–100 tokens** |
| 2 指令 | 完整 `SKILL.md` 正文 | 技能被激活 | **<5000 tokens（推荐）** |
| 3 资源 | `scripts/` / `references/` / `assets/` | 指令引用到时 | 视文件而定 |

文件引用规则（出处：`agentskills.io/specification#file-references`）：**用相对技能根的路径**；**引用保持一层深**（"Keep file references one level deep from `SKILL.md`. Avoid deeply nested reference chains."）。规范要求主文件 `<500 行`，超了就把详细材料移进 `references/`。

---

## 2. 开发项目（development project）骨架

### 2.1 一手来源对"技能放哪 / 工作区在哪"的建议

**(a) 技能目录的加载位置**（出处：`agentskills.io/client-implementation/adding-skills-support#where-to-scan`）：

| 作用域 | 路径 | 用途 |
| --- | --- | --- |
| Project | `<project>/.<your-client>/skills/` | 客户端原生位置 |
| Project | `<project>/.agents/skills/` | **跨客户端互通** |
| User | `~/.<your-client>/skills/` | 客户端原生位置 |
| User | `~/.agents/skills/` | **跨客户端互通** |

原文："The `.agents/skills/` paths have emerged as a widely-adopted convention for cross-client skill sharing."

Claude Code 的位置表（出处：`code.claude.com/docs/en/skills#where-skills-live`）：`~/.claude/skills/<name>/SKILL.md`（个人）、`.claude/skills/<name>/SKILL.md`（项目）、`<plugin>/skills/<name>/SKILL.md`（插件），以及企业级托管目录。

**(b) 评测/迭代工作区**（出处：`skill-creator/SKILL.md:167`）："Put results in `<skill-name>-workspace/` as a sibling to the skill directory."（**与技能目录同级**。）

`agentskills.io/skill-creation/evaluating-skills#workspace-structure` 给出完整布局：

```
csv-analyzer/                       # 技能目录
├── SKILL.md
└── evals/
    └── evals.json
csv-analyzer-workspace/             # 工作区（与技能目录同级）
└── iteration-1/
    ├── eval-top-months-chart/
    │   ├── with_skill/
    │   │   ├── outputs/            # 运行产出的文件
    │   │   ├── timing.json         # token 与耗时
    │   │   └── grading.json        # 断言结果
    │   └── without_skill/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    ├── eval-clean-missing-emails/
    │   └── ...
    └── benchmark.json              # 聚合统计
```

原文强调："The main file you author by hand is `evals/evals.json`. The other JSON files ... are produced during the eval process."（手写的是评测集，其余是生成物。）

### 2.2 本项目实际约定

本仓库在 2.1 之上，加了**需求 / 调研 / 台账**三层（全部为本仓库自定，见 `AGENTS.md` 与 `skills/shy-skill-suite/references/`）：

| 产物 | 位置 | 出处 |
| --- | --- | --- |
| 技能包 | `skills/<name>/` | `README.md:27-42`、`AGENTS.md` |
| 需求文档（活文档） | `docs/<name>/requirements/REQ-NNNN-<slug>.md` | `AGENTS.md`；`writing-requirements.md:23-27` |
| 领域词表 | `docs/<name>/glossary.md` | `writing-requirements.md:24` |
| 调研报告 | `docs/<name>/research/` | `AGENTS.md` |
| 卫生项台账 | `docs/<name>/cleanup.md` | `writing-requirements.md:88` |
| 设计笔记 | `docs/<name>/design/`（实例：`docs/shy-skill-suite/design/`） | 仓库实例（无规范条文） |
| 评测/复审工作区 | `<name>-workspace/iteration-N/`（**不入库**） | `lifecycle.md:11-12`；`running-evals.md:34-53`；`.gitignore`（`*-workspace/`） |
| REQ 总览报告 | `reports/`（**不入库**） | `.gitignore`（`reports/`） |

**两条关键的仓库纪律**（都源自 `AGENTS.md`）：

- 技能**必须自包含**：技能文件内只引用技能自身（相对技能根），**不引用仓库级 `docs/`**——因为技能会被单独复制到 `~/.config/TeleAgent/skills/` 部署，`docs/` 不随行。
- 报告落位：调研报告一律进 `docs/<skill>/research/`。

### 2.3 本项目 vs 一手来源的对照

- **一致**：技能包结构与标准一致（`SKILL.md` + 可选 `scripts/` / `references/` / `assets/`）；工作区与技能目录同级、按 `iteration-N/` 分轮，和 `skill-creator` / `evaluating-skills` 一致。
- **差异 1 · 技能存放位置**：本仓库用 `skills/<name>/` 作为**源码仓**里的位置，部署时复制到 `~/.config/TeleAgent/skills/`（`README.md:50-53`）；一手标准建议跨客户端用 `.agents/skills/`。本仓库**不采用** `.agents/skills/`。
- **差异 2 · 需求层**：`docs/<name>/requirements/` 这套 REQ 活文档**没有任何一手来源**，是本仓库自创。
- **差异 3 · 技能目录禁 README**：本仓库 `validate_skill.py:116-117` 规定技能目录内不得有 `README.md`（README 只放仓库根）。标准无此条——这是仓库卫生规则。

---

## 3. 推荐骨架清单（可直接落成脚手架）

> 下面把"标准要求"与"本仓库约定"分开标注：`[标准]` = 一手来源要求/建议；`[仓库]` = 本仓库自定；`[可选]` = 按需创建。

### 3.1 开发项目根（本仓库布局）

```
<project-root>/
├── AGENTS.md                      [仓库] 面向 agent 的仓库约定（目录约定、自包含规则）
├── README.md                      [仓库] 面向人的仓库说明 + 技能列表
├── LICENSE
├── .gitignore                     [仓库] 忽略 *-workspace/、reports/、__pycache__ 等
├── skills/                        [标准/仓库] 技能包源码目录（部署时整包复制）
│   └── <name>/
│       ├── SKILL.md
│       ├── scripts/               [可选]
│       ├── references/            [可选]
│       ├── assets/                [可选]
│       ├── evals/                 [可选] 随技能入库的评测集
│       └── commands/              [可选] 客户端斜杠命令模板（非标准）
├── docs/                          [仓库] 人类文档（不随技能部署）
│   └── <name>/
│       ├── requirements/          [仓库] REQ-NNNN-<slug>.md 活文档
│       ├── research/              [仓库] 调研报告
│       ├── glossary.md            [可选][仓库] 领域词表
│       ├── cleanup.md             [可选][仓库] 卫生项台账
│       └── design/                [可选][仓库] 设计笔记
├── <name>-workspace/              [标准][生成物，gitignore] 评测/复审工作区
│   └── iteration-1/
│       ├── eval-<id>/{with_skill,baseline}/{outputs,grading.json,timing.json}
│       ├── eval_metadata.json
│       ├── analyzer_notes.json
│       └── benchmark.json / benchmark.md / report.html
└── reports/                       [仓库][生成物，gitignore] REQ 总览报告
```

### 3.2 单个技能包（标准结构）

```
<name>/
├── SKILL.md          必需。frontmatter(name+description) + 正文指令；正文 <500 行 / <5k token
├── references/       可选。按需加载的文档；单文件聚焦、引用一层深
├── scripts/          可选。可执行代码；自包含或声明依赖、非交互、--help、结构化输出
├── assets/           可选。模板 / 图片 / 数据文件
├── evals/            可选（本仓库/去 facto）。evals.json 起手评测集；effectiveness.json 行为轴用例
└── commands/         可选（客户端约定）。斜杠命令模板；复制到客户端 commands 目录才生效
```

### 3.3 脚手架落地建议

- **起手只建 `SKILL.md`**：本仓库 `scripts/scaffold_skill.py` 的设计就是"只生成 `SKILL.md`，不建子目录、不生成需求文档"，子目录按需增量创建。（出处：`scaffold_skill.py:1-11,69`；`lifecycle.md:69`。）
- **`SKILL.md` 最小 frontmatter**：只写 `name` + `description`；`compatibility` 只在真有环境要求时加。
- **子目录出现时机**：正文逼近 500 行 → 拆 `references/`；出现重复脚本逻辑 → 拆 `scripts/`；需要输出模板 → 拆 `assets/`；要回归评测 → 建 `evals/`。（出处：`agentskills.io/specification`；`skill-creator/SKILL.md:96-98`；`best-practices#structure-large-skills-with-progressive-disclosure`。）

---

## 4. 争议 / 未找到一手依据

| # | 条目 | 状态 |
| --- | --- | --- |
| 1 | `evals/` 是否算"技能包的一部分" | **标准目录清单未枚举**；两处一手来源（`skill-creator`、`evaluating-skills`）都把评测集放技能目录内的 `evals/evals.json`。属**去 facto 约定**，非 spec 要求。 |
| 2 | `agents/` 目录 | **仅见于 `skill-creator`**，标准无、其它一手来源未见。属该技能自身的工作流约定。 |
| 3 | `commands/` 目录 | **客户端约定**，标准无。Claude Code 已把 commands 并入 skills；opencode 用独立 commands 目录。跨客户端不可移植。 |
| 4 | `docs/<name>/requirements/` + `REQ-NNNN` 活文档 | **未找到一手依据**。本仓库自创（`writing-requirements.md`）。 |
| 5 | `docs/<name>/glossary.md` / `cleanup.md` / `design/` | **未找到一手依据**。本仓库自创。 |
| 6 | 技能目录内禁 `README.md` | **标准无此条**；本仓库 `validate_skill.py:116-117` 自定。 |
| 7 | 跨客户端位置 `.agents/skills/` vs 本仓库 `~/.config/TeleAgent/skills/` | 一手标准推荐 `.agents/skills/` 作跨客户端互通；本仓库部署目标是 TeleAgent 私有目录，**未采用**该约定。 |
| 8 | `name_cn` / `description_cn` / `create_source` 等 frontmatter 字段 | **不在标准 6 字段内**；本仓库 `validate_skill.py:29-31` 把它们列为"客户端扩展字段"放行。它们在其它客户端会被忽略/报错，**不可移植**。 |
| 9 | opencode 的 skills 加载路径与 frontmatter 认领范围 | 本次 `opencode.ai/docs/skills/` **未能取回**（Transport error）；只引用本仓库 `writing-skills.md:16-19` 的记录。**待以 opencode 官方文档复核**。 |
| 10 | `.claude/skills/` 之外的"祖先目录上溯扫描" | `adding-skills-support` 提到部分实现会扫描（含 git root、XDG），但属"部分实现"，非标准要求。 |
| 11 | 技能数量上限 / 每技能上下文预算的其它数字 | 一手标准只给"目录每技能约 50–100 tokens"，**未给数量上限**。（本仓库既有调研 `skill-development-best-practices.md:286` 已记同结论。） |

---

## 5. 来源清单

### 5.1 一手（拥有该主张）

| # | 来源 | 归属方 | URL / 路径 | 访问日 | 用途 |
| --- | --- | --- | --- | --- | --- |
| P1 | Agent Skills 规范 | `agentskills/agentskills`（Anthropic 起草并作为开放标准发布） | `https://agentskills.io/specification` | 2026-09-20 | 目录结构、frontmatter、可选目录、渐进披露、文件引用 |
| P2 | Agent Skills 概览 | 同上 | `https://agentskills.io/home.md` | 2026-09-20 | 技能是"含 SKILL.md 的目录"、三级加载 |
| P3 | 技能创作最佳实践 | 同上 | `https://agentskills.io/skill-creation/best-practices.md` | 2026-09-20 | 渐进披露拆分、上下文预算、模板放 `assets/` |
| P4 | 在技能中使用脚本 | 同上 | `https://agentskills.io/skill-creation/using-scripts.md` | 2026-09-20 | 脚本引用用相对技能根路径、脚本设计 |
| P5 | 评测技能产出质量 | 同上 | `https://agentskills.io/skill-creation/evaluating-skills.md` | 2026-09-20 | `evals/evals.json`、`<skill>-workspace/iteration-N/` 布局 |
| P6 | 给 agent 加技能支持 | 同上 | `https://agentskills.io/client-implementation/adding-skills-support.md` | 2026-09-20 | 技能扫描位置（`.agents/skills/` 跨客户端约定）、`SKILL.md` 精确命名、目录 token 预算 |
| P7 | Claude Code 技能文档 | Anthropic（Claude Code） | `https://code.claude.com/docs/en/skills` | 2026-09-20 | 技能位置表、commands 合并进 skills、扩展 frontmatter |
| P8 | 工程博客《Equipping agents for the real world with Agent Skills》 | Anthropic | `https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills` | 2026-09-20（发布 2025-10-16） | 技能 anatomy、渐进披露三级、代码执行 |

### 5.2 本机文件（一手，本仓库/本机实例）

| # | 来源 | 路径 | 用途 |
| --- | --- | --- | --- |
| L1 | `skill-creator` 技能 | `C:\Users\admin\.agents\skills\skill-creator\SKILL.md` | Anatomy（`:75-84`）、`evals/evals.json`（`:145`）、`<skill>-workspace/`（`:167`）、`agents/` 目录（`:461-465`） |
| L2 | `skill-creator` JSON schema | `C:\Users\admin\.agents\skills\skill-creator\references\schemas.md` | `evals.json` / `grading.json` / `benchmark.json` 字段 |
| L3 | 仓库约定 | `AGENTS.md`、`README.md` | `skills/<name>/`、`docs/<skill>/{research,requirements}/`、技能自包含 |
| L4 | 需求文档规范 | `skills/shy-skill-suite/references/writing-requirements.md` | `docs/<skill>/requirements/REQ-NNNN-<slug>.md`、glossary/cleanup 位置 |
| L5 | 生命周期 | `skills/shy-skill-suite/references/lifecycle.md` | 产物表（需求/技能文件/findings/评测证据） |
| L6 | 评测规范 | `skills/shy-skill-suite/references/running-evals.md` | 工作区布局、评测集留在技能内 |
| L7 | 写作规范 | `skills/shy-skill-suite/references/writing-skills.md` | 调用方式、opencode command 路线（`:16-19`） |
| L8 | 脚手架脚本 | `skills/shy-skill-suite/scripts/scaffold_skill.py` | 起手只建 `SKILL.md` |
| L9 | 校验脚本 | `skills/shy-skill-suite/scripts/validate_skill.py` | frontmatter 白名单（含客户端扩展字段）、禁 README、相对引用检查 |
| L10 | 实例技能 | `skills/shy-skill-suite/`、`skills/knowledge-distill/` | 实际用了哪些目录/文件（`scripts/` / `references/` / `assets/` / `evals/` / `commands/`） |
| L11 | 忽略规则 | `.gitignore` | `*-workspace/`、`reports/` 不入库 |

### 5.3 未能取回（明确标注）

| # | 来源 | URL | 状态 |
| --- | --- | --- | --- |
| S1 | opencode 技能文档 | `https://opencode.ai/docs/skills/` | **Transport error**；opencode 侧结论仅引 L7，待复核 |
| S2 | Claude Developer Platform Agent Skills | `https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview` | 区域不可用；改用 P7 |
| S3 | 旧域名 Agent Skills 文档 | `https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview` | 区域不可用；改用 P7 |

---

## 6. 一句话总结

**技能包的最小结构是"一个目录 + 一个 `SKILL.md`"**，`scripts/` / `references/` / `assets/` 按需加；**开发项目的骨架是"技能包 + 同级 `<skill>-workspace/`"**（一手来源）；本仓库在此之上加了 `docs/<name>/{requirements,research,glossary,cleanup}` 这套需求/调研层——它**没有一手来源**，是本仓库自己的约定，落脚手架时应与本仓库既有 `AGENTS.md` 保持一致。
