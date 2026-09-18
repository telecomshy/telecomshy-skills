---
id: REQ-0024
title: 为 shy-skill-suite 取真实行为证据（触发率 + with/baseline delta）
skill: shy-skill-suite
status: done
kind: feature
iteration: 2
created: 2026-09-16
updated: 2026-09-17
blocked_by: [REQ-0022]
related: [REQ-0010, REQ-0019, REQ-0021]
---

# REQ-0024 为 shy-skill-suite 取真实行为证据

## 问题与目标

2026-09-16 复审行为轴 **P1**：`shy-skill-suite` 没有任何真实行为证据——触发（`REQ-0021` 的逼问触发词、`REQ-0010` 的收窄）只有描述层面的判断；整技能也没有 with_skill vs baseline 的 delta。按 `reviewing-skills.md` Step 2「只有 delta 才算证据」，当前只能说技能"没坏"，**不能说"有效"**。

证据（复审时）：
- 本会话 `available_skills` 不含 `shy-skill-suite`（安装晚于会话启动）→ 无法取触发轨迹。
- `REQ-0020` / `REQ-0021` 的验收已自标「待验证」。

目标：部署后取到**真实轨迹**：触发率（正例 + near-miss）与至少一条 with/baseline 对照。

## 触发与分支

- 复审 Step 1（触发审查）/ Step 2（有效性审查）。
- 用户说"实测一下 / 跑一遍看触发准不准"。

## 行为与步骤

1. 重启 opencode 后（技能与命令已装入 `~/.config/opencode/`），用合并入口 `/shy-review` 对 `shy-skill-suite` 自己跑：
   - **触发**：`scripts/optimize_description.py <skill_dir> --eval-set evals/evals.json --runner opencode --detect shy-skill-suite` 取真实触发率；正例（逼问 / 复审 / 写需求）+ near-miss（"澄清这段代码要做什么"）。
   - **对照**：2–3 条真实 prompt，各跑 with_skill 与 baseline（无技能），记录 pass_rate / token / 耗时；`aggregate_benchmark.py` 聚合。
2. 把触发率与 delta 写入 `<skill>-workspace/` 的 `findings.json` / `benchmark.json`，并由 `render_report.py` 出报告。
3. 回写本 REQ：勾选验收、追加迭代记录。

## 脚本与资源

- 用 `scripts/generate_eval_set.py`（起手集，需复核）、`optimize_description.py --runner opencode`、`agent_runner.py`、`aggregate_benchmark.py`、`render_report.py`。
- 工作区：`skills/shy-skill-suite-workspace/`。
- 不改技能文件（除非证据指向要改，另开 REQ）。

## 降级与边界

- 无可用 agent runner（opencode 非交互不可用）→ 标「待验证」，**不伪造**触发率/delta。
- 对照的 baseline「无技能」在本机指"不加载 shy-skill-suite"；须确保 baseline 真没加载（`subagents.md` 的 executor 规则）。
- 评测集是启发式起手集，须人工/agent 复核后再用其结论。

## 验收标准

- [x] 触发正例有真实轨迹（命令 + 输出 + 命中技能的证据）。（2026-09-17：`optimize_description.py --runner cmd` 真跑，5 正例全过；`raw/with_skill-*.json` 含 `"tool":"skill","input":{"name":"shy-skill-suite"}`） — （episode）
- [x] near-miss 有真实轨迹（命令 + 输出 + 未落盘/未进入技能流程）。（2026-09-17：5 条 near-miss，4 条正确未触发；#101 单跑触发 → 开 `REQ-0039`，**后经 3×3 复现判定为噪声**，见该 REQ） — （episode）
- [x] 至少 1 条 `benchmark.json` 含 with_skill vs baseline 的 `pass_rate` / `token_ratio` / `time_ratio`。（2026-09-17：`iteration-1/benchmark.json`，1.0 vs 0.33；**token 未采集，`token_ratio` 无效**） — （episode）
- [x] `<skill>-workspace/report.html` 的评测区非"无数据"。（2026-09-17：`iteration-1/report.html` 显示 100% / 33% / 3.0x） — （episode）
- [x] 结论（触发率、delta、是否有效）写入本 REQ 迭代记录；跑不了的项明确标「待验证」。（见第 3 行与「备注」的限制清单） — （episode）

## 范围外

- 不改命令 / 脚本 / 文档（发现要改的另开 REQ）。
- 不做跨平台评测。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（复审行为轴 P1） | — | 待开工 |
| 2 | 2026-09-17 | **尝试取证，被环境阻塞**（**归因后被更正**，见第 3 行）：`opencode run` 报 `TypeError: fn3 is not a function`（`src/plugin/index.ts:87`，rc=1）。当时判为 `opencode-vision` 插件，试过 `OPENCODE_CONFIG` 无插件配置、`"plugin": []` 覆盖均无效。 | `opencode run "只回复两个字母：OK"` → rc=1；日志 `...\log\2026-09-17T143909.log` | 待解除；不伪造触发率/delta |
| 3 | 2026-09-17 | **取证完成**。① **更正第 2 行归因**：真凶是环境变量 `OPENCODE_CLIENT` / `OPENCODE_SERVER_PASSWORD` 泄漏给子进程（清掉后 `opencode run` → `OK`、rc=0）；`opencode-vision` 插件按用户要求已卸载。② **触发轴**：`optimize_description.py --runner cmd --cmd "<opencode> run {prompt} --format json" --detect shy-skill-suite`，10 条（5 正 + 5 near-miss，**人工重写**，未用启发式起手集），train 6/6、test 3/4 → **9/10 = 0.9**；唯一失败 #101「什么是 Agent Skills 标准？」**误触发**（过宽）→ 已开 `REQ-0039`。③ **有效性 delta（旧版快照口径）**：with_skill = 当前工作树 / baseline = git `HEAD`，3 条踩改动面的任务 → **1.0 vs 0.33（improvement 3.0x）**。 | 触发：`iteration-1/raw/desc-opt.json`；delta：`iteration-1/benchmark.json` + `report.html`（评测区非空）+ `raw/*.json` | **done**；遗留 4 条限制见「备注」；near-miss 过宽转 `REQ-0039` |

## 备注 / 待办

- **取证结果（2026-09-17）**：触发 **0.9**（9/10）；delta **3.0x**（1.0 vs 0.33）。
- **#101 更正**：「什么是 Agent Skills 标准？」的单跑触发**后经 3×3 复现判定为噪声**（旧、新 description 均 0/3），**不是**稳定的过宽；`REQ-0039` 的收紧已回退（out-of-scope）。**教训：触发类结论必须多条多次，1 次不算数**。
- **限制（当证据用必须一并带上）**：
  1. **样本小**：触发 10 条 × 1 次、delta 3 题 × 1 次；技能自己要求 8–10 条 × 3 次。属**软证据**。
  2. **token 未采集**：opencode 的 `--format json` 未解析出 usage → `token_ratio` 恒为 1.0，**无效，别当结论**。
  3. **耗时别过度解读**：`time_ratio 0.37` 中 baseline 有一次 25s（它在试探搜盘被拒），算噪声。
  4. **有效区分只有 2/3 题**：`p2-blocking` 两臂都过，不区分。
- **方法论发现（值得进 `running-evals.md`）**：对"内容可在磁盘搜索、且必须读文件才能工作"的技能，**"无技能 baseline"无法用权限隔离**——`permission: allow` 时 baseline 会用 `glob/grep/read` 把技能源码搜出来（污染）；禁止读盘又会让 with_skill 失效。故改用**旧版快照**口径（技能自己 `running-evals.md:26` 的规定：改技能用旧版快照），回避了这个死结。
- **环境更正**：`opencode run` 阻塞的真凶是环境变量 `OPENCODE_CLIENT` / `OPENCODE_SERVER_PASSWORD` 泄漏给子进程，**不是** `opencode-vision` 插件；插件已按用户要求卸载。
- 来源：2026-09-16 复审 findings #1（行为轴 P1）。
- 依赖 `REQ-0022`：用合并后的单一入口跑，避免 review/eval 两套。
- 这是**取证**任务，不是改代码；产出是 `findings.json` / `benchmark.json` / 报告。
