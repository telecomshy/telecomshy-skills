---
name: shy-skill-suite
description: Skill development suite: operating conventions for the full development lifecycle of a "skill" artifact. Use when you are grilling / clarifying what a skill should do, creating or modifying a skill, writing a requirements document for a skill (REQ-NNNN naming / structure / acceptance criteria), reviewing a skill (trigger reliability, behavioral effectiveness, structure budget, scripts and safety), writing or editing a skill's SKILL.md, validating skill structure, or driving a skill's development iteration loop and writing results back to requirements. Not applicable to content-processing tasks that do not change a skill's behavior, such as translation, language switching, or format conversion.
compatibility: Requires Python >= 3.7 (standard library only; tested on 3.12). scripts/ is used only for validation, evaluation, requirement tracking, and report generation; if the Python version is too low, skip the scripts and follow the specs in references/ manually.
metadata:
  name_cn: 技能开发套件
  description_cn: 技能全流程操作规范：写技能需求文档，以及生成/改写后复审技能、提出改进并迭代。
  create_source: super-agent-skill-creator
---

# Skill Development Suite

Covers a skill's **development lifecycle**: grill → write requirements → **implement** (silent gate → write back → stop); **review** is triggered by the user on demand (report → item-by-item triage → single-pass implementation → stop). Each branch routes to its spec file according to user intent.

## Branch routing

| User intent | Go to |
| --- | --- |
| The full loop of developing / iterating a skill | [`references/lifecycle.md`](references/lifecycle.md) |
| Grilling requirements / interrogating what a skill should do (including retroactively inferring intent for an existing skill) | [`references/grilling.md`](references/grilling.md) |
| How to write a skill / how to write `SKILL.md` / getting a skill right | [`references/writing-skills.md`](references/writing-skills.md) |
| Writing / editing only a requirements document; "write requirements", "requirements doc", "what should this change do" | [`references/writing-requirements.md`](references/writing-requirements.md) |
| Review only; "evaluate this skill", "check the skill", "are the triggers accurate", "suggest improvements" | [`references/reviewing-skills.md`](references/reviewing-skills.md) |
| Running evals to gather evidence (trigger rate, with/without-skill comparison) | [`references/running-evals.md`](references/running-evals.md) |

## Shared principles (all branches follow these)

- **Single source of truth**: see the definition in `references/writing-skills.md` §7.
- **A skill must be self-contained**: definition and checks in `references/reviewing-skills.md` Step 7.
- **Delete before adding**: see `references/reviewing-skills.md` §1.
- **Evidence first**: any judgment without a real execution trace or comparative evidence can only be marked "to be verified", never treated as a conclusion.
- **Output for humans**: the report's three fields (problem / plain-language explanation / suggested change) and the plain-language writing rules are in `references/reviewing-skills.md` Step 8; terminology follows `references/glossary.md`.
- **Implementation and review are two separate paths**: after implementing, run only the **silent, sub-second gate** (report done when it is green; speak up only when it is red), and **do not review automatically**; **review is triggered by the user**, and after producing a report you **triage item by item** (fix now / fix later / discard), implement once according to the selection, then stop, with **no automatic re-review**. See `references/lifecycle.md` for details.

## Resources

Only the ones not covered by the routing table are listed here (the rest are above):

- `references/glossary.md` — the suite's own vocabulary (term / one-line plain-language explanation / `_avoid_`); the standard for wording in explanations and reports.
- `references/subagents.md` — roles and narrow briefs for sub-agents dispatched during review (executor / grader / spec-reviewer / analyzer / comparator), and dispatch vs. inline.
- `scripts/` — pure-standard-library CLIs; for interfaces see each script's `--help`, for the eval script list see `references/running-evals.md`; the Gate uses `validate_skill.py` + `run_checks.py` + `selftest.py`.
- `assets/report-template.html` — HTML report template (inline styles, no external resources). **Static read-only by default**; triage controls appear only under `--serve` (a temporary local server), and "submit to agent" at the end writes `triage.json`.
- `commands/` — opencode slash-command templates (`shy-grill` / `shy-review` / `shy-apply` / `shy-next`); copy them to `~/.config/opencode/commands/` to take effect, see "Slash shortcuts" in `references/lifecycle.md` for details.
- `evals/evals.json` — the starter trigger-eval set shipped with the skill (for reproducing trigger conclusions; see `references/running-evals.md`).
- `evals/effectiveness.json` — the behavior-axis comparison case set shipped with the skill (with_skill vs baseline, task-style prompts + assertions; see `references/running-evals.md`).

## Out of scope

Does not handle the domain implementation of the skill being developed; it only handles the conventions for the full skill-development lifecycle: grilling, requirements, implementation, review, evaluation, and iteration.
