---
id: REQ-0077
title: 斜杠命令改名 shy-skill-<分支>，且必填参数缺失时直接询问用户
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-24
updated: 2026-09-24
blocked_by: []
related: [REQ-0020, REQ-0071, REQ-0074, REQ-0076]
---

# REQ-0077 斜杠命令改名 shy-skill-<分支>，且必填参数缺失时直接询问用户

## 问题与目标

现状：套件 5 个斜杠命令名为 `/shy-eval`、`/shy-grill`、`/shy-reqs`、`/shy-review`、`/shy-start`（文件 `commands/shy-<分支>.md`），与技能触发词（`/shy-code-review`、`/shy-to-spec`、`/shy-setup-models` …）共用 `shy-` 命名空间，来源难辨。

两个真实缺口：

1. **命名**：套件命令归属 `shy-skill-suite`，命令名却与各技能同名空间，用户易混。
2. **缺参数**：参数必填的命令未规定"用户没给就直接问用户"。实测：`/shy-eval` 未带技能名时，模板没有"问用户"这一步，代理可能自行默认目标。

目标：① 套件命令统一为 `/shy-skill-<分支>`；② 必填参数的命令在 `$ARGUMENTS` 缺失时**直接询问用户**。

## 触发与分支

- 用户输入 `/shy-skill-<分支>` 触发对应分支（旧名 `/shy-<分支>` 已删除，不再生效）。
- 命令模板维护（`commands/`）与斜杠快捷说明（`references/lifecycle.md`）。

## 行为与步骤

1. 5 个命令文件改名：`commands/shy-skill-{eval,grill,reqs,review,start}.md`；旧文件名不再存在。
2. 技能与文档内命令名引用统一为 `/shy-skill-<分支>`（`SKILL.md` / `SKILL.en.md` / `references/*`）。
3. 必填参数的命令（`eval` / `grill` / `review`）写明：`$ARGUMENTS` 未提供时**直接询问用户**，不默认。（`reqs` / `start` 已有同等说明。）
4. `run_checks.py` 的旧断言随之更新，并新增命名与"缺参数询问"两条检查。

## 脚本与资源

- `commands/shy-skill-{eval,grill,reqs,review,start}.md`（改名 + 补"缺则问用户"）。
- `references/lifecycle.md` 斜杠快捷表，`references/{glossary,reviewing-skills,running-evals,writing-requirements}.md`，`SKILL.md`、`SKILL.en.md`：命令名引用更新。
- `scripts/run_checks.py`：更新旧断言（`commands/shy-<分支>.md`、`/shy-<分支>` 字面量）+ 新增 `req0077-command-names` / `req0077-arg-ask`。
- `scripts/track_requirements.py`、`scripts/render_report.py` 内提到旧命令名的说明文字同步。
- `.gitignore` 注释内的 `/shy-reqs` 同步。

## 降级与边界

- 旧命令名 `/shy-<分支>` **一并删除**，不留别名；用户已部署的旧命令文件需替换为新文件。
- 不改命令的语义与分支路由，仅改名与补"缺则问用户"。
- 不涉及技能触发词（`/shy-code-review` 等保持原样）。

## 验收标准

- [x] `commands/` 下 5 个文件为 `shy-skill-{eval,grill,reqs,review,start}.md`，旧名 `shy-<分支>.md` 均不存在 —— `check:req0077-command-names`
- [x] `eval` / `grill` / `review` 三个命令正文含"直接询问用户" —— `check:req0077-arg-ask`
- [x] 技能与 references 内不再出现旧命令名：`grep -rn "shy-\(eval\|grill\|reqs\|review\|start\)\b" skills/shy-skill-suite` 无输出 —— 判定：跑该命令看输出（语义）
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok` —— 判定：跑该命令看输出（语义）
- [x] `python "skills/shy-skill-suite/scripts/track_requirements.py" --root .` → `status: ok` —— 判定：跑该命令看输出（语义）

## 范围外

- 保留旧命令名作为别名。
- 改动 shy 技能的触发词（`/shy-code-review` 等）。
- 重写历史 REQ 正文（`REQ-0020` 只标注取代，不改写）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-24 | 落盘 REQ | — | 实现 |
| 2 | 2026-09-24 | 实现：5 个命令 `git mv` 改名 shy-skill-<分支>；`SKILL.md`/`SKILL.en.md`/`references/*` 引用与 `run_checks.py` 断言同步；`eval`/`grill`/`review` 补"缺则直接询问用户"；新增 `req0077-command-names`/`req0077-arg-ask`；部署本机全局命令目录 | `validate_skill.py` → `status: ok`；`run_checks.py` 72/72（含 req0077 两条）；`selftest.py` 39/39；`track_requirements.py --root .` → `status: ok`；旧命令名 grep 无输出 | 全部验收过，转 done |

## 备注 / 待办

逼问：已过 1 轮（mini-grill：前缀形式 = `shy-skill-<分支>`；旧名 = 删除；询问范围 = 补缺的 `eval`/`grill`/`review` 三个）。
`REQ-0020` 的「`/shy-<分支>` 命名决策」由本 REQ 取代（部分取代，按 `writing-requirements.md §3` 标注受影响处 + 迭代记录，不用 `superseded_by`）。
