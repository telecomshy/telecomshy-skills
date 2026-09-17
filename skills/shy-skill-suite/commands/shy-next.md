---
description: 技能开发套件 · 列出需求 frontier 与回归债（track_requirements）
---

调用 `skill` 工具加载 `shy-skill-suite` 技能，然后运行 `scripts/track_requirements.py --root .`，列出当前能开始的 REQ（frontier）、被阻塞的、悬空 `blocked_by`，以及**回归债**（`regression_debt`：`done` 但需复核的 REQ 及原因）。

技能（可选）：$ARGUMENTS
