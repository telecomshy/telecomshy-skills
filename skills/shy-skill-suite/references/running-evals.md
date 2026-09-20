# 运行评测（独立取证路径）

评测（eval）是**独立、user-invoked** 的取证路径（`/shy-eval`）：只产触发率 / with_skill vs baseline 的 delta，**不改技能、不提修复建议**。它给复审的 Step 1（触发）与 Step 2（有效性）提供**可选**证据——复审默认静态，缺证据显式降级，不强制跑 eval。脚本在 `scripts/` 下，纯标准库、无第三方依赖。

## 独立评测路径（`/shy-eval`）

`/shy-eval <skill> [触发|有效性|两者]`（默认两者）：加载本技能 → 调 `optimize_description.py`（触发轴）/ `run_effectiveness.py`（有效性轴）→ `aggregate_benchmark.py` 聚合 → `render_report.py` 渲染并打开报告。**与 `/shy-review` 互不调用**。

- **必须钉模型**：全程 `--model <provider>/<id>`，并把模型 ID 记进证据；不钉模型的结论不可复现（见下「必须钉模型」）。
- 产物落 `<skill>-workspace/iteration-N/`（N = 现有最大编号 + 1，**不覆盖**旧目录；过期证据**不删**，供追溯）。
- 触发轴：`optimize_description.py … --evidence-ws <iteration-N> --model <id>`；有效性轴：`run_effectiveness.py … --skill-dir <skill_dir> --model <id>`；聚合：`aggregate_benchmark.py <iteration-N> --skill-dir <skill_dir> --model <id>`。三者都会把指纹写进 `<iteration-N>/evidence.json`。

## 指纹（判「本轮证据」）

`evidence.json` 记录**分轴指纹** + 模型 ID + 时间，供复审判断手上的 eval 是不是**当前技能版本**产的：

- **触发轴** = `hash(description)`——改 `SKILL.md` 正文不作废触发证据，改 `description` 才作废。
- **有效性轴** = `hash(SKILL.md + references/ + scripts/ + assets/ + evals/effectiveness.json)`——对任何技能文件改动敏感（刻意的保守取向）。

确定性（否则证据永远"不匹配"）：文件按相对路径排序、路径统一为 `/`、只 hash 内容（不掺 mtime / 绝对路径）。算指纹：`python "<SKILL_DIR>/scripts/skill_fingerprint.py" --skill-dir <skill_dir> [--axis trigger|effectiveness]`。

**复审读证据的规则**：同技能工作区存在 eval 且**指纹匹配当前技能** → 可引用为该轴证据、标注来源；指纹**不匹配**（技能自 eval 后已改）→ 标「过期证据（技能已变更）」、行为轴降级，**可**产出「待验证 + 建议跑 `/shy-eval`」的 finding（把取证显式交给用户）。**无 `evidence.json` 的旧证据一律视为过期**（保守）。

## 脚本

| 脚本 | 作用 |
| --- | --- |
| `generate_eval_set.py` | 从 `SKILL.md` 的 description 生成起手触发评测集（should-trigger / near-miss） |
| `optimize_description.py` | 按 train/held-out test 给 description 打分、给改进建议（选优按 test 分） |
| `agent_runner.py` | 把一条 prompt 跑过 agent 客户端并检测技能是否被触发（适配 opencode / TeleAgent） |
| `run_effectiveness.py` | 行为轴有效性对照：with_skill / baseline 两臂跑任务式用例，隔离根 + 技能屏蔽 + 污染扫描 |
| `aggregate_benchmark.py` | 聚合 iteration 结果成 `benchmark.json` / `benchmark.md`（含 with_skill vs baseline 的 delta） |

## 工作区布局

评测结果放在**技能目录的同级**工作区，每轮一个 `iteration-N/`：

```
<skill>-workspace/
└── iteration-1/
    ├── eval-0/
    │   ├── eval_metadata.json          # {"eval_id":0,"eval_name":"...","prompt":"...","assertions":[...]}
    │   ├── with_skill/
    │   │   ├── grading.json            # pass_rate + assertions[] + claims[] + eval_feedback[]（见下）
    │   │   └── timing.json             # {"total_tokens":int,"total_duration_seconds":float}
    │   └── baseline/                   # 与 with_skill 同构；新技能用无技能，改技能用旧版快照
    │       ├── grading.json
    │       └── timing.json
    ├── analyzer_notes.json             # 可选，{"notes":["..."]}；由 analyzer 产出、reviewing Step 8
    └── benchmark.json / benchmark.md   # 由 aggregate_benchmark.py 产出（notes 会并入）
```

`baseline/` 也可写作 `without_skill/`（脚本兼容）。多轮试验用 `with_skill_0/`、`baseline_0/` 等。

`grading.json` 字段（角色定义见 `subagents.md` 的 grader）：`pass_rate`；`assertions[]{text,passed,evidence}`（逐条断言）；`claims[]{type,passed,evidence}`（断言之外的**隐式主张**核验，`type ∈ {factual,process,quality}`）；`eval_feedback[]`（对**评测集本身**的批评：弱断言 / 遗漏结果 / 不可验证断言）。

`analyzer_notes.json` 由 analyzer 写入，`aggregate_benchmark.py` 自动读到 `benchmark.json.notes` 并渲染进报告——结论不落盘就等于没留证据。

## 评测集 schema（`evals/evals.json`）

```json
{
  "skill_name": "<name>",
  "evals": [
    {
      "eval_id": 0,
      "eval_name": "trigger-direct-0",
      "prompt": "用户会真的这么说的 prompt",
      "input_files": [],
      "assertions": [{"name": "skill-activated", "check": "「<name>」技能被触发", "weight": 1.0}],
      "should_trigger": true
    }
  ]
}
```

**评测集留在技能里**：`evals/evals.json`（相对技能根）是随技能入库的起手评测集——行为结论要可复现，评测集就不能只躺在被 gitignore 的工作区里。工作区 `iteration-N/` 是生成物，不入库。

## 命令

```bash
# 1) 生成起手评测集（启发式，需复核）
python "<SKILL_DIR>/scripts/generate_eval_set.py" <skill_dir> -o evals/evals.json

# 2) 给 description 打分（离线启发式）
python "<SKILL_DIR>/scripts/optimize_description.py" <skill_dir> --eval-set evals/evals.json -o reports/desc-opt.json

# 2') 真跑触发——每条默认跑 3 次、按触发率 ≥ 0.5 判触发；钉模型 + 隔离 cwd + 并发
#     单跑有抖动（同一 description 换一次跑，误触发的题会变），别用单跑结论改 description
python "<SKILL_DIR>/scripts/optimize_description.py" <skill_dir> --eval-set evals/evals.json \
  --runner cmd --cmd 'opencode run --model <provider>/<id> "{prompt}"' \
  --detect <skill-name> --detect-mode skill-line --trials 5 --workers 4 \
  --cwd <临时目录> --isolate-cwd --verbose

# 3) 聚合 benchmark
python "<SKILL_DIR>/scripts/aggregate_benchmark.py" <workspace>/iteration-1 \
  --skill-name <name> --previous <workspace>/iteration-0
```

## 有效性对照（with_skill vs baseline）

触发轴问"会不会用"，有效性轴问"用了有没有更好"。用 `run_effectiveness.py` 跑：**任务式** prompt（不点名技能）、每臂 × 每用例 × `--trials` 次，产出与工作区布局同构（`eval-<id>/<arm>_<t>/`）。

```bash
# with_skill 臂
python "<SKILL_DIR>/scripts/run_effectiveness.py" --arm with_skill \
  --cases "<SKILL_DIR>/evals/effectiveness.json" --ws <workspace>/iteration-N \
  --model <provider>/<id> --workers 3

# baseline 臂：整批屏蔽目标技能 + 易抢答的其他技能（跑完自动恢复）
python "<SKILL_DIR>/scripts/run_effectiveness.py" --arm baseline \
  --cases "<SKILL_DIR>/evals/effectiveness.json" --ws <workspace>/iteration-N \
  --model <provider>/<id> --workers 3 \
  --skills-dir "<技能目录>" --disable-skills shy-skill-suite,skill-creator,writing-for-agents
```

**隔离（硬要求）**：每批在系统临时目录新建**唯一隔离根**，所有运行目录都在其下、跑完删除（`--keep` 保留）。**不要**把运行目录放进共享目录——agent 会上溯父目录搜索；实测 baseline 从共享 temp 的旧副本里读到了技能内容（REQ-0069）。

**污染可见化**：每次运行把扫描结果写进 `timing.json`——`loaded_skills`（`Skill "名"` 加载行）与 `contamination{foreign_reads, other_skills_loaded, target_loaded, ancestor_scans}`。**判读规则**：baseline 出现 `target_loaded`、或 `foreign_reads` 命中目标技能的任何副本 ⇒ 该 run 作废或降权；出现 `other_skills_loaded` ⇒ 该 run 是"别的指导"，不是"无指导"。污染 run 一律在报告里点名，**不得静默计入 delta**。

**无技能 baseline 的天花板**（见「边界」）：技能内容在磁盘上可被搜到 ⇒ baseline 天然偏弱。要"干净的无技能对照"须同时做到：技能源码不在可搜索路径 + 屏蔽其他技能；做不到时优先用**旧版快照**做 baseline。

## HTML 报告（评审路 / 评测路的呈现）

**评测路**（`/shy-eval`）收尾时渲染评测报告（`benchmark.json` + `eval-*/`）；**评审路**（`/shy-review`，用户主动触发）收尾时渲染**含 findings 的**报告供**分拣**（立即修 / 以后修 / 丢弃）；实现路不出报告（见 `reviewing-skills.md` Step 8）：

```bash
python "<SKILL_DIR>/scripts/render_report.py" <workspace>/iteration-1 --skill-name <name>

# 页面直接提交分拣（可选；默认静态单文件）
python "<SKILL_DIR>/scripts/render_report.py" <workspace>/iteration-1 --skill-name <name> --serve
```

- 读 `benchmark.json` + `eval-*/` + `findings.json`（schema 见 `reviewing-skills.md`），输出 `<iteration>/report.html`（`--out` 可改）。
- **生成后默认自动用浏览器打开**；关闭方式（任一即可）：`--no-open`，或环境变量 `SHY_NO_OPEN` / `CI` / `NO_BROWSER` 为真值。无显示环境不报错，仍写出文件。
- **报告只在 Step 8 生成一次**（见 `reviewing-skills.md` Step 8）：复审中途、以及**子 agent 测试渲染**时，一律关闭自动打开（否则会中途弹浏览器打断用户）。
- 单文件、无服务器、无外部资源：opencode / TeleAgent 直接打开即可。
- **分拣只在 `--serve` 模式出现**：每条 finding 带三选一（立即修 / 以后修 / 丢弃，默认立即修），报告末尾只有一个「提交给 agent」按钮 → `POST /triage` 写**与报告同目录**的 `triage.json`（每项 `{id, choice, note, location}`；`id` 为报告渲染顺序，回写按 `location` 对应 `findings.json`），服务随即退出。无复制 / 下载 / 清空。
- **静态报告（无 `--serve`）是只读归档**：无分拣控件、无按钮，**不会自动回传任何数据**；提交只在 `--serve` 下由用户点击触发。`--serve-timeout`（默认 1800 秒）控制等待；超时未提交 → 服务退出、静态 `report.html` 仍可用。
- 只有 findings（无 benchmark）或反之都能出；两者都无 → 退出码 1。

## runner 适配（客户端无关）

| runner | 命令来源 | 说明 |
| --- | --- | --- |
| `heuristic` | 无 | 离线关键词 / 汉字二元组重叠，仅作起手，**不是证据** |
| `opencode` | 默认 `opencode run "{prompt}"` | 也可用 `--cmd` 覆盖 |
| `teleagent` | `--cmd` 或环境变量 `TELEAGENT_RUN_CMD` | TeleAgent 的调用方式因环境而异，用模板注入 |
| `cmd` | `--cmd`（必须含 `{prompt}`） | 任意客户端 |

**检测**：`--detect` 传技能名或正则；**流式检测**——逐行读取输出，命中即结束会话（正例常会继续干活到超时，等它跑完纯属浪费，且超时会误判未触发）。跨行正则可用的前提不成立（逐行匹配）；客户端日志格式不同，检测串可能需要按客户端微调。

**命令模板按 argv 切分、不经 shell**（`shell=False`）：`{prompt}` 始终作为**单个参数**注入，模板里的 `&` / `|` / 反引号不会被解释；代价是模板不能用管道、重定向等 shell 语法（需要时写一个包装脚本，再让 `{prompt}` 调用它）。

**评测隔离（`--isolate-cwd`）**：嵌套 agent 会在 `--cwd` 里写文件；共用目录会让后跑的用例看到前一轮的产物、结果失真（实测同一负例在脏/净目录里触发率 1.0 vs 0/3）。真跑评测一律加 `--isolate-cwd`——每次运行在 `--cwd` 下新建空目录、跑完即删。

**必须钉模型**：`opencode run` 的**默认模型解析不可控**——实测嵌套会话 `model=None`、落到免费模型后循环 / 超时 / 不加载技能（整批数据作废），且桌面所选模型不会传播给 CLI。真跑一律用 `--cmd 'opencode run --model <provider>/<id> "{prompt}"'`，并把**所用模型 ID** 写进报告 / 迭代记录；不钉模型的结论不可复现。

**并发与检测模式**：`--workers`（默认 4）并发跑各 (查询, trial)——每次预测一个独立子进程，互不共享状态（实测 3 并发 11.7s vs 串行 36s）；`--detect-mode`（默认 `auto`：opencode → `skill-line`，其余 `substring`）——`skill-line` 只认 `Skill "名"` 加载行，防"只是提到名字"被算作触发。单次超时默认 **120s**（实测检测中位 ~15s，但存在"晚触发"用例——数十 KB 输出后才加载技能——且并发会抬高单次延迟；60s 会把它们误杀成假阴性。超时按未触发 fail-fast）。

## 边界

- 起手评测集是**启发式**，必须人工或 agent 复核后再用；评测集质量决定评测结论质量。
- 真跑模式依赖客户端的**非交互命令**（不能弹 TTY）。
- 对照基线（with_skill vs baseline）是硬要求：**只有 delta 才算证据**，单跑不算。
- 启发式分数只用于排序候选，**不能**当作"技能有效"的证据。
- **token 可能采不到**：客户端输出里解析不出 usage 时 `avg_tokens = 0`、`token_ratio` 恒为 **1.0**——那是"**没测到**"，不是"没花费"。**`token_ratio` 无效，不得当结论**。耗时同理：单次超时 / 重试会污染 `time_ratio`，别过度解读。
- **baseline 怎么定**：**改技能用旧版快照**（改前的版本）。**"无技能" baseline 只适用**于内容不可在磁盘搜到、且不依赖读文件的技能——否则权限放开时 agent 会用 `glob/grep/read` 把技能源码搜出来作答（**对照被污染**），禁止读盘又会让 with_skill 失效（技能要读 `references/`）。
