---
description: 技能开发套件 · 开始开发新技能（逼问 → 落需求 → 起骨架，同一流程）
---

调用 `skill` 工具加载 `shy-skill-suite` 技能，然后进入**同一条**开发流程（与自然语言触发完全一致，不分叉）：**逼问 → 落需求 → 起骨架**。

技能名**可选**：`$ARGUMENTS` 给了就直接作为目标技能名；没给就**先问用户**要技能名（**不默认**），拿到后再往下走。

1. **逼问**：按 `references/grilling.md` 建设计树、一轮问完 frontier、每问附建议答案，直到 frontier 空（用户确认理解一致）。
2. **落需求**：按 `references/writing-requirements.md` 把逼问结论写成 `docs/<skill>/requirements/REQ-0001-<slug>.md`（`status: ready`），并在「备注 / 待办」记一行逼问记录。
3. **起骨架**：跑 `python "<SKILL_DIR>/scripts/scaffold_skill.py" <skill> --path skills --project --description "<触发描述>"` 一次建齐**技能包 + 开发层**（`skills/<skill>/SKILL.md`、`docs/<skill>/requirements/`、`.gitignore` 条目）；再按 `references/writing-skills.md` 写 `SKILL.md`，收尾按 `references/lifecycle.md` 阶段 2 跑 Gate。

阶段判据与收尾见 `references/lifecycle.md`；本命令只是入口，**不另立一套流程**。

技能名：$ARGUMENTS
