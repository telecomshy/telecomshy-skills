---
description: 技能开发套件 · 复审 + 评测，出一份 HTML 报告并打开（不自动改）
---

调用 `skill` 工具加载 `shy-skill-suite` 技能，然后：

1. 按 `references/reviewing-skills.md` 做三轴复审，产出 `findings.json`；
2. 按 `references/running-evals.md` 跑评测（触发率 + with_skill vs baseline），有数据则聚合 `benchmark.json`；
3. 用 `scripts/render_report.py` 渲染**一份** HTML 报告（默认自动打开）。

**只呈现、不落盘、不自动修改**——落盘要等用户显式触发 `/shy-apply`。

技能 / 工作区：$ARGUMENTS
