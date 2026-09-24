---
description: 技能开发套件 · 单技能 REQ 报告（按类型和状态分组的可折叠 HTML）
---

调用 `skill` 工具加载 `shy-skill-suite` 技能，然后：

1. 从 `$ARGUMENTS` 取**必填技能名**（缺则停下，问用户要看哪个技能；不要默认全仓）。
2. 跑 `python "<SKILL_DIR>/scripts/track_requirements.py" --root . --view overview --skill <skill>` 拿一行计数摘要（`<skill>：新增功能 N / 修复缺陷 M / …`）。
3. 跑 `python "<SKILL_DIR>/scripts/render_reqs.py" --root . --skill <skill> --no-open` 生成**单文件自包含** `reports/<skill>-reqs.html`（按类型 → 状态分组、可折叠；默认自动打开，`--no-open` / `SHY_NO_OPEN=1` 关闭）。
4. 在对话里给一行计数摘要（如 `shy-skill-suite：新增功能 N / 修复缺陷 M / …`）并指出 HTML 路径。

可选按类型过滤：`--kind <kind>`（`feature` / `fix` / `refactor` / `docs` / `hygiene` / `unspecified`）。

技能名 / 过滤：$ARGUMENTS
