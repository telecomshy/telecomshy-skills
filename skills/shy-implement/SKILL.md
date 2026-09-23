---
name: shy-implement
description: implement 的流程副本（收尾审查带成本闸门）：当用户要「/shy-implement」「shy 实施」，或要按 spec / 工单实施一段工作时使用。流程与 mattpocock implement 一致（tdd 驱动、常规类型检查与单测、末尾全量测试、提交），差异仅在收尾审查：默认走原生 /code-review 轻跑，用户明确要求多跑对拍才升级 shy-code-review。
disable-model-invocation: true
---

> 血统：全文副本自 `~/.agents/skills/implement/SKILL.md`（2026-09-23）。差异仅一处：收尾审查带**成本闸门**（见加粗行）——默认原生轻跑，明确要对拍才升级。上游更新时同步本副本。

Implement the work described by the user in the spec or tickets.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, review the work: **`/code-review`（原生轻跑，默认）**；仅当用户已明确要求多跑对拍时改走 **`shy-code-review`**（其委派子代理前有成本闸门，确认后才花 token）。

Commit your work to the current branch.
