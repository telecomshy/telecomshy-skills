# 运行评测（复审的执行层）

给复审的 **Step 1（触发）** 与 **Step 2（有效性）** 提供可执行脚本。脚本在 `scripts/` 下，纯标准库、无第三方依赖。

## 脚本

| 脚本 | 作用 |
| --- | --- |
| `generate_eval_set.py` | 从 `SKILL.md` 的 description 生成起手触发评测集（should-trigger / near-miss） |
| `optimize_description.py` | 按 train/held-out test 给 description 打分、给改进建议（选优按 test 分） |
| `agent_runner.py` | 把一条 prompt 跑过 agent 客户端并检测技能是否被触发（适配 opencode / TeleAgent） |
| `aggregate_benchmark.py` | 聚合 iteration 结果成 `benchmark.json` / `benchmark.md`（含 with_skill vs baseline 的 delta） |

## 工作区布局

评测结果放在**技能目录的同级**工作区，每轮一个 `iteration-N/`：

```
<skill>-workspace/
└── iteration-1/
    ├── eval-0/
    │   ├── eval_metadata.json          # {"eval_id":0,"eval_name":"...","prompt":"...","assertions":[...]}
    │   ├── with_skill/
    │   │   ├── grading.json            # {"pass_rate":0.0-1.0,"assertions":[{"text","passed","evidence"}]}
    │   │   └── timing.json             # {"total_tokens":int,"total_duration_seconds":float}
    │   └── baseline/                   # 与 with_skill 同构；新技能用无技能，改技能用旧版快照
    │       ├── grading.json
    │       └── timing.json
    └── benchmark.json / benchmark.md   # 由 aggregate_benchmark.py 产出
```

`baseline/` 也可写作 `without_skill/`（脚本兼容）。多轮试验用 `with_skill_0/`、`baseline_0/` 等。

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

## 命令

```bash
# 1) 生成起手评测集（启发式，需复核）
python "<SKILL_DIR>/scripts/generate_eval_set.py" <skill_dir> -o evals/evals.json

# 2) 给 description 打分（离线启发式）
python "<SKILL_DIR>/scripts/optimize_description.py" <skill_dir> --eval-set evals/evals.json -o reports/desc-opt.json

# 2') 真跑触发（opencode / TeleAgent）
python "<SKILL_DIR>/scripts/optimize_description.py" <skill_dir> --eval-set evals/evals.json \
  --runner opencode --detect <skill-name>

# 3) 聚合 benchmark
python "<SKILL_DIR>/scripts/aggregate_benchmark.py" <workspace>/iteration-1 \
  --skill-name <name> --previous <workspace>/iteration-0
```

## HTML 报告（呈现门禁）

复审 / 评测收工后，把结果渲染成**单文件自包含** HTML 交给人看（不回写 REQ、不自动优化，见 `reviewing-skills.md` Step 8）：

```bash
python "<SKILL_DIR>/scripts/render_report.py" <workspace>/iteration-1 --skill-name <name>
```

- 读 `benchmark.json` + `eval-*/` + `findings.json`（schema 见 `reviewing-skills.md`），输出 `<iteration>/report.html`（`--out` 可改）。
- **生成后默认自动用浏览器打开**；关闭方式（任一即可）：`--no-open`，或环境变量 `SHY_NO_OPEN` / `CI` / `NO_BROWSER` 为真值。无显示环境不报错，仍写出文件。
- **报告是复审的终局产物**：只在 `reviewing-skills.md` Step 8 生成一次。复审中途、以及**子 agent 测试渲染**时，一律关闭自动打开（否则会中途弹浏览器打断用户）。
- 单文件、无服务器、无外部资源：opencode / TeleAgent 直接打开即可。
- 只有 findings（无 benchmark）或反之都能出；两者都无 → 退出码 1。

## runner 适配（客户端无关）

| runner | 命令来源 | 说明 |
| --- | --- | --- |
| `heuristic` | 无 | 离线关键词 / 汉字二元组重叠，仅作起手，**不是证据** |
| `opencode` | 默认 `opencode run "{prompt}"` | 也可用 `--cmd` 覆盖 |
| `teleagent` | `--cmd` 或环境变量 `TELEAGENT_RUN_CMD` | TeleAgent 的调用方式因环境而异，用模板注入 |
| `cmd` | `--cmd`（必须含 `{prompt}`） | 任意客户端 |

**检测**：`--detect` 传技能名或正则；命中命令的 stdout/stderr 即判为触发。客户端日志格式不同，检测串可能需要按客户端微调。

**命令模板按 argv 切分、不经 shell**（`shell=False`）：`{prompt}` 始终作为**单个参数**注入，模板里的 `&` / `|` / 反引号不会被解释；代价是模板不能用管道、重定向等 shell 语法（需要时写一个包装脚本，再让 `{prompt}` 调用它）。

## 边界

- 起手评测集是**启发式**，必须人工或 agent 复核后再用；评测集质量决定评测结论质量。
- 真跑模式依赖客户端的**非交互命令**（不能弹 TTY）。
- 对照基线（with_skill vs baseline）是硬要求：**只有 delta 才算证据**，单跑不算。
- 启发式分数只用于排序候选，**不能**当作"技能有效"的证据。
