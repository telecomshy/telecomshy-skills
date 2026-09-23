---
id: REQ-0001
title: 做一个 implement-spec 流程副本，让规格实现链收尾真实调用 shy-code-review
skill: shy-implement-spec
status: in-progress
kind: feature
iteration: 1
created: 2026-09-23
updated: 2026-09-23
blocked_by: []
related: [shy-code-review:REQ-0001, shy-implement:REQ-0001]
---

# REQ-0001 做一个 implement-spec 流程副本，让规格实现链收尾真实调用 shy-code-review

## 问题与目标

mattpocock `implement-spec` 步骤 7 写死「run /code-review on the PR branch」，规格实现链收尾永远走原版审查。目标：同 `shy-implement` 方案——**全文副本**做 `shy-implement-spec`，仅步骤 7 改指 `shy-code-review`，硬保证收尾走三跑对拍。触发场景：「/shy-implement-spec」「shy 按规格实现」。

## 触发与分支

「/shy-implement-spec」「shy 按规格实现」→ 执行本技能（= implement-spec 流程）；步骤 7 审查 → `shy-code-review`。链路/会话点名 `implement-spec` 时经 AGENTS.md「Shy 技能路由」改走本技能。

## 行为与步骤

逐字沿用上游 `implement-spec`（task graph / frontier、exploration 子代理、implementer 并发、merger、收尾审查、PR 就绪、清理 worktree），唯一差异：步骤 7 审查调 `shy-code-review`（并照旧由单个 implementer 子代理修全部 findings）。血统注记置于正文首。

## 脚本与资源

- 技能文件：`~/.agents/skills/shy-implement-spec/SKILL.md`（全文副本 + 血统注记）。
- 外圈：`AGENTS.md`「Shy 技能路由」表含 `implement-spec` → `shy-implement-spec` 行。

## 降级与边界

- 上游更新时人工同步本副本；血统注记标出差异位置。
- 收尾修复仍照上游：单个 implementer 子代理一次修完全部 findings。

## 验收标准

- [x] `SKILL.md` = 上游正文逐字副本 + 一行差异（步骤 7 → `shy-code-review`）+ 血统注记 —— 判定：与上游逐行对照（语义）
- [x] `validate_skill.py <技能目录>` 输出 `status: ok` —— 判定：跑该命令看输出（语义）
- [x] 上游 `~/.agents/skills/implement-spec/` 未被写入 —— 本次交付事实（episode）
- [x] AGENTS.md 路由表含 `implement-spec` → `shy-implement-spec` 行 —— 判定：读该文件（语义）
- [ ] 真实跑一次 `shy-implement-spec` 链：步骤 7 实际调用 `shy-code-review` —— 判定：看一次真实运行的调用记录（行为）

## 范围外

- 修改 `implement-spec` 原文。
- 覆写 `~/.config/opencode/commands/implement-spec.md` 指针（可选项，另行决定）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-23 | 骨架 + 副本 SKILL.md + 本 REQ 落盘；路由表补 implement-spec 行 | validate_skill `status: ok`；run_checks 绿 | （行为）项待首验，status 留 in-progress |

## 备注 / 待办

逼问：跳过（依据：同 shy-implement——用户已确认「复制改指针」方案）。
静态项未走 `check:` 注册（注册表属 `shy-skill-suite`，范围外），以 `（语义）`+判定命令代替。
