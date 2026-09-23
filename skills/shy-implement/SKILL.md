---
name: shy-implement
description: implement 的流程副本（收尾审查走 shy-code-review）：当用户要「/shy-implement」「shy 实施」，或要按 spec / 工单实施一段工作时使用。流程与 mattpocock implement 一致（tdd 驱动、常规类型检查与单测、末尾全量测试、提交），唯一差异：收尾的代码审查改调 shy-code-review（三跑对拍 + 主代理裁决）。
disable-model-invocation: true
---

> 血统：全文副本自 `~/.agents/skills/implement/SKILL.md`（2026-09-23）。唯一差异：收尾审查由 `/code-review` 改为 `shy-code-review`（见下方加粗处）。上游更新时同步本副本。

Implement the work described by the user in the spec or tickets.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use **`shy-code-review`** to review the work.

Commit your work to the current branch.
