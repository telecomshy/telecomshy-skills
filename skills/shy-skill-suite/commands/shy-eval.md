---
description: 技能开发套件 · 独立评测取证（触发率 / 有效性对照，不改技能、不提修复建议）
---

调用 `skill` 工具加载 `shy-skill-suite` 技能，然后按 `references/running-evals.md` 的「独立评测路径」执行。**只取证、不改技能、不提修复建议**——修复走 `/shy-review` → 分拣 → 用户确认后实施。

参数：`$ARGUMENTS` 形如 `<skill> [触发|有效性|两者]`，轴默认**两者**。

1. 解析目标技能目录与轴；工作区取 `<skill>-workspace/iteration-N`（N = 现有最大编号 + 1，不覆盖旧目录）。
2. **必须钉模型**（`running-evals.md` 硬要求）：全程用 `--model <provider>/<id>`，并把模型 ID 记进证据；不钉模型的结论不可复现。
3. **触发轴**：`python "<SKILL_DIR>/scripts/optimize_description.py" <skill_dir> --eval-set <skill_dir>/evals/evals.json --runner cmd --cmd 'opencode run --model <id> "{prompt}"' --detect <skill-name> --detect-mode skill-line --trials 5 --workers 4 --cwd <临时目录> --isolate-cwd --evidence-ws <workspace>/iteration-N --model <id> --out <workspace>/iteration-N/desc-opt.json`。
4. **有效性轴**：`python "<SKILL_DIR>/scripts/run_effectiveness.py" --arm with_skill` 与 `--arm baseline` 各跑一次，`--cases <skill_dir>/evals/effectiveness.json --ws <workspace>/iteration-N --skill-dir <skill_dir> --model <id>`；baseline 用 `--skills-dir` + `--disable-skills` 屏蔽目标技能与易抢答技能（如 `skill-creator,writing-for-agents`）。
5. 聚合：`python "<SKILL_DIR>/scripts/aggregate_benchmark.py" <workspace>/iteration-N --skill-name <name> --skill-dir <skill_dir> --model <id>` → `benchmark.json`；证据落在 `<workspace>/iteration-N/evidence.json`（两轴指纹 + 模型 + 时间）。
6. 渲染并打开 eval 报告：`python "<SKILL_DIR>/scripts/render_report.py" <workspace>/iteration-N --skill-name <name>`（默认自动打开；子 agent / 测试加 `--no-open` 或设 `SHY_NO_OPEN=1`）。
7. **与 `/shy-review` 互不调用**：本命令不产 findings、不分拣；复审另由用户触发。

技能 / 轴：$ARGUMENTS
