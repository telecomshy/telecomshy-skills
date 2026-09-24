---
description: 技能开发套件 · 复审（按需引用评测），出一份 HTML 报告并打开（不改行为；台账机械项当轮结清）
---

调用 `skill` 工具加载 `shy-skill-suite` 技能，然后：

1. 按 `references/reviewing-skills.md` 做三轴复审，产出 `findings.json`；**默认静态**，同目录存在**指纹匹配当前技能**的 eval 才引用（见 `references/running-evals.md` 的「指纹」），无则标「（静态）待验证」/「过期证据」；
2. **不强制跑 eval**——需要取证时，另由用户触发 `/shy-skill-eval`；
3. 用 `python "<SKILL_DIR>/scripts/render_report.py" <workspace>/iteration-N --skill-name <name> --serve` 渲染并打开报告（页面可直接提交分拣；不加 `--serve` 为只读归档）。

**不自动修改技能行为 / findings**；**台账（自洽 / 卫生）机械项由 agent 当轮结清**（谁修 / 何时 / 机械 vs 决策的边界见 `references/reviewing-skills.md` Step 8）——findings 等你确认分拣后，再按所选实施一次即停（见 `references/lifecycle.md` 阶段 3 → 4）。

**技能 / 工作区必填**：`$ARGUMENTS` 缺失时**直接询问用户**要复审哪个技能（不默认全仓）。

技能 / 工作区：$ARGUMENTS
