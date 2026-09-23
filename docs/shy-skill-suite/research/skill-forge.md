# 对标调研：AgriciDaniel/skill-forge 与 shy-skill-suite 的功能对比

> **后续进展（2026-09-17 补记）**：本报告写后技能已变更——新增**可执行验收标准**（`scripts/run_checks.py` + REQ 里 `check:` / `（行为）` / `（语义）` 三类标记）、「P2 不阻断」停止规则，以及 grader 兼评评测集 / 抽取隐式主张、analyzer notes 落地（本报告 §4.1/§4.2 的部分候选已落地）。现状见 `REQ-0030` 迭代记录与 `skills/shy-skill-suite/references/reviewing-skills.md`。

> **源码复核（2026-09-20 补记）**：重克隆 `AgriciDaniel/skill-forge`（commit `2872ee9`，与 §0 锁定版本一致，未变），对**重叠功能的源码**逐行复核，结论全部成立并补充细节：
>
> - **`aggregate_benchmark.py` 的 `token_savings_ratio` 反义命名已实测确认**：`skill-forge/scripts/aggregate_benchmark.py:203-204` 用 `with_token_mean / baseline_token_mean` 却命名 `token_savings_ratio`——`>1` 表示带技能**多花** token。shy 侧已改名 `token_ratio` 并注明 `>1 = 多花`（`scripts/aggregate_benchmark.py:7,203`）。
> - **`thresholds_met` 只在文档、脚本确实不产出**：复核 `aggregate_benchmark.py:206-229` 的 `summary`，无此字段；「阈值门控」无程序化落地，靠 agent 手算。
> - **`validate_skill.py` 两套评分口径并存已实测**：脚本 flat 扣分（CRITICAL−20/HIGH−10/MEDIUM−5/LOW−2，`:291-305`）与 SKILL.md 加权 rubric（`:101-108`）不是一回事，同一技能会得到两个"健康分"。
> - **`optimize_description.py` 实为单轮已实测**：`for i in range(max_iterations)` 在 `:244-245` 无条件 `break`（注释自认"Claude iterates calling this script per round"）。
> - **`skill_utils.py` 复制而非复用已实测**：`validate_skill.py:18-91` / `convert_skill.py` 各自内联前端解析器，未调用共享模块。
> - **shy 侧新增 `run_checks.py`（可执行验收标准）**：REQ 的 `## 验收标准` 里 `check:<name>` 条目一次机械跑完、秒级出结果；Spec 轴"靠跑不靠读"。forge 无任何等价物——这是 §3 对照表与 §4 候选均未涵盖的**新增差异**，已并入 §3 表。
>
> 复核指令与结果见 §7「证伪检查命令与结果」追加段。

> 范围：为 `shy-skill-suite`（技能开发套件）找可借鉴的功能。逐项拆解对标物 `AgriciDaniel/skill-forge` 的功能、产物与门禁，再与 `shy-skill-suite` 对照，给出「可直接吸收 / 需改造 / 明确不吸收」三类候选。
> 对标物锁定依据：`docs/shy-skill-suite/requirements/REQ-0001`（「skill-forge 是 plan → build 直接生成整套文件」）、`REQ-0005`（「skill-forge 的 8 个 agent」）、`REQ-0007`（「skill-forge 的 comparator」）、`lifecycle.md`（「skill-forge 有 eval 驱动的迭代」）——四条指纹全部只命中本仓库：8 个 agent（architect/writer/validator/converter/executor/grader/analyzer/comparator）、Tier 1–4、`plan → build`、`comparator`。
> 一手来源：`git clone --depth 1 https://github.com/AgriciDaniel/skill-forge`（commit `2872ee9e1be8b81d48d8e6f2fe6c96225885e87b`，main，MIT，`CHANGELOG` 最新 `v1.1.0`）。
> 方法：本地克隆后逐文件通读；每条主张标注 `file:line`。涉及差异的结论均对 `shy-skill-suite` 侧跑了一次证伪检查（见 §4 的「验证」列）。
> 调研日期（access date）：2026-09-16。

---

## 0. 结论速览（TL;DR）

1. **它是一套「流水线式」技能创造者**：`plan → build → review → evolve → eval → benchmark → publish → convert` 八个子技能 + 调度器；核心叙事是 **Tier 1–4 复杂度分层 + 0–100 健康分 + 阈值门控**。
2. **它的独有能力（shy 完全没有）**：`package_skill.py`（打 `.skill` 包）、`convert_skill.py`（转 Codex/Gemini/Antigravity/Cursor）、`assets/templates/` 四套 tier 模板、`agents/`（8 个原生子 agent 定义）、`init_skill.py --tier` 分档脚手架。
3. **shy 的独有能力（它完全没有）**：需求文档 REQ 活文档（`docs/<skill>/requirements/` + `track_requirements.py`）、逼问 `grilling.md`、三轴分离复审（行为 / 需求 Spec / 标准）、先证伪再提意见、`agent_runner.py` 真跑触发检测。**它没有"回写需求"这一环**（`lifecycle.md` 的判断经本次核对成立）。
4. **两者最像的地方**：eval 工作区布局（`iteration-N/eval-N/{with_skill,baseline}`）、grader/analyzer/comparator 角色、`description` 作为唯一触发指针、train/test 选优防过拟合。这些 shy 已吸收（`REQ-0005/0007`），实现反而更完整。
5. **可直接吸收的高价值三项**：① 0–100 分级健康分 + 阈值门控（给复审结论一个可比的数）；② `.skill` 打包（发布能力）；③ tier 模板（起骨架的"按档位"版本）。
6. **必须警惕**：它自身存在三处**文档-实现不一致 / 反向命名**（§5），照抄会把 bug 抄进来；尤其 `token_savings_ratio`/`time_savings_ratio` 的语义反向，正是 shy `REQ-0013` 要修的那个坑。

---

## 1. skill-forge 事实清单

**定位**：Tier 4 的 Claude Code 技能，用于创建 / 复审 / 演化 / 发布其他技能，遵循 Agent Skills 开放标准与「3 层架构（directive / orchestration / execution）」（`CLAUDE.md:1-7`）。

**仓库结构与规模**（`README.md:88-118`，`CLAUDE.md:11-59`）：

| 层 | 内容 |
| --- | --- |
| 调度器 | `skill-forge/SKILL.md`（175 行）——命令路由 + Tier 表 + 质量门 |
| 子技能 | `skills/skill-forge-{plan,build,review,evolve,eval,benchmark,publish,convert}/SKILL.md`（8 个） |
| Agents | `agents/skill-forge-{architect,writer,validator,converter,executor,grader,analyzer,comparator}.md`（8 个） |
| 脚本 | `skill-forge/scripts/`（8 个，纯 stdlib） |
| 知识库 | `skill-forge/references/`（10 个 md） |
| 模板 | `skill-forge/assets/templates/`（minimal / workflow / multi-skill / ecosystem，4 个） |

**Pipeline**（`skill-forge/SKILL.md:33-43,59-69,164-175`）：

```
plan(设计) → build(生成) → review(审计) → eval(功能评测) → benchmark(统计基准) → evolve(迭代) → publish(分发) → convert(跨平台)
```

**安装/分发**：`bash install.sh` 把主技能+子技能装到 `~/.claude/skills/`、agents 装到 `~/.claude/agents/`，支持 `--uninstall`（`install.sh:5-63`）；也声明为 Claude Code 插件（`.claude-plugin/plugin.json`）。依赖 **Python 3.10+ 纯标准库**（`README.md:121-125`）。

---

## 2. 功能逐项拆解

### 2.1 复杂度分层 Tier 1–4（它的核心抽象）

| Tier | 名称 | 结构 | 模板 | 出处 |
| --- | --- | --- | --- | --- |
| 1 | Minimal | 单 `SKILL.md` | `minimal.md` | `skill-forge/SKILL.md:75-79` |
| 2 | Workflow | `SKILL.md + scripts/` | `workflow.md` | `:81-84` |
| 3 | Multi-Skill | 编排器 + 子技能 | `multi-skill.md` | `:86-90` |
| 4 | Ecosystem | 编排器 + 子技能 + agents + scripts | `ecosystem.md` | `:92-96` |

- **判档信号表**（`skills/skill-forge-plan/SKILL.md:43-50`）：用例数 1-2→T1、2-3→T2、4-8→T3、8+→T4；决策矩阵再按「单工作流无脚本 / 需确定性校验 / 多工作流 / 复杂域+并行委派」复核（`plan:52-56`）。
- 每个 tier 给出确定目录树，规划即脚手架蓝图（`plan:62-114`）。
- **与 shy 的关系**：shy 已吸收 "Tier 3/4" 术语（`lifecycle.md:30`「只有满足其一才升 Tier 3/4（orchestrator + 子技能，或再加 `agents/`）」），但**刻意不采用它的分档生成**——`REQ-0001` 明确「skill-forge 是 plan→build 直接生成整套文件；我们把开发拆成迭代阶段，所以脚手架要轻量，只生成目录结构」。差异是**有意的**，不是缺陷。

### 2.2 生成 `build`（`init_skill.py`）

- CLI：`python init_skill.py <name> --tier <1-4> --path <out> --sub a,b,c`（`init_skill.py:307-325`）。
- 产物随 tier 变化（`init_skill.py:234-304`）：T2 起加 `references/domain-knowledge.md` + `scripts/process.py`（含 argparse 骨架、`chmod 0755`）；T3 加 `skills/<name>-<child>/SKILL.md` 与 `assets/`；T4 为前 3 个子技能生成 `agents/` 定义（`model: inherit`，`tools: Read/Grep/Glob`）。
- 非幂等（目标存在即拒绝，`:338-341`）。
- build 子技能还内联了可运行的 SKILL.md / 脚本 / agent / install.sh 模板（`skills/skill-forge-build/SKILL.md:105-198`），并**在交付时附 3 条应触发 + 3 条不应触发的测试查询**（`build:205-212`）。
- **与 shy 的差异**：shy 的 `scaffold_skill.py` 只生成 `SKILL.md`（`skills/shy-skill-suite/SKILL.md:41`）。tier 分档、子技能骨架、agent 骨架、install.sh 均缺。

### 2.3 复审 `review`（0–100 健康分）

- 10 步流程：定位文件 → 结构校验 → frontmatter 审计 → 触发分析 → 指令质量 → 架构 → 脚本 → **生成 Health Score** → 生成触发评测集 → 出报告（`skills/skill-forge-review/SKILL.md:14-168`）。
- **SKILL.md 侧加权 rubric**（`review:101-108`）：Frontmatter 25% / Trigger 20% / Instruction 25% / Structure 15% / Script 10% / Progressive Disclosure 5%。
- **报告格式固定**：`Critical / High Priority / Recommendations / Suggested Test Queries`（`review:128-168`）。
- **脚本 `validate_skill.py` 的打分口径**（与上面不同）：CRITICAL −20 / HIGH −10 / MEDIUM −5 / LOW −2，下限 0；`pass = score ≥ 60`，`--strict` 要求 ≥ 80（`validate_skill.py:291-305,357-359`）。
- 触发评测集规模要求：应触发 8–10、不应触发 8–10，且负例必须是 **near-miss**（非明显无关）（`review:116-118`）。
- **与 shy 的差异**：shy 复审是**三轴分离**（行为 / 需求 Spec / 标准）且**不给总分**（`reviewing-skills.md:9-21`）；shy 的 `validate_skill.py` 明确「只查结构与规范，不做语义/质量审查」（`shy-skill-suite/scripts/validate_skill.py:2-15`）。forge 的单一 0–100 分带来"可比较"的好处，但也把需求轴淹没进质量轴——正是 shy 刻意避免的（`reviewing-skills.md:164`「把 Spec 轴并进质量轴」列为反模式）。

### 2.4 迭代 `evolve`

- 按**问题类别**分派修复手册：A 触发问题 / B 执行问题 / C 架构问题 / D 质量问题（`skills/skill-forge-evolve/SKILL.md:15-102`）。
- **迭代工作区**：`eval-workspace/iteration-N/eval-N/{with_skill,baseline}/` + `benchmark.json` + `feedback.json`（`evolve:108-122`）。
- **双层迭代**：完整 eval pipeline + 轻量 `Self-Annealing`（改→跑原失败用例→跑 3 个回归用例→成功则沉淀 learning）（`evolve:138-153`）。
- 描述优化显式规定「**按 test 分选优、不按 train**」防过拟合（`evolve:165`）。
- **与 shy 的差异**：shy 的 `lifecycle.md` 把迭代串成「逼问→落需求→实现→复审→**回写需求**→下一轮」，并显式指出 forge「**没有把复审结果回写成需求**这一环」（`lifecycle.md:3,47`）。本次核对成立：forge 的迭代产物是 workspace 工件与 learning，**无需求文档**。shy 的 `Self-Annealing` 等价物是 `writing-skills.md §7` 的"失败回填成 gotcha"。

### 2.5 评测 `eval`

- 用 **executor / grader / comparator / analyzer** 四个子 agent（`skills/skill-forge-eval/SKILL.md:101-214`）。
- 工作区约定：**必须在 skill 目录之外**（`eval:58-62`）。
- 每个 eval 跑 `with_skill` 与 `baseline` 两条；新技能 baseline = 不加载技能，改技能 baseline = 旧版本快照（`eval:101-126`）。
- JSON schema：eval set（`eval:27-48`）、`eval_metadata.json`（`eval:90-99`）、`timing.json`（`total_tokens/duration_ms/total_duration_seconds`，`eval:120-126`）、`grading.json`（`assertions[]{name,passed,evidence}` + `pass_rate`，`eval:134-147`）、`feedback.json`（`eval:191-203`）。
- 失败契约：单 run >5min 标 `timed_out`；崩溃写 `error.txt` 继续；无法判定记 `passed: null`（`eval:216-222`）。
- **与 shy 的差异**：shy 的 `subagents.md` + `running-evals.md` 定义了等价角色与工作区（executor / grader / spec-reviewer / analyzer / comparator），且 `optimize_description.py` 支持 `--runner opencode|teleagent|cmd` **真跑触发**。此块 shy 不弱于 forge。

### 2.6 基准 `benchmark`（统计化 + 阈值门控）

- 每个 eval 跑 `trials_per_eval`（默认 3）次，算 mean/std，暴露抖动（`skills/skill-forge-benchmark/SKILL.md:44-53`；`aggregate_benchmark.py:92-99` 用样本标准差）。
- **阈值门控**（`benchmark:36-40,151-157`）：`min_pass_rate ≥ 0.8`、`max_avg_tokens ≤ 100000`、`max_avg_duration_seconds ≤ 120`、`min_improvement_ratio ≥ 1.0`；**未过阈值不得发布**。
- 可靠性标签：单 eval trial < 2 → `unreliable`；`pass_rate_std > 0.3` → 标不可靠；成本 > 2× 均值 → 离群（`benchmark:162`；`agents/skill-forge-analyzer.md:36-47`）。
- `benchmark.json` 含 `improvement_ratio` / `token_savings_ratio` / `time_savings_ratio`（`aggregate_benchmark.py:206-248`）。
- **与 shy 的差异**：两者的 `aggregate_benchmark.py` **几乎同构**（同一份代码演化而来）。shy 额外有 `--previous` 回归对比的完整实现。**阈值门控是 forge 独有**（但见 §5，脚本实际不产出 `thresholds_met`）。**注意**：forge 的 `token_savings_ratio` 同样按 `with/baseline` 计算却叫 "savings"——即 shy `REQ-0013` 要修的同一个反义命名 bug。

### 2.7 发布 `publish`（`.skill` 打包）

- 前置硬门禁：**review score ≥ 80/100**（`skills/skill-forge-publish/SKILL.md:17`）。
- 产物：`install.sh`、repo 级 `README.md`（**约定绝不放进技能文件夹**，`publish:66`）、`.skill` zip（`package_skill.py`）、`.gitignore`、LICENSE、可选 `.claude-plugin/` manifest。
- `package_skill.py`：把技能目录打成 ZIP 换扩展名 `.skill`；白名单打包主目录 + `skills/<name>-*/` + `agents/<name>-*.md` + 根 `scripts/` + `install.sh` + LICENSE；排除 `__pycache__/.pyc/.git/node_modules/.env` 等（`package_skill.py:25-115,143-146`）。
- Release checklist 显式要求「任何文件无 secrets/API keys」（`publish:150-157`）。
- **与 shy 的差异**：shy **完全没有打包/发布能力**（已证伪检查，见 §4）。这是最大功能空白之一。

### 2.8 跨平台转换 `convert`（最独有的能力）

- 目标平台：OpenAI Codex / Gemini CLI / Antigravity / Cursor（`skills/skill-forge-convert/SKILL.md:3-12`）。
- 流程：读源技能 → `convert_skill.py --dry-run --target all` 出兼容报告 → 实转 → 对每个平台产物再跑 `validate_skill.py` → 出部署报告（`convert:22-101`）。
- **frontmatter 字段三分类**（`convert_skill.py:21-46`）：**Portable**（name/description/license/compatibility/metadata/argument-hint）/ **Adaptable**（allowed-tools、disable-model-invocation，按平台 keep/strip/move）/ **Claude-Only**（context/agent/hooks/model/user-invocable/skills/memory，剥离并警告）。
- 兼容分 = `(portable×1 + adaptable×0.5) / total × 100`（`convert_skill.py:201-213`）。
- 正文路径替换（如 `~/.claude/skills/` → `~/.agents/skills/`；Antigravity 把 `./scripts/` → `{{SKILL_PATH}}/scripts/`）（`:219-250`）；MCP 配置格式转换（JSON↔TOML）（`:731-795`）；生成 `install-multiplatform.sh`（`:800-904`）。
- 平台规则知识库完整：`references/platforms.md`（存储路径、指令文件、字段兼容、hook 能力、子代理能力对比）。
- **与 shy 的差异**：shy **完全没有**跨平台转换。但 shy 的服务对象是 opencode / TeleAgent，不是 Claude Code；forge 的转换目标里没有 opencode/TeleAgent。**是否值得吸收取决于 shy 是否要跨平台发布**（见 §4，列「需决策」）。

### 2.9 Agents 分工（8 个）

| 阶段 | Agent | 写盘 | 关键产物 | 出处 |
| --- | --- | --- | --- | --- |
| 设计 | architect | 否 | 架构评估/文件树/路由表 | `agents/skill-forge-architect.md:40-46` |
| 生成 | writer | 否 | SKILL.md 全文 | `skill-forge-writer.md:55-58` |
| 校验 | validator | 否 | 0–100 分 + 优先级问题 | `skill-forge-validator.md:42-59` |
| 转换 | converter | 否 | 兼容矩阵 + 风险 + 适配策略 | `skill-forge-converter.md:44-52` |
| 评测-执行 | executor | 是 | `timing.json` + `outputs/` | `skill-forge-executor.md:56-61` |
| 评测-评分 | grader | 是 | `grading.json`（二元断言 + 证据） | `skill-forge-grader.md:36-62` |
| 评测-分析 | analyzer | 否 | 失败簇/可靠性/回归/成本 | `skill-forge-analyzer.md:29-65` |
| 评测-对比 | comparator | 否 | 盲测 A/B 偏好 | `skill-forge-comparator.md:42-76` |

- **工具权限呈递增梯度**：多数 agent 只读（Read/Grep/Glob）；validator/converter 多 Bash；**只有 executor 有 Write**——从工具层保证「评分者不能改产物」。
- **与 shy 的差异**：shy 无 `agents/` 目录，把角色写进 `references/subagents.md`（派发 vs 内联），并**额外有 `spec-reviewer`（需求轴独立评审）**——forge 没有需求轴，故无此角色。shy 的"独立于作者"约束更明确（`subagents.md:1-3`）。

### 2.10 References 知识库（10 个）

`anatomy` / `patterns` / `frontmatter-spec` / `description-guide` / `testing-guide` / `pro-agent` / `tools-reference` / `hooks-reference` / `skills-activation` / `platforms`（`skill-forge/SKILL.md:150-162`）。

最值得借鉴的三份：
- **`description-guide.md`**：三段式框架 `[WHAT]+[CAPABILITIES]+[WHEN/TRIGGERS]`、**负向触发**（`Do NOT use for...`）、长度分层（100–200 / 200–500 / 500–900 / ≤1024）、**反向测试问句**（"When Would You Use This?"）（`description-guide.md:8-136`）。shy 的 `writing-skills.md §1` 已覆盖大部分，但**负向触发与长度分层**可以补。
- **`testing-guide.md`**：量化指标 **触发准确率 90%+ / 误报 <5% / 完成率 95%+ / 错误恢复 80%+**（`testing-guide.md:96-104`），以及欠/过触发的**反向调参**（`testing-guide.md:148-165`）。shy 的 `running-evals.md` 只有「触发率默认阈值 0.5」（`reviewing-skills.md:54`），**更粗**。
- **`pro-agent.md`**：3 层架构与「会出错的做成脚本、需判断的留在指令」二分法则，附**复合失败率论证**（每步 90%，5 步累计 59%）（`pro-agent.md:5-9,100-101`）。shy 的 `writing-skills.md §9` 有类似"校准脆弱度"，但无这条论证。

---

## 3. 功能对照总表

| 功能域 | skill-forge | shy-skill-suite | 差距类型 |
| --- | --- | --- | --- |
| 需求文档（活文档） | 无 | **REQ-NNNN + 状态机 + 迭代记录**（`writing-requirements.md`） | shy 独有 |
| 需求跟踪 / frontier | 无 | **`track_requirements.py`**（frontier / 悬空 `blocked_by`） | shy 独有 |
| 验收标准的可执行门 | 无（验收只停在需求散文） | **`run_checks.py`**（REQ 里 `check:` 标签 → 机械跑、秒级；Spec 轴"靠跑不靠读"） | shy 独有 |
| 逼问 | plan 的 5 问 discovery（`plan:14-22`） | **设计树 + frontier + 三动作**（`grilling.md`） | shy 更强 |
| 脚手架 | `init_skill.py --tier 1-4`（生成整套树） | `scaffold_skill.py`（只生成 SKILL.md） | forge 更强 |
| Tier 分层 | **Tier 1–4 + 4 套模板** | 只在 `lifecycle.md` 用 Tier 3/4 概念，无模板 | forge 更强 |
| 复审 | 0–100 分（含加权 rubric + 报告） | **三轴分离 + P0/P1/P2**，无总分 | 各有取舍 |
| 校验器 | 0–100 分、分四级、可校验 agent；**英文硬编码触发词检查** | 结构/规范校验 + frontmatter 白名单 + YAML 危险检测 + **悬空引用检查** | 互补 |
| 触发评测集 | `generate_eval_set.py` | 同名脚本（同源） | 持平 |
| 描述选优 | `optimize_description.py`（实为 1 轮） | 同名 + `--runner opencode\|teleagent\|cmd` 真跑 | shy 更强 |
| 真跑触发检测 | 无（无 `agent_runner`） | **`agent_runner.py`** | shy 独有 |
| eval 工作区 | `iteration-N/eval-N/{with_skill,baseline}` | 同构（`running-evals.md`） | 持平 |
| benchmark | 多 trial + 方差 + **阈值门控** | 多 trial + 方差 + `--previous` 回归对比，**无阈值** | forge 更强 |
| 盲测 A/B | `comparator` agent | `subagents.md` comparator | 持平（shy 已吸收） |
| 发布 / 打包 | **`package_skill.py` → `.skill`** | 无 | forge 独有 |
| 跨平台转换 | **`convert_skill.py`（4 平台）** | 无 | forge 独有 |
| 原生子 agent | **`agents/` 8 个** | `references/subagents.md` 角色表 | 结构差异 |
| 知识库 | 10 个 references | 7 个 references | 持平（主题不同） |
| 先证伪再提意见 | 无 | **`reviewing-skills.md §3` + AGENTS.md** | shy 独有 |
| 自包含约束 | 靠 install.sh 打包整包 | **显式原则 + 悬空引用检查** | shy 更强 |

---

## 4. 借鉴候选（三类）

> 验证方式：能跑的已跑并给出结果；跑不了的标「待决策」，不作为已证结论。

### 4.1 可直接吸收

| 候选 | 来源 | 为什么值得 | 验证 |
| --- | --- | --- | --- |
| **0–100 分级健康分 + 阈值门控**（给复审一个可比的数，并按级别扣分：CRITICAL −20 / HIGH −10 / MEDIUM −5 / LOW −2；`pass ≥ 60`，`strict ≥ 80`） | `validate_skill.py:291-305,357-359`；`benchmark:151-157` | shy 复审只有 P0/P1/P2 定性，跨轮/跨技能不可比；分数能进 benchmark 报告 | 已读源码确认算法存在；**待决策**：是否与 shy 的「三轴分离」兼容（建议分数只覆盖"标准轴"，不碰需求轴） |
| **`.skill` 打包 + 发布 checklist** | `package_skill.py:25-115,143-146`；`publish:150-157` | shy 目前无任何分发能力；技能要被单独复制部署（AGENTS.md 明确前提），打包是自然下一步 | 已证伪「shy 有打包」→ `Get-ChildItem skills/shy-skill-suite` 只列 `references/ scripts/ SKILL.md`，`grep package_skill` 无命中 |
| **description 的负向触发 + 长度分层** | `description-guide.md:79-111` | shy 的 `writing-skills.md §1` 只说"宁可 pushy"，缺显式的 `Do NOT use for...` 与长度基准 | 已读 shy `writing-skills.md`，确无负向触发条目 |
| **测试量化指标（90% / 5% / 95% / 80%）** | `testing-guide.md:96-104` | shy 的触发率阈值只有笼统的 0.5；具体指标让"算通过"变成可判定 | 已读 `reviewing-skills.md:54`，确认只有 0.5 |

### 4.2 需改造后吸收

| 候选 | 来源 | 改造点 |
| --- | --- | --- |
| **tier 模板 / `init_skill.py --tier`** | `assets/templates/*`；`init_skill.py:234-304` | shy 已决定"脚手架保持轻量"（`REQ-0001`），不能直接照搬整套生成；可只取其**四档"何时拆分"的判定表**（`plan:43-56`）补进 `lifecycle.md §1`。**待决策** |
| **平台转换的三分类法（Portable / Adaptable / Claude-Only）** | `convert_skill.py:21-46`；`platforms.md:39-75` | shy 面向 opencode/TeleAgent，不在 forge 的 4 个目标平台里；但**字段三分类 + 兼容分**是可复用的方法论。是否做转换属**待决策**（shy 是否需要跨平台发布） |
| **`Self-Annealing`（失败→原用例→3 回归用例→沉淀）** | `evolve:138-153` | shy 的 `lifecycle.md` 阶段 4「回写需求」更强，但缺"改后跑回归"的轻量回路；可并入 `reviewing-skills.md`。**待验证**：与现有 Step 2 的整技能对照是否重复 |
| **`pro-agent.md` 的复合失败率论证（90%^5≈59%）** | `pro-agent.md:5-9` | 可直接放进 `writing-skills.md §9`，给"脆弱操作写成脚本"一个 why |

### 4.3 明确不吸收

| 不吸收项 | 理由 |
| --- | --- |
| **单一 0–100 分作为复审总评** | 与 shy 三轴分离原则冲突（`reviewing-skills.md:17,164` 明列"把 Spec 轴并进质量轴"为反模式）。分数只能作为**标准轴的子项**。 |
| **`token_savings_ratio` / `time_savings_ratio` 命名** | 语义反向（按 with/baseline 算却叫 savings），正是 shy `REQ-0013` 待修的 bug；**绝不能照抄**。 |
| **英文硬编码的触发词检查** | forge 的 `validate_skill.py:143-152` 要求 `Use when...` 等英文模式，对中文技能误报；shy 校验器有意只查结构。 |
| **Claude Code 专属知识**（hooks 15 事件、`skills-activation.md` 的 2% 字符预算、`tools-reference.md` 的 Task 权限语法） | shy 运行在 opencode / TeleAgent，这些平台语义不通用。 |

---

## 5. 必须警惕：对标物自身的坑

| 坑 | 证据 | 影响 |
| --- | --- | --- |
| **`token_savings_ratio` / `time_savings_ratio` 语义反向** | `aggregate_benchmark.py:206-248`（按 `with/baseline` 计算，名字却叫 savings） | 与 shy `REQ-0013` 同一 bug，**shy 正在修而 forge 未修** |
| **review 的两套评分口径不一致** | SKILL.md 是加权 rubric（25/20/25/15/10/5，`review:101-108`）；脚本是按级别扣分（`validate_skill.py:291-305`） | 同一技能会出现两个"健康分"，报告对不上 |
| **`thresholds_met` 只在文档、脚本不产出** | benchmark 子技能的 schema 列了 `thresholds_met`（`skills/skill-forge-benchmark/SKILL.md:92-97`），但 `aggregate_benchmark.py` 输出无此字段 | 阈值门控无程序化落地，靠 agent 手算 |
| **`optimize_description.py` 名义多轮、实际 1 轮** | 主循环无条件 `break`（`optimize_description.py:245`） | "自动优化循环"是文档叙事，实为单轮建议 |
| **`skill_utils.py` 被复制而非复用** | `validate_skill.py` / `convert_skill.py` 内联了各自的前端解析器（`validate_skill.py:18-91`；`convert_skill.py:75-145`），未调用共享模块 | 违反单一事实源，三份解析器会漂移 |
| **`plugin.json` 版本落后于 `CHANGELOG`** | `plugin.json` = `1.0.0`，`CHANGELOG.md:3` = `v1.1.0` | 发布元数据不一致 |

---

## 6. 一句话总结

**skill-forge 的价值在"广度"（分层生成、打分、基准阈值、发布、跨平台）与"流水线化"；shy-skill-suite 的价值在"深度"（需求活文档、逼问、三轴复审、先证伪、真跑触发检测）。** 可吸收的是它的**度量与分发层**（健康分 / 阈值 / 打包 / 描述触发细节），不吸收的是它的**单一总分**与**命名 bug**。

---

## 7. 来源

- 对标仓库：`AgriciDaniel/skill-forge` @ `2872ee9e1be8b81d48d8e6f2fe6c96225885e87b`（本地克隆于 `%TEMP%\opencode\skill-forge-src`；MIT）。
- 本仓库对照物：`skills/shy-skill-suite/`（`SKILL.md` + 7 `references/` + 7 `scripts/`）、`docs/shy-skill-suite/requirements/REQ-0001…0017`。
- 引用的 forge 文件路径统一简写：`skill-forge/SKILL.md`、`skills/skill-forge-*/SKILL.md`、`agents/skill-forge-*.md`、`skill-forge/scripts/*.py`、`skill-forge/references/*.md`、`skill-forge/assets/templates/*.md`。
- 证伪检查命令与结果：
  - `Get-ChildItem skills/shy-skill-suite -Recurse` → 只有 `references/`、`scripts/`、`SKILL.md`（无 `agents/`、`assets/`）。
  - grep `package_skill|convert_skill|0-100|health score|assets/templates` 于 `skills/shy-skill-suite` → 无命中。
  - **2026-09-20 复核追加**（克隆 `AgriciDaniel/skill-forge` @ `2872ee9`，`%TEMP%\opencode\skill-forge-src`）：
    - `git rev-parse HEAD` → `2872ee9e1be8b81d48d8e6f2fe6c96225885e87b`（与报告锁定版本一致，无漂移）。
    - `Select-String token_savings_ratio aggregate_benchmark.py` → `:203-204` 按 `with/baseline` 计算；`Select-String thresholds_met aggregate_benchmark.py` → 输出 schema 无此字段（只在 benchmark 子技能 SKILL.md）。
    - `Select-String "break|for |while " optimize_description.py` → `:244-245` 主循环无条件 `break`。
    - 复核 `validate_skill.py:291-305`（flat 扣分）与 `SKILL.md:101-108`（加权 rubric）两套口径并存；`validate_skill.py:18-91` 内联解析器。
    - shy 侧 grep `run_checks.py` → `scripts/run_checks.py` 存在（1664 行），forge 无同名文件。
