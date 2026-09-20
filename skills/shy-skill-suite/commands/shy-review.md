---
description: 技能开发套件 · 复审（按需引用评测），出一份 HTML 报告并打开（不自动改）
---

调用 `skill` 工具加载 `shy-skill-suite` 技能，然后：

1. 按 `references/reviewing-skills.md` 做三轴复审，产出 `findings.json`；**默认静态**，同目录存在**指纹匹配当前技能**的 eval 才引用（见 `references/running-evals.md` 的「指纹」），无则标「（静态）待验证」/「过期证据」；
2. **不强制跑 eval**——需要取证时，另由用户触发 `/shy-eval`；
3. 用 `python "<SKILL_DIR>/scripts/render_report.py" <workspace>/iteration-N --skill-name <name> --serve` 渲染并打开报告（页面可直接提交分拣；不加 `--serve` 为只读归档）。

**只呈现、不回写 REQ、不自动修改**——回写要等用户显式触发 `/shy-apply`。

技能 / 工作区：$ARGUMENTS
