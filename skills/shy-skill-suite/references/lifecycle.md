# 技能开发生命周期（迭代环）

把「逼问 → 落需求 → **实现**（静默门 → 回写 → 停）」与「**评审**（用户触发 → 报告 → 分拣 → 单次实施 → 停）」两条路串成闭环。skill-forge 有 eval 驱动的自动流水线，但**没有把评审结果按用户分拣回写需求**这一环——本文件补上它。

## 产物

| 产物 | 位置 | 角色 |
| --- | --- | --- |
| 需求文档 `REQ-NNNN` | `docs/<skill>/requirements/` | **活文档**、事实源：目标、验收、范围、迭代记录 |
| 技能文件 | `skills/<skill>/` | 被开发的产物（`SKILL.md` / `scripts/` / `references/` / `assets/`） |
| 复审 findings | `<skill>-workspace/.../findings.json`（+ 呈现报告） | 结构化：带轴与优先级 P0/P1/P2；schema 见 `reviewing-skills.md` |
| 评测证据 | `<skill>-workspace/iteration-N/` | with_skill vs baseline 的 delta + `evidence.json`（两轴指纹 + 模型 + 时间，见 `running-evals.md`） |

## 斜杠快捷（opencode）

本套件是 model-invoked；"必须人工触发"的动作走 opencode command（模板在 `commands/`，复制到 `~/.config/opencode/commands/` 后生效）：

| 命令 | 进入 |
| --- | --- |
| `/shy-start [<skill>]` | **开始开发新技能**：逼问 → 落需求 → 起骨架（**同一流程**；技能名可选，缺则先问用户）。入口见 `commands/shy-start.md` |
| `/shy-grill` | 逼问一个技能该做什么（`grilling.md`） |
| `/shy-review` | 触发**评审路**：三轴复审、**按需引用**指纹匹配的评测，出报告供分拣（`reviewing-skills.md`） |
| `/shy-eval` | 独立**评测取证**：触发率 / with_skill vs baseline 对照，写指纹证据、渲染报告（`running-evals.md`） |
| `/shy-reqs` | 单技能 REQ 报告：按类型（kind）→ 状态（status）分组、可折叠，产出可展开 HTML（`track_requirements.py --view overview --skill <skill>` / `render_reqs.py --skill <skill>`） |

**评测（eval）与复审（review）分离**：eval 是**独立、user-invoked** 的取证路径（`/shy-eval`），只产触发率 / delta、不改技能、不提修复建议；复审默认静态，仅当同技能工作区存在**指纹匹配当前技能**的 eval 才引用（见 `running-evals.md`）。**实现路径不会自动进入评审，评审也不自动跑 eval。**

## 七个阶段

### 0 · 逼问（grill）

把模糊想法逼成明确需求。机制（设计树 + frontier）、要问透的项、三个动作（术语规范化 / 场景压测 / 与实现核对）、完成判据与"可跳过"规则，见 [`grilling.md`](grilling.md)。

### 1 · 落需求（REQ）

按 `writing-requirements.md` 落盘。**先判逼问**（决策缺口在谁那里）：

| 谁提的 | 动作 |
| --- | --- |
| 用户提需求、但没说全（目标 / 触发说法 / 验收证据有缺） | **逼问**（`grilling.md`：设计树 + frontier，每问附建议答案），问到能写验收 |
| 用户提需求、已给全 | 跳过，在 REQ 备注记 `逼问：跳过（依据：…）` |
| agent 提（复审 findings / 分析建议） | **不逼问**：提案自带 问题与目标 / 范围外 / 验收 / 备选与默认；用户做「做 / 不做 / 换方案」 |
| agent 提案含**真实分叉且无合理默认** | **只就分叉问一次**（mini-grill），不全量逼问 |

无论逼问与否，REQ 的「备注 / 待办」都要留一行 `逼问：已过 / 跳过（依据：…）`。

**大改动拆增量**：

- 每个增量是一次**可独立验收的行为变化**（不是"写完 `SKILL.md`"这类层级切片）。
- 一个增量应能在一个上下文窗口内完成，且能单独演示 / 验证。
- 声明**阻塞关系**：用 `blocked_by` 指向必须先 `done` 的前置 REQ。若一个增量依赖另一个，就把它们拆成多个 REQ 并连边，而不是塞进一个文件。
- **大重构走 expand–contract**：先让新分支与新表述和旧的并存（expand）→ 分批切换，每批一个增量 → 旧分支无引用后删除（contract）。任何一步都不该让技能"半坏"。
- 小改动就是一个增量，不必拆。

**要不要拆成套件？** 只有满足其一才升 Tier 3/4（orchestrator + 子技能，或再加 `agents/`）：子流程有**独立触发词**、需要并行或子 agent、需要对外发布。否则停在 Tier 1/2——没人手动调用、无独立触发、一个上下文窗口装得下，就不拆。

- 正例：`knowledge-distill` 有 6 个分支仍是一个技能（同一 `description` 触发、共享上下文）。
- 反例：一个技能要按**互不相关的用户或触发词**走两条工作流时，才考虑拆。

**完成判据**：待开发的 REQ 已达 `status: ready`——验收标准逐条可端到端验证、范围外已写、`blocked_by` 已连边（或显式为空）、迭代记录有第 1 行、**备注有逼问记录（已过 / 跳过 + 依据）**。

### 2 · 实现（实现路）

生成 / 改写技能文件，按增量推进。

**两条路从这里分开**：本阶段是**实现路**——用户说"做 X"，你把它做出来，然后**报完成、停下**。

动笔时按 [`writing-skills.md`](writing-skills.md) 的 lever 写（description 作指针、信息层级与按需披露、leading word、剪枝、完成判据……）。

新建技能时用 `python "<SKILL_DIR>/scripts/scaffold_skill.py" <name> --description "<触发描述>"` 起骨架——**轻量，只生成 `SKILL.md`**（不建子目录、不生成 REQ），内容靠后续迭代补。加 `--project` 则一次建齐**开发层**：技能包 + `docs/<name>/requirements/`（目录）+ 追加 `.gitignore` 条目（`*-workspace/` / `reports/` / `__pycache__/`，**仅缺失时**追加）——**仍不预建** `scripts/` / `references/` / `assets/` / `evals/` / `commands/` 空目录、**不写 REQ 正文**（REQ 由阶段 1 产生）。入口 `/shy-start`。

实现收尾跑一次 **Gate（静默秒级门）**：`validate_skill.py <skill_dir>` + `run_checks.py --root . --skill <skill>` + `selftest.py`（末尾给出 `（episode）` / 迁移债 / 台账 open 计数）。**静默 = 绿了就报"完成"、红了才说**；不产 findings、不出报告、**不自动进评审**。

**完成判据**：`validate_skill.py <skill_dir>` → `status: ok`；该增量每条验收标准都能指出证据（命令输出 / 文件 / 计数），无一条标「待验证」；**Gate 通过**；**做减法前已查引用**——删 / 隐藏对外呈现或检查（按钮 / 字段 / 显示 / `check`）前，已检索技能文件与 `run_checks.py` 注册表、确认无规则 / 检查仍要求它；**改行为的涟漪已付清**——受影响的契约文本（旧 REQ 的验收 / 技能文档）已当轮订正，新行为已有回归检查。**实现完成 = 交付合格，不要求"审过一轮"。**

### 3 · 评审（评审路，用户主动触发）

**只在用户明确要求时进入**（"帮我评审 / 检查一下 / 跑个复审"、`/shy-review`）。**实现路不会自动进这里。**

> 本阶段即 **Discovery**——**低频、对抗式**，触发点**只有两个**：**真实失败**（任务做砸 / 真 bug）/ **用户显式要求**。**不是"每次改动都跑"**——那是 **Gate**（阶段 2 的静默门）的活。改动一律先过 Gate；Discovery 是额外的、偶尔的"找新问题"。**真实失败时不自动进入**：报告并建议评审，进不进入由用户决定。

按 `reviewing-skills.md` 执行**完整三轴**（行为轴：触发 + 有效性；需求轴：Spec——**先跑 `run_checks.py`，只有 `（语义）` 项才逐条读**；标准轴：结构 / 脚本 / 安全）。**复审默认静态**：行为轴的触发率与 delta 结论一律标「（静态）待验证」；同技能工作区存在**指纹匹配当前技能**的 eval 才引用为证据，指纹不匹配则标「过期证据（技能已变更）」。

**取证时机由用户选**：跑 eval 是分钟级的独立动作，只在用户显式触发 `/shy-eval`（或用户说"这次也测"）时发生；复审可以**建议**取证，但**不自行静默跑**。日常轻改动不必取证。

**评审收尾 = 报告 + 分拣**（这是评审路的终点）：

1. 产出 `findings.json` + **HTML 报告并打开**（`running-evals.md`）；报告前 **Step 8 由主 agent 把台账机械项当轮结清**（子代理只发现、禁写，见 `reviewing-skills.md` Step 8）。
2. **逐条**请用户分拣（**不做批量**）——`--serve` 报告页内逐条勾选（默认立即修），末尾点「提交给 agent」；静态报告只读、不能勾选；也可直接在对话里答：
   - **立即修** → 在本轮实施（见阶段 4）。
   - **以后修** → 落盘成 `ready` 的 REQ（进 frontier）。
   - **丢弃** → **不落盘、不留痕**。
3. **用户确认分拣后**，按所选**实施一次**，再跑 Gate，**结束**——**不自动再审、不自动进入下一轮**。

> 评审只在用户要求时发生；一次评审的实施只针对用户勾选的那批，**不会自我繁殖，也不会自己重开一轮评审**。

### 4 · 回写需求

**实现路**：机械记账**自动做**（勾验收 / 追加迭代记录 / `status: done`）——静默门绿就回写，不必停下等人。

**评审路**：按阶段 3 的**分拣结果**回写——「立即修」的项实施后勾选 / 记迭代；「以后修」的落盘为 `ready` 的新 REQ；「丢弃」的**不落盘、不留痕**。回写内容：

- 已满足的验收项 → 勾选 `- [x]`。
- 未满足 / 新发现（仅「立即修」「以后修」）→ 转成新的验收标准，或新开一份 REQ。
- 范围变化 → 更新「范围外」。
- 追加一条**迭代记录**（格式见 `writing-requirements.md`）。
- `status`：全部验收过且无 P0/P1 → `done`；仍有下一轮 → `in-progress`；`iteration` 加一、`updated` 改为当天。
- **整份被取代**：加 `superseded_by: REQ-NNNN`（定义见 `writing-requirements.md` §3）——取代关系必须落字段，不能只写在备注散文里（那是"假 `done`"的成因）。

**完成判据**：每条验收项已勾选或转成新 REQ；迭代记录新增一行；`status` / `iteration` / `updated` 已更新；改完后 `python "<SKILL_DIR>/scripts/track_requirements.py" --root .` 仍 `status: ok`（REQ 仍可解析、`blocked_by` 无悬空）。

### 5 · 下一轮（用户驱动，不自动推进）

**没有自动回环**：实现完停下、评审完也停下。要推进时，从 frontier 取下一个——`python "<SKILL_DIR>/scripts/track_requirements.py" --root .` 列出现在能开始的 REQ（`blocked_by` 全部 `done`），按依赖顺序做；**何时开始由用户决定**。评审里「以后修」的项已进 frontier，会在那时被取到。

**收工判据**（评审路实施后 / 判断技能是否收敛时用）：

- `run_checks.py` 全部 `check:` 项通过；`（行为）` / `（语义）` / `（未定）` 项判定完毕；`（episode）` 不读；
- 无 P0/P1（**P2 不阻断**；"文档 / 措辞自洽"类进 `cleanup.md` 台账，见 `reviewing-skills.md` Step 8）；
- **迁移债达标**（`state.json` 的 `debt_targets`）；`converged` 由 `run_checks.py` **机械算出**（定义见 `glossary.md`），**不由 agent 自证**；
- 对照 delta 稳定，或再做也不见有意义的改进（过约束时**做减法**，见 `reviewing-skills.md` §3）。

### 6 · 复盘（retro）

改的是**套件 / 环境**本身（模板、指针、脚本、检查项），不是被开发的技能。只在被开发的技能已收敛、或观察到套件本身反复导致问题时做。

**完成判据**：复盘改动每一处已落到 REQ 或 `cleanup.md`（无悬空）；改完过 Gate（见阶段 2 的三件套），且 `python "<SKILL_DIR>/scripts/track_requirements.py" --root .` 仍 `status: ok`。

## 一句话

需求是**活文档**：用户确认落盘后，每轮评审按用户的分拣回写它（阶段 3 → 4）。**实现 / 评审 / 评测三路分离**——实现完停下、评审由用户触发、评测另由 `/shy-eval` 按需取证；技能与需求一起演进，而不是需求写完就冻结。
