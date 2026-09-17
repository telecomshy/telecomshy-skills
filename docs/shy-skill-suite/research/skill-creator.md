# 对标调研：Anthropic skill-creator 与 shy-skill-suite 的功能对比

> **后续进展（2026-09-17 补记）**：本报告写后技能已变更——新增**可执行验收标准**（`scripts/run_checks.py` + REQ 里 `check:` / `（行为）` / `（语义）` 三类标记）、「P2 不阻断」停止规则、grader 兼评评测集与抽取隐式主张、analyzer notes 落地。本报告中「需求轴靠读散文 / 复审循环」相关描述已过时；现状见 `REQ-0030` 迭代记录与 `skills/shy-skill-suite/references/reviewing-skills.md` Step 3。

> 范围：为 `shy-skill-suite`（技能开发套件）找可借鉴的功能。逐项拆解对标物 **Anthropic 官方 `skill-creator`** 的功能、产物与脚本，再与 `shy-skill-suite` 对照，给出「可直接吸收 / 需改造后吸收 / 明确不吸收」三类候选。
> 对标物锁定依据：本仓库多处已显式对标（`REQ-0002:17` 点名 `skill-creator` 的 `quick_validate.py`；`REQ-0005:21,73` 点名其 `agents/`；`REQ-0007:62` 点名其 `comparator`；`REQ-0019:19` 逐行分析其 `eval-viewer/generate_review.py`），且 `references/reviewing-skills.md:211`、`writing-requirements.md:147` 把它列入「依据」。
> 一手来源（上游）：`github.com/anthropics/skills`，分支 `main`，commit `34040c9c568585f6929bedeaad110ad08f079624`（committer date 2026-09-10），技能位于 `skills/skill-creator/`。
> 一手来源（本地）：`C:\Users\18907\.agents\skills\skill-creator\`（本机安装副本）。
> 本地与上游一致性：对 18 个文件逐一做 SHA256（CRLF→LF 归一化）比对，**18/18 全同**（见 §8）。即本地副本 = 上游 HEAD，无版本漂移。
> 技能子树最后变更：`SKILL.md` / `scripts/run_loop.py` @ `b0cbd3df1533`（2026-03-06）；`eval-viewer/generate_review.py` / `scripts/aggregate_benchmark.py` @ `3d5951151859`（2026-02-25）；`LICENSE.txt` @ `b9e19e6f4477`（2026-04-20）。
> 方法：读本地全部文件（18 个）、并用 `codeload` 下载上游同 commit 的 zip 做逐文件比对；每条主张标注 `file:line`。涉及差异的结论均对 `shy-skill-suite` 侧跑了一次证伪检查（见 §4 的「验证」列）。
> 调研日期（access date）：2026-09-17。
> 限制：本机无 `python` / `py` 可执行文件，所有需要运行 Python 的验证一律标「静态阅读」；git 直连 clone 失败，改用 `codeload` zip（命令与结果见 §8）。

---

## 0. 结论速览（TL;DR）

1. **它是一套「eval 驱动 + 人类在环」的技能开发器**，核心叙事是：**draft → 跑 with-skill/baseline 对照 → 把结果塞进交互式 HTML viewer 让人评 → 按反馈重写 → 重复**，最后用 `run_loop.py` 自动优化 `description`（`SKILL.md:10-22,472-485`）。
2. **它面向 Claude 平台，不是 opencode/TeleAgent**：通篇依赖 `claude -p`（`run_eval.py:70-79`）、`.claude/commands/`（`run_eval.py:53-54`）、`available_skills`（`SKILL.md:398`）、`present_files`（`SKILL.md:408`），并有专门的 Claude.ai / Cowork 分支（`SKILL.md:420-455`）。全仓 grep `opencode|TeleAgent` **0 命中**。
3. **它最硬的、shy 没有的三件套**：① **交互式 eval viewer**（本地 HTTP + 自动保存反馈 + 「上一轮产出/反馈」并列 + Benchmark tab；`eval-viewer/generate_review.py` + `viewer.html`）；② **自动化 description 优化环**（`run_loop.py`，含 train/test 分层、按 test 选优、防泄漏盲化）；③ **grader 兼任「评测集批评者」**（`agents/grader.md:9,68-79` 的 `eval_feedback`），以及**隐式主张抽取核验**（`grader.md:43-59`）。
4. **两者最像的地方**：工作区布局 `iteration-N/eval-N/{with_skill,baseline}`、`grading.json`（`text/passed/evidence`）、`timing.json`（`total_tokens/duration_ms`）、grader/analyzer/comparator 角色、train/test 选优防过拟合、`.skill` 打包思路。这些都已被 shy 吸收或以角色描述保留（`REQ-0005`/`REQ-0007`/`REQ-0019`）。
5. **可直接吸收的高价值四项**：① grader 兼评评测集（`eval_feedback`）；② grader 抽取/核验隐式主张；③ HTML 报告并列**上一轮产出与反馈**（shy 只有 `--previous` 的**数字**对比）；④ 把 analyzer 观测以 `notes` 持久化进 `benchmark.json` 并渲染。另有 TOC 规则、description 100–200 词目标、validation-gated `.skill` 打包。
6. **必须警惕**：它自身有**工作区布局文档-实现不符**、**delta 方向被目录字母序反转**、**`assertions`/`expectations` 术语漂移**、**Windows 不兼容脚本**（`select.select`/`lsof`）等坑（§7），照抄会把 bug 抄进来。

---

## 1. skill-creator 事实清单

**定位**：Anthropic 官方示例技能之一（`README.md`：*"This repository contains Anthropic's implementation of skills for Claude"*），用于**创建新技能**与**迭代改进既有技能**，并**量化测量技能表现**。
**许可**：Apache 2.0（`LICENSE.txt:1-4`；上游仓库根无顶层 LICENSE，各技能各自带 `LICENSE.txt`）。

**仓库结构与规模**（本地路径 `C:\Users\18907\.agents\skills\skill-creator\`）：

| 层 | 文件 | 规模 |
| --- | --- | --- |
| 主文件 | `SKILL.md` | 485 行 / 33,653 B |
| Agents | `agents/analyzer.md`（274 行）、`comparator.md`（202 行）、`grader.md`（223 行） | 3 个 |
| References | `references/schemas.md` | 430 行 |
| Scripts | `scripts/`：`run_loop.py`(328)、`run_eval.py`(310)、`aggregate_benchmark.py`(401)、`generate_report.py`(326)、`improve_description.py`(247)、`package_skill.py`(136)、`quick_validate.py`(103)、`utils.py`(47)、`__init__.py`(0) | 9 个 |
| Eval viewer | `eval-viewer/generate_review.py`(471 行)、`eval-viewer/viewer.html`(46,323 B) | 2 个 |
| Assets | `assets/eval_review.html` | 146 行 |
| 许可 | `LICENSE.txt` | 11,546 B |
| **合计** | **18 个文件** | **≈225 KB** |

**工作流（两个子环）**（`SKILL.md:10-30`）：

```
[创建/改进环] 理解意图 → 写 SKILL.md 草稿 → 写 2-3 个测试 prompt(evals/evals.json)
   → 同一轮并发跑 with_skill + baseline → 边跑边草拟 assertions
   → grader 评分(grading.json) → aggregate_benchmark → 起 eval viewer 给人评
   → 读 feedback.json → 重写技能 → 下一 iteration → 重复

[触发优化环] 生成 20 条 should-trigger / should-not-trigger 查询
   → assets/eval_review.html 让用户编辑/签字 → run_loop.py 自动迭代 description
   → 按 test 分选优 → 套用 best_description
```

**关键约定**：结果放 `<skill-name>-workspace/`（技能目录的**同级**，`SKILL.md:167`）；每个用例一个 `eval-N/`；分级与聚合分离；报告只在 `generate_review.py` 生成，禁止自写 HTML（`SKILL.md:249,451`）。

**依赖**：Python 标准库为主（`generate_review.py:12-13` 自述 zero-dependency，但 HTTP 用 `http.server`）；`quick_validate.py:9` 需要 **PyYAML**（`import yaml`）；description 优化需要 `claude` CLI。

---

## 2. 功能逐项拆解

> 约定：`file:line` 一律相对本地技能根 `C:\Users\18907\.agents\skills\skill-creator\`，简写为 `SKILL.md`、`scripts/*.py`、`agents/*.md`、`eval-viewer/*`、`references/schemas.md`、`assets/eval_review.html`。

### 2.1 触发优化：自动化 `description` 迭代环（`run_loop.py` + `run_eval.py`）

- **`run_eval.py`**：为每条查询创建 `.claude/commands/<skill>-skill-<uuid>.md`，使技能进入 `available_skills`；跑 `claude -p <query> --output-format stream-json --include-partial-messages`，从流事件里检测 `Skill`/`Read` 工具调用是否命中该 command 文件名（`run_eval.py:51-68,70-79,129-171`）。判定：should-trigger 时 `trigger_rate ≥ threshold` 即通过（默认 0.5；`:228-242`）。
- **`run_loop.py`**：把 train/test 按 `should_trigger` 分层切分（`:24-44`，holdout 默认 0.4），每轮并发评估全部查询（`:87-99`），把 **test 结果从 history 里剥掉**再喂给改进模型（`:194-198` 防泄漏），调用 `improve_description.py` 生成新描述（`:199-208`），最多迭代 5 次（`:251`），最后**按 test 分选优**（`:216-222`）。
- **`improve_description.py`**：以 `claude -p`（prompt 走 stdin）生成新描述（`:20-47,144`），并规定目标长度 **100–200 词、硬限 1024 字符**（`:132`）；超限再发一次「缩短」单轮调用（`:163-182`，注释承认这是从旧 SDK 多轮退化来的）。
- **`generate_report.py`**：把每次迭代渲染成 HTML 表格（train/test 两色列、每查询 ✓/✗ + 触发率、自动高亮最佳轮），并支持 `auto_refresh`（`:16-32,205-209`）。
- **`assets/eval_review.html`**：让用户交互编辑触发评测集（增删/改查询、切 should-trigger），导出 `eval_set.json`（`:63,105-141`）。
- **Delta vs shy**：shy 的 `optimize_description.py` **刻意不自带改写**（`optimize_description.py:11` "脚本本身不重写 description……循环由 agent 驱动"），只做分层打分 + 给建议；**没有** `run_loop.py` 这样的自动迭代实现。见 §4.2。

### 2.2 评测执行与评分：`grader` / `analyzer` / `comparator`

- **grader**（`agents/grader.md`）：逐 assertion 给 PASS/FAIL + 证据（`:33-41`）；**额外抽取并核验隐式主张**（factual/process/quality，`:43-59`）；**额外批评评测集本身**（`eval_feedback`：只查文件名不查内容、遗漏的重要结果、无法验证的断言，`:68-79,171-183`）。输出 schema `expectations[]{text,passed,evidence}`（`:106-133`）。
- **analyzer**（`agents/analyzer.md`）：盲测后分析赢因与可操作改进（`:1-183`）；benchmark 模式下做**跨 run 模式发现**：恒过/恒败断言、高方差、有无技能反转、成本离群（`:187-260`），输出 `notes`（字符串数组）。
- **comparator**（`agents/comparator.md`）：**盲测 A/B**（`:3-9`），生成 content/structure 二维 rubric（1–5，合成 1–10 分，`:37-86`），断言通过率仅作**次要证据**（`:79-83`），平局极少（`:83-85`）。
- **Delta vs shy**：shy 的 `subagents.md` 已有 executor/grader/spec-reviewer/analyzer/comparator 五角色，且 comparator 额外要求**两次顺序都跑**（`subagents.md:50`）、盲测只当信号不当证据（`subagents.md:53`）——**比 skill-creator 更严**。差距在 grader 的两个额外职责（见 §4.1）和 analyzer 的 `notes` 落地。

### 2.3 基准聚合：`aggregate_benchmark.py`

- 支持两种布局：工作区布局 `eval-N/{with_skill,without_skill}/run-1/grading.json` 与 legacy `runs/eval-N/...`（`:17-34`）。
- 样本标准差 mean/stddev/min/max（`:45-64`）；delta 取「前两个 config」（`:206-224`）。
- 产出 `benchmark.json` + `benchmark.md`，字段对齐 `references/schemas.md:219-305`（`run_summary{p /{mean,stddev,min,max}}`、`runs[]`、`notes[]`）。
- **Delta vs shy**：两者**近乎同源**。shy 的 `aggregate_benchmark.py` 用 `with_skill/baseline` 显式命名、产出 `improvement_ratio/token_ratio/time_ratio`（`aggregate_benchmark.py:186-188`，命名正确，`REQ-0013` 已修），并支持 `--previous` 回归对比（`:193-202`）。skill-creator 的比率字段名与 shy 不同，且存在 §7 的 delta 反转 bug。

### 2.4 交互式 HTML viewer：`eval-viewer/generate_review.py` + `viewer.html`（最具体的产物）

- `generate_review.py` 递归发现含 `outputs/` 的 run 目录（`:60-84`），把 prompt、outputs（文本/图片/PDF/XLSX 内联 base64）、grading、benchmark 与「上一轮」数据**全部嵌入** `viewer.html` 的 `/*__EMBEDDED_DATA__*/`（`:149-210,250-281`）。
- 默认起本地 HTTP（端口 3117，`:390`）并 `webbrowser.open`（`:461`）；也支持 `--static <path>` 输出独立 HTML（`:401,431-436`）。反馈经 `POST /api/feedback` 写入工作区 `feedback.json`（`:361-378`）。
- `--previous-workspace` 会加载上一轮的 `feedback.json` 与 outputs，作为「Previous Output / Previous Feedback」并列展示（`:213-247`；`viewer.html:578-612`）。
- `viewer.html` 两个 tab：「Outputs」（逐用例看产出 + 写反馈）与「Benchmark」（统计汇总 + 逐 eval + analyzer notes；`:553-556,1114-1322`）。
- **Delta vs shy**：shy 的 `render_report.py` 是**静态单文件、无服务器、不写回反馈**（`render_report.py:233-241,329-370`），**只渲染当前迭代**（无「上一轮产出/反馈」并列）。这是 **REQ-0019 的显式决策**（`REQ-0019:56,89`：不做服务器/反馈回写，因 opencode/TeleAgent 无稳定「打开浏览器+回传」链路）。

### 2.5 打包：`package_skill.py`（validation-gated `.skill`）

- 打 ZIP 换扩展名 `.skill`（`:87,91-101`）；**打包前强制** `quick_validate.validate_skill`（`:70-77`）；排除 `__pycache__/node_modules/*.pyc/.DS_Store`，且**只在技能根**排除 `evals/`（`:19-39`）。
- **Delta vs shy**：shy **完全没有打包能力**（grep `.skill|zipfile|package_skill` 仅命中无关单词，见 §4 验证）。此项 `skill-forge.md §4.1` 已提出；skill-creator 是**第二个来源**，额外贡献「打包前校验」与「根级排除 evals」。

### 2.6 校验：`quick_validate.py`

- 白名单 `{name, description, license, allowed-tools, metadata, compatibility}`（`:42`）；`name` kebab-case ≤64（`:64-71`）；`description` ≤1024 且不含 `<>`（`:79-84`）；`compatibility` ≤500（`:86-92`）。
- **Delta vs shy**：shy 的 `validate_skill.py` 是其**超集**：字段白名单一致（`validate_skill.py:28-30`，另加客户端扩展字段）、额外查 `name==目录名`（`:124`）、`README.md` 禁止（`:98`）、YAML 危险写法（`:106`）、**相对引用悬空**（`:56-77`）。skill-creator 的 `quick_validate.py` 既不检查引用也不检查目录名。**故此项为「已存在/更强」，不吸收**。

### 2.7 写作指导（`SKILL.md` 正文）

- **Pushy description**（`:67`）；三段式 anatomy（`:75-84`）；**渐进披露三级加载**（`:86-93`）；**SKILL.md <500 行、大 reference (>300 行) 加 TOC**（`:96-98`）；按 variant 组织 references（`:100-109`）。
- **「解释 why、少用 MUST」**（`:137-139,302`）；**「GENERATE THE EVAL VIEWER BEFORE evaluating inputs yourself」**（`:451`）；**「跨用例重复劳动 → 固化成 scripts/」**（`:304`）。
- **沟通校准**：按用户熟悉度决定是否解释 JSON/assertion 等术语（`:32-41`）。
- **Delta vs shy**：shy 的 `writing-skills.md` 覆盖了信息层级/按需披露/leading word/剪枝/完成判据（§3–§9），且有 skill-creator 没有的「否定句」「校准脆弱度」「何时拆分」。差距：**TOC 规则**、**description 100–200 词目标**、**沟通校准**（见 §4）。

### 2.8 平台分支（`SKILL.md:420-455`）

- **Claude.ai**：无子 agent → 串行自跑、跳过 baseline/benchmark、跳过 `claude -p` 优化（`:424-436`）。
- **Cowork**：有子 agent 但无浏览器 → `--static` 输出 HTML（`:447-455`）。
- **Delta vs shy**：**不通用**——opencode/TeleAgent 的能力路由写在 shy 的 `writing-skills.md:18-20`（opencode 忽略 `disable-model-invocation`、用 command 做人工入口）。此项**明确不吸收**。

---

## 3. 功能对照总表

| 功能域 | skill-creator | shy-skill-suite | 差距类型 |
| --- | --- | --- | --- |
| 需求活文档 REQ / frontier | 无 | **REQ-NNNN + 状态机 + `track_requirements.py`** | shy 独有 |
| 逼问 / 设计树 | 4 问 capture intent（`SKILL.md:51-54`） | **设计树 + frontier + 三动作**（`grilling.md`） | shy 更强 |
| 脚手架 | 无独立脚手架（模板内联） | `scaffold_skill.py`（只生成 SKILL.md） | 互补 |
| 触发评测集生成 | 手写 20 条 + HTML 签字（`:337-373`） | **`generate_eval_set.py` 启发式 + 复核** | 互补 |
| 自动化 description 优化环 | **`run_loop.py`（自动改写 + train/test）** | `optimize_description.py`（**不自改写**，agent 驱动） | **skill-creator 更强** |
| 真跑触发检测 | `claude -p` + `.claude/commands`（`run_eval.py`） | **`agent_runner.py`（opencode/teleagent/cmd，shell=False）** | shy 更强（客户端无关） |
| 评测集交互签字 | **`assets/eval_review.html`** | 无（手改 JSON） | **skill-creator 更强** |
| 评分者 | grader（含**评评测集** + **抽取主张**） | grader（逐断言 + 证据，无这两项） | **skill-creator 更强** |
| 盲测对比 | comparator（content/structure rubric） | comparator（rubric + **双序** + 只当信号） | shy 更强 |
| 基准聚合 | `aggregate_benchmark.py`（有 delta 反转 bug） | 同名（显式比率名、`--previous`、无 bug） | shy 更强 |
| analyzer 观测落地 | **`notes` 进 `benchmark.json` + viewer 渲染** | 只在 subagents.md 定义角色，无落地字段 | **skill-creator 更强** |
| 交互式 HTML viewer | **HTTP + 反馈回写 + 上一轮并列 + Benchmark tab** | `render_report.py`（静态、单轮、无回写） | **skill-creator 更强** |
| 报告渲染 | `generate_report.py`（description 优化专用） | `render_report.py`（评测 + findings 合一） | 各有取舍 |
| 上一轮回归对比 | viewer 并列上一轮**产出+反馈**；benchmark **无** delta | benchmark **有** `--previous` delta；报告无产出并列 | 互补 |
| 打包 / 发布 | **`package_skill.py`（校验门控 `.skill`）** | 无 | **skill-creator 独有** |
| 校验器 | `quick_validate.py`（基础） | `validate_skill.py`（超集：引用/目录名/YAML） | shy 更强 |
| TOC / 长 reference 规则 | **>300 行加 TOC**（`:98`） | 无显式规则 | **skill-creator 更强** |
| description 长度目标 | **100–200 词 + 硬限 1024**（`:132`） | 仅硬限 1024（`writing-skills.md:10`） | **skill-creator 更强** |
| 沟通校准 | **按用户熟悉度调节术语**（`:32-41`） | 无 | **skill-creator 独有** |
| 原生子 agent | `agents/` 3 个独立 md | `references/subagents.md` 角色表 | 结构差异 |
| 盲测/评估独立性 | 靠 agent 文件约束 | **显式「谁写谁不评」+ 副作用禁令** | shy 更强 |
| 先证伪再提意见 | 无 | **`reviewing-skills.md §3` + AGENTS.md** | shy 独有 |
| 自包含约束 | 靠 `.skill` 打包 | **显式原则 + 悬空引用检查** | shy 更强 |
| 平台 | Claude Code / Claude.ai / Cowork（`claude -p`） | **opencode / TeleAgent** | 目标不同 |

---

## 4. 借鉴候选（三类）

> 验证口径：每条候选都先跑「能否推翻『shy 已有该能力』」的检查，命令与结果内联。跑不了的整段标「静态阅读」。
> **淘汰数：共评估 18 个候选，10 个通过（进入借鉴清单），8 个被证伪**——其中 4 个是「shy 已有/更强」，4 个是「与 shy 既定决策或平台冲突」（后者列入 §4.3 明确不吸收）。

### 4.1 可直接吸收（7）

| 候选 | 来源 | 为什么值得 | 验证（命令 + 结果） |
| --- | --- | --- | --- |
| **grader 兼评「评测集质量」**（弱断言警告、遗漏结果、不可验证断言） | `agents/grader.md:9,68-79,171-183` | 一条「通过了但测不出东西」的断言比没有更糟（`grader.md:9`）；shy 的 grader 只判断言，不质疑断言 | `Get-ChildItem -Recurse shy \| Select-String "eval_feedback\|critique"` → **0 命中**；`subagents.md:23-28` 的 grader 职责无此项 |
| **grader 抽取并核验隐式主张**（factual/process/quality） | `agents/grader.md:43-59` | 预定义断言之外的事实错误（如「用了 2023 数据」）能被抓到 | `Select-String "claim\|抽取.*主张"` 于 shy → **0 命中** |
| **HTML 报告并列「上一轮产出 + 上一轮反馈」** | `generate_review.py:213-247`；`viewer.html:578-612` | shy 只有 `aggregate_benchmark.py --previous` 的**数字**对比；看「上一轮实际产出长什么样」缺失 | `Select-String "previous\|上一轮"` 于 `render_report.py` / `assets/report-template.html` → **0 命中**（命中的都在 aggregate_benchmark/optimize_description） |
| **analyzer 观测以 `notes` 持久化进 `benchmark.json` 并渲染** | `schemas.md:279-284,303`；`viewer.html:1308-1316` | shy 的 analyzer 结论只在对话里，没落字段、不进报告 | `Select-String "notes\|analyzer"` 于 shy `aggregate_benchmark.py` → **0 命中**；全 shy grep `"notes"` → **0 命中** |
| **TOC 规则：>300 行的 reference 加目录** | `SKILL.md:98` | shy 的 `reviewing-skills.md`（16 KB）等长文无目录，agent 检索成本高 | `Select-String "300\|目录\|table of contents"` 于 shy `references/` → 仅命中「目录」作 directory 义，**无 TOC 规则** |
| **description 目标「100–200 词（硬限 1024 字符）」** | `improve_description.py:132` | shy 只有硬限 1024，无「写多长合适」的量级感 | `Select-String "100-200\|字.*目标\|词"` 于 shy → **0 命中**（仅 ASCII_WORD 正则误命中） |
| **validation-gated `.skill` 打包**（打包前跑校验、根级排除 `evals/`） | `package_skill.py:19-39,70-101` | shy 无分发能力；`skill-forge.md §4.1` 已提 `.skill`，skill-creator 是第二来源，补「校验门控 + evals 根排除」 | `Get-ChildItem shy \| Select-String "\.skill\|zipfile\|package_skill"` → **无打包相关命中** |

### 4.2 需改造后吸收（3）

| 候选 | 来源 | 改造点 |
| --- | --- | --- |
| **自动化 description 改写环**（`run_loop.py` 的循环骨架：分层 train/test → 评估 → 让 LLM 改写 → 迭代 → 按 test 选优） | `run_loop.py:79-241` | shy 已有分层与「按 test 选优」（`optimize_description.py:173-190`），但改写者必须换成 **opencode/TeleAgent 的 LLM 调用**（把 `claude -p` 换成本仓 `agent_runner.py` 的 runner 层），且循环境里要保留 shy 的防泄漏盲化语义。**待决策**：与「报告只在 Step 8 出一次」的门禁如何共处 |
| **「先把产出给人看，再自己评」的强制顺序** | `SKILL.md:451`（GENERATE THE EVAL VIEWER *BEFORE* evaluating） | shy 的呈现门禁（`lifecycle.md:64`）是「用户确认前不回写 REQ」，方向不同；可补一条「生成报告后先交人看，再自行改进」的顺序约束。**待验证**：是否与 `reviewing-skills.md` Step 2 的对照取证冲突 |
| **按用户熟悉度调节术语**（沟通校准） | `SKILL.md:32-41` | 可并入 `SKILL.md` 的共用原则或 `writing-requirements.md §4`。属软约束，价值中等，**待决策** |

### 4.3 明确不吸收（4）

| 不吸收项 | 理由（含来源） |
| --- | --- |
| **HTTP 服务器 + `/api/feedback` 反馈回写** | shy `REQ-0019:56,74,89` **显式决策不做**：opencode/TeleAgent 无稳定「打开浏览器 + 回传」链路；shy 只做静态呈现，回写走 `/shy-apply`。 |
| **内嵌 run 原始产出**（base64 图片/PDF、SheetJS 渲染 XLSX，`generate_review.py:149-210`） | shy `REQ-0019:57,76` **显式列为范围外**（体积与客户端无关性考虑）。 |
| **优化过程中自动刷新报告 / 自动开浏览器**（`run_loop.py:278-279`） | 与 shy「报告只在复审 Step 8 生成一次、且由主 agent 打开」的门禁（`reviewing-skills.md:155`、`subagents.md:65`）冲突。 |
| **Claude 平台分支与机制**（`claude -p`、`.claude/commands/`、`available_skills`、`present_files`、Claude.ai/Cowork 段） | 目标平台不同：skill-creator 全仓 grep `opencode\|TeleAgent` = **0 命中**；shy 跑在 opencode/TeleAgent。 |

### 4.4 被证伪：shy 已有/更强（不重复吸收，4）

| 候选 | 证伪依据 |
| --- | --- |
| 盲测 comparator 的 rubric | shy `subagents.md:44-53` 已有 rubric + **双序抵消位置偏好** + 「信号非证据」，比 `comparator.md` 更严。 |
| frontmatter 校验 / `compatibility` 字段 | shy `validate_skill.py:28-30,127-140` 已覆盖并超出 `quick_validate.py`。 |
| 评测工作区布局 `iteration-N/eval-N/{with_skill,baseline}` | shy `running-evals.md:16-32` 同构，且 `aggregate_benchmark.py`/`render_report.py` 兼容更多别名。 |
| train/test 分层、按 test 选优防过拟合 | shy `optimize_description.py:37-55,181-190` 已实现（含「建议只用 train 失败」）。 |

---

## 5. 必须警惕：对标物自身的坑

> 以下均为**静态阅读源码**所得（本机无 Python，无法运行验证的情况已注明）。每条给出 `file:line`。

| # | 坑 | 证据 | 影响 |
| --- | --- | --- | --- |
| W1 | **聚合脚本要求的工作区布局与主流程不符**：SKILL.md 让 agent 把 `grading.json` 存到 `eval-<ID>/with_skill/grading.json`（`:180,225`），但 `aggregate_benchmark.py` 只认 `with_skill/run-*/grading.json`，无 `run-*` 就跳过该 config（`:101-113`）。按 SKILL.md:229 的命令跑按 SKILL.md 布局产出的工作区，**聚合为空** | `SKILL.md:180,225,229` vs `aggregate_benchmark.py:17-34,101-113` | 直接照抄会让「跑完评测却聚合不出 benchmark」 |
| W2 | **delta 方向被目录字母序反转**：脚本用 `sorted(eval_dir.iterdir())` 收集 config（`:101`），`baseline` 字典序 < `with_skill`，而 `aggregate_results` 把 `configs[0]` 当 primary、`configs[1]` 当 baseline（`:206-216`），于是 `delta = baseline - with_skill`；`schemas.md:272-276` 却把 delta 记为 with-minus-without（示例 `"+0.50"`） | `aggregate_benchmark.py:101,206-224` vs `schemas.md:272-276`；`@("baseline","with_skill") \| Sort-Object` → baseline 在前（已跑） | 报告里 delta 符号与直觉相反，`benchmark.md` 也把 Baseline 排第一列（`:288-304`） |
| W3 | **`assertions` vs `expectations` 术语漂移**：SKILL.md 的 `eval_metadata.json` 用 `assertions`（`:195,201,205`），同一节又说 grading.json 的 `expectations` 数组用 `text/passed/evidence`（`:225`）；`schemas.md:20` 的 evals.json 用 `expectations`，`schemas.md:92` 的 grading.json 也用 `expectations` | `SKILL.md:195,225`；`schemas.md:20,92` | 读者/实现容易把两个词当同一字段，或反之 |
| W4 | **脚本不跨平台**：`run_eval.py:108` 对子进程管道用 `select.select`（Windows 上只支持 socket，会抛错）；`generate_review.py:291` 调用 `lsof`（Windows 无）。本仓开发环境是 win32 | `run_eval.py:108`；`generate_review.py:288-306` | 照抄会在 Windows 直接不可用 |
| W5 | **死字段 `note`**：`improve_description.py:116` 读 `h.get("note")`，但 `run_loop.py` 构造的 history（`:121-137`）从不写 `note` | `run_loop.py:121-137`；`improve_description.py:116` | 无效代码/误导 |
| W6 | **从多轮退化为单轮的版本债**：`improve_description.py:158-162` 注释明说「旧 SDK 路径是真多轮；`claude -p` 是一次性，故把上次输出内联进新 prompt」 | `improve_description.py:20-47,158-182` | 文档若称「多轮」则与实现不符 |
| W7 | **`run_loop.py` 默认自动开浏览器、无 headless guard**（只有 `--report none` 能关）：`run_loop.py:278-279`；对比 shy 的 `render_report.py:244-257` 有 `SHY_NO_OPEN/CI/NO_BROWSER` | `run_loop.py:271-281` vs `render_report.py:244-266` | agent/无人环境会弹出浏览器打断 |
| W8 | **`quick_validate.py` 在主 SKILL.md 里从不被提及**：它只被 `package_skill.py:17,72` 内部调用，grep `SKILL.md` 无 `quick_validate` | `SKILL.md` grep → 0 命中；`package_skill.py:17,70-77` | 一个「孤儿工具」，用户不知道何时该跑 |
| W9 | **`benchmark.json` 的 `eval_name` 只在文档、脚本不产出**：`schemas.md:296` 说 `eval_name` 用作 viewer 分节标题，但 `aggregate_benchmark.py` 的 `load_run_results`/`generate_benchmark` 从不采集 `eval_name`（`:86-171,227-254`） | `schemas.md:296` vs `aggregate_benchmark.py:127-134,238-254` | viewer 只能回退到 eval_id，与文档承诺不符 |
| W10 | **许可元数据不一致**：上游仓库根**无**顶层 LICENSE（GitHub API `license: null`），但 README 称「Many skills ... Apache 2.0」；每个技能自带 `LICENSE.txt` | GitHub API `/repos/anthropics/skills` `license:null`；`LICENSE.txt:1-4` | 复用代码时许可判定需逐个技能确认 |

---

## 6. 一句话总结

**skill-creator 的价值在「自动化 + 交互呈现」**：它把「量化触发评测 → 交互式 viewer 让人评 → 按反馈改 → 自动迭代 description」这条链做成了可直接运行的脚本；**shy-skill-suite 的价值在「规范与证据纪律」**：需求活文档、三轴分离复审、先证伪、客户端无关真跑检测。可吸收的是它的**评测集元批评、主张核验、上一轮并列、analyzer notes 落地**这几处「让证据更硬」的细节，以及打包与 TOC/长度这类工程规范；**不吸收**它的服务器化交互、原始产出内嵌与 Claude 平台耦合，也**不能照抄**它的工作区布局与 delta 方向 bug。

---

## 7. 与既有调研的重叠（不重写，只指路）

- **`.skill` 打包**、**description 长度分层**、**comparator/grader 角色分工**、**aggregate_benchmark 同源** 这几处，`docs/shy-skill-suite/research/skill-forge.md`（§2.6、§2.7、§2.9、§4.1）已有结论；本报告只在 skill-creator 提供**额外证据**处补充（打包的校验门控与 `evals/` 根排除；`improve_description.py:132` 的 100–200 词；`run_loop.py` 的自动改写环）。
- `skill-forge.md §5` 记录的 `token_savings_ratio` 反向命名，是 **skill-forge** 的坑；skill-creator 用的是另一套字段名，但同样存在 §7-W2 的 **delta 方向反转**——两者是**不同**的坑，不要混为一谈。

---

## 8. 来源

### 8.1 对标仓库与 commit

- 上游：`https://github.com/anthropics/skills`，分支 `main`，commit **`34040c9c568585f6929bedeaad110ad08f079624`**（committer date 2026-09-10T19:44:08Z / 页面显示 2026-09-10；`pushed_at` 2026-09-10），许可：技能内 `LICENSE.txt` = Apache 2.0。
- 技能子树最后变更（GitHub commits API，`path=skills/skill-creator`）：
  - `SKILL.md` → `b0cbd3df1533`（2026-03-06，「drop ANTHROPIC_API_KEY requirement」）
  - `scripts/run_loop.py` → `b0cbd3df1533`（2026-03-06）
  - `eval-viewer/generate_review.py`、`scripts/aggregate_benchmark.py` → `3d5951151859`（2026-02-25）
  - `LICENSE.txt` → `b9e19e6f4477`（2026-04-20）
- 本地副本：`C:\Users\18907\.agents\skills\skill-creator\`。
- 对照物：`E:\code\my_projects\telecomshy-skills\skills\shy-skill-suite\`（`SKILL.md` + 7 `references/` + 9 `scripts/` + 4 `commands/` + 1 `assets/`）、`docs/shy-skill-suite/requirements/REQ-0001…0033`。

### 8.2 命令与结果

```text
# 1) 列技能树（本地）
Get-ChildItem -Recurse -File "C:\Users\18907\.agents\skills\skill-creator"   → 18 文件，≈225 KB
Get-ChildItem -Recurse -File "...\skills\shy-skill-suite"                    → SKILL.md + 7 refs + 9 scripts + 4 commands + assets

# 2) 直连 clone（失败）
git clone --depth 1 https://github.com/anthropics/skills.git C:\WINDOWS\TEMP\opencode\skill-creator-src
  → error: RPC failed; curl 28 Recv failure: Connection was reset / expected 'packfile'
  → 重试 180s 超时。改用 codeload。

# 3) 取 main SHA + 技能树
GET https://api.github.com/repos/anthropics/skills/commits/main
  → 34040c9c568585f6929bedeaad110ad08f079624
GET .../git/trees/main?recursive=1   → 确认 skills/skill-creator/ 存在且子文件与本地同名

# 4) 下载上游同 commit 源码
Invoke-WebRequest https://codeload.github.com/anthropics/skills/zip/34040c9c... -OutFile ...\skills-upstream.zip
  → 4,025,030 B；Expand-Archive → C:\WINDOWS\TEMP\opencode\skill-creator-src\skills-34040c9c.../

# 5) 本地 vs 上游逐文件比对
  先按原始 SHA256 → 18/18 DIFF（系 CRLF vs LF）
  再 CRLF→LF 归一化后 SHA256 → 18/18 SAME（结论：本地 = 上游 HEAD）

# 6) skill-creator 平台指纹
Get-ChildItem -Recurse -File skill-creator | Select-String "opencode|TeleAgent|teleagent"  → 0 命中
  (Select-String "claude" -AllMatches | Measure-Object).Count                              → 52

# 7) 对 shy 的证伪检查（关键几组）
Select-String "package_skill|\.skill|zipfile" 于 shy            → 无打包实现
Select-String "HTTPServer|serve_forever|feedback\.json|eval-viewer" 于 shy → 0
Select-String "run_loop|重写 description" 于 shy                → 仅 optimize_description.py:11「脚本本身不重写」
Select-String "eval_feedback|critique" 于 shy                   → 0
Select-String "claim|抽取.*主张" 于 shy                          → 0
Select-String "previous|上一轮" 于 shy render_report.py/template  → 0（仅 aggregate_benchmark/optimize_description 有 --previous）
Select-String '"notes"|notes' 于 shy aggregate_benchmark.py     → 0
Select-String "100-200|字数|词" 于 shy                          → 0（无长度目标）
Select-String "300|目录|table of contents" 于 shy references/   → 无 TOC 规则

# 8) 验证 delta 反转的排序前提
@("baseline","with_skill","without_skill","old_skill") | Sort-Object
  → baseline / old_skill / with_skill / without_skill  （baseline 恒在 with_skill 之前）
```

### 8.3 引用路径简写

- `skill-creator/SKILL.md` = `C:\Users\18907\.agents\skills\skill-creator\SKILL.md`
- `scripts/*.py`、`agents/*.md`、`references/schemas.md`、`eval-viewer/*`、`assets/eval_review.html` 均相对该技能根。
- shy 侧简写：`skills/shy-skill-suite/...` 与 `docs/shy-skill-suite/requirements/REQ-*.md`。
