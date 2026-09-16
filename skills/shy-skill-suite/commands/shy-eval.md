---
description: 技能开发套件 · 跑评测并生成 HTML 报告（不自动优化）
---

调用 `skill` 工具加载 `shy-skill-suite` 技能，然后按 `references/running-evals.md` 跑评测（with_skill vs baseline），并用 `scripts/render_report.py` 渲染 HTML 报告。

**只呈现结果，不自动优化**；落盘要等用户显式触发 `/shy-apply`。

技能 / 工作区：$ARGUMENTS
