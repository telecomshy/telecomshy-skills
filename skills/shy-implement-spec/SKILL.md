---
name: shy-implement-spec
description: implement-spec 的流程副本（收尾审查带成本闸门）：当用户要「/shy-implement-spec」「shy 按规格实现」，或要按一份规格实现功能时使用。流程与 mattpocock implement-spec 一致，差异仅在收尾审查：默认走原生 /code-review 轻跑，用户明确要求多跑对拍才升级 shy-code-review。
disable-model-invocation: true
---

> 血统：全文副本自 `~/.agents/skills/implement-spec/SKILL.md`（2026-09-23）。差异仅一处：步骤 7 的收尾审查带**成本闸门**——默认原生轻跑，明确要对拍才升级。上游更新时同步本副本。

You have been provided a spec. This spec should have tickets associated with it, describing how to implement the spec.

The goal is a PR which implements the entire spec on a single branch.

The tickets are not a list of steps. They are a **task graph** with blocking relationships between them. This means there is always a **frontier** of tickets which are ready to be grabbed.

Communication to and from subagents should be sparse. Communicate primarily through **context pointers**: to the spec, tickets, research notes, and previous commits. Don't duplicate information already available via pointers.

**Implementer subagents** should be run in the background where possible for **maximum concurrency**.

## Steps

1. Read the spec and tickets. Read enough to understand the task graph.

2. (optional) Use an **exploration subagent** to conduct any exploration required by the tickets - relevant codebase files or external documentation. Ensure the exploration subagent can save files - it should save its markdown notes in a directory outside the repo, accessible by all future subagents. This lets **implementer subagents** focus on implementation rather than exploration.

3. Create a branch, and a draft PR. The PR should be marked as 'closing' the spec issue and tickets.

4. Use **implementer subagents** to implement each ticket. Each implementer subagent should work in its own worktree, on its own branch.

5. Once an **implementer subagent** completes, merge its work to the PR branch with a **merger subagent**.

6. If this changes the **frontier** of available tickets, kick off more **implementer subagents** to work on the new tickets. This allows for maximum concurrency.

7. Once all tickets are complete, review the PR branch: **`/code-review`（原生轻跑，默认）**；仅当用户已明确要求多跑对拍时改走 **`shy-code-review`**（其委派子代理前有成本闸门，确认后才花 token）。Fix all issues raised by the review in a single **implementer subagent**.

8. Mark the PR as ready for review.

9. Clean up all **implementer subagent** worktrees.
