---
description: 技能开发套件 · 复审 + 评测，出一份 HTML 报告并打开（不自动改）
---

调用 `skill` 工具加载 `shy-skill-suite` 技能，然后：

1. 按 `references/reviewing-skills.md` 做三轴复审，产出 `findings.json`；
2. 按 `references/running-evals.md` 跑评测（触发率 + with_skill vs baseline），有数据则聚合 `benchmark.json`；
3. 用 `python "<SKILL_DIR>/scripts/render_report.py" <workspace>/iteration-N --skill-name <name> --serve` 渲染并打开报告（页面可直接提交分拣；不加 `--serve` 为只读归档）。

**只呈现、不回写 REQ、不自动修改**——回写要等用户显式触发 `/shy-apply`。

技能 / 工作区：$ARGUMENTS
