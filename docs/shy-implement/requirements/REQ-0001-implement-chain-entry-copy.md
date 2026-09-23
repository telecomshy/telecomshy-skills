---
id: REQ-0001
title: 做一个 implement 流程副本，让实施链收尾真实调用 shy-code-review
skill: shy-implement
status: done
kind: feature
iteration: 1
created: 2026-09-23
updated: 2026-09-23
blocked_by: []
related: [shy-code-review:REQ-0001]
---

# REQ-0001 做一个 implement 流程副本，让实施链收尾真实调用 shy-code-review

## 问题与目标

mattpocock `implement` 正文写死「use /code-review」，实施链收尾永远走原版审查，`shy-code-review` 插不进链路（AGENTS.md 路由是软保证）。目标：以**全文副本**方式做一个 `shy-implement`，流程与上游逐字一致、仅收尾审查一步改指 `shy-code-review`——流程正文自带指针，硬保证。触发场景：「/shy-implement」「shy 实施」，或按 spec / 工单实施工作。

## 触发与分支

「/shy-implement」「shy 实施」「按工单实施」→ 执行本技能（= implement 流程）；收尾审查 → `shy-code-review`。链路/会话点名 `implement` 时经 AGENTS.md「Shy 技能路由」改走本技能。

## 行为与步骤

逐字沿用上游 `implement`（tdd 驱动、常规类型检查与单测、末尾全量测试、提交），唯一差异：收尾审查调 `shy-code-review`。血统注记置于正文首（来源路径 + 日期 + 差异位置 + 同步责任）。

## 脚本与资源

- 技能文件：`~/.agents/skills/shy-implement/SKILL.md`（全文副本 + 血统注记）。
- 外圈：`AGENTS.md`「Shy 技能路由」表含 `implement` → `shy-implement` 行。

## 降级与边界

- 上游 `implement` 更新时人工同步本副本（15 行量级，同步成本≈0）；血统注记标出差异位置。
- 链内 `tdd` 继续走原版（无对拍需求）。

## 验收标准

- [x] `SKILL.md` = 上游正文逐字副本 + 一行差异（收尾 → `shy-code-review`）+ 血统注记 —— 判定：与上游逐行对照（语义）
- [x] `validate_skill.py <技能目录>` 输出 `status: ok` —— 判定：跑该命令看输出（语义）
- [x] 上游 `~/.agents/skills/implement/` 未被写入 —— 本次交付事实（episode）
- [x] AGENTS.md 路由表含 `implement` → `shy-implement` 行 —— 判定：读该文件（语义）
- [x] 真实跑一次 `shy-implement` 链：收尾审查实际调用 `shy-code-review` —— 判定：看一次真实运行的调用记录（行为）

## 范围外

- 修改 `implement` 原文；改 `tdd` 流程。
- 覆写 `~/.config/opencode/commands/implement.md` 指针（可选项，另行决定）。
- 自动同步上游（人工同步即可，量级小）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-23 | 骨架 + 副本 SKILL.md + 本 REQ 落盘；路由表补 implement 行 | validate_skill `status: ok`；run_checks 绿 | （行为）项待首验，status 留 in-progress |
| 2 | 2026-09-23 | 首次真实运行：shy-implement 实施 #47/#48/#53/#49/#51 五票（每票一提交），收尾真实调用 shy-code-review | 本会话 git log + 两轴审查报告 | （行为）项已验收，转 done |

## 备注 / 待办

逼问：跳过（依据：用户提出「复制 implement 改指针」方案并确认最小改动方向；血统注记与同步责任为工程补充细节）。
静态项未走 `check:` 注册（注册表属 `shy-skill-suite`，范围外），以 `（语义）`+判定命令代替。
