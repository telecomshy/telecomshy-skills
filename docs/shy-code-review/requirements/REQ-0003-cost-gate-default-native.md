---
id: REQ-0003
title: shy 系列成本闸门：默认原生轻跑，明确要求才多跑（token 消耗必经确认）
skill: shy-code-review
status: in-progress
kind: feature
iteration: 1
created: 2026-09-23
updated: 2026-09-23
blocked_by: []
related: [REQ-0001, REQ-0002]
---

# REQ-0003 shy 系列成本闸门：默认原生轻跑，明确要求才多跑（token 消耗必经确认）

## 问题与目标

shy-* 的增强环节按子代理数量烧 token（shy-code-review 完整对拍 = 6 个子代理），此前**默认全开**；尤其仓库路由会把链路里的 `code-review` 静默升级成三跑对拍——用户没点单就花钱。目标（用户原则）：**默认走原生轻跑；委派任何子代理前报规模并确认；用户本轮明确要求过多跑则视为已确认不再拦**。

## 触发与分支

shy-code-review / shy-to-spec / shy-to-tickets / shy-improve-codebase-architecture 全部运行入口 + shy-implement / shy-implement-spec 的收尾审查 + 仓库路由（tasknotes-aireporter `AGENTS.md`「Shy 技能路由」）。

## 行为与步骤

1. 四个封装技能各加「成本闸门（第 0 步）」：委派子代理前报规模（对拍 2 轴 × 3 跑 = 6 个；盲评 3 个；三探索 3 个）并确认；默认选项 = **原生轻跑**（按上游原样）；快速模式（2 跑）作中间档；用户本轮已明确要多跑 → 视为已确认、报一句即走。
2. shy-implement / shy-implement-spec 收尾审查改为条件升级：默认 `/code-review` 原生轻跑，用户明确要对拍才走 `shy-code-review`（其闸门再确认一次）。
3. 仓库路由反转：默认原版，明确要求增强才映射 shy- 版。
4. README（telecomshy-skills）前置依赖块补「成本闸门」说明。

## 脚本与资源

- `~/.agents/skills/shy-*/SKILL.md` 与 `telecomshy-skills/skills/shy-*/SKILL.md`（双份同步）。
- `tasknotes-aireporter/AGENTS.md`「Shy 技能路由」节；`telecomshy-skills/README.md`。

## 降级与边界

- 闸门只问一次（每轮一次）；用户明确要过就不再拦，避免烦扰。
- 闸门默认项永远是便宜档；升级是显式选择。

## 验收标准

- [x] 四个封装技能含「成本闸门（第 0 步）」节：报规模、默认原生轻跑、明确要求视为已确认 —— 本次交付事实（episode）
- [x] 两个副本收尾审查为条件升级（默认原生 /code-review），血统注记同步 —— 判定：读文件（语义）
- [x] 仓库路由处置完毕：整节已删（发现性由各 shy-* 的 `description` 承担，成本闸门管住花钱）；**可证伪赌注**：若实测「链路内点名要对拍却不升级」断桥，回填一行映射即可 —— 判定：读 AGENTS.md 已无「Shy 技能路由」节（语义）
- [x] README 前置依赖块含成本闸门说明 —— 判定：读 README（语义）
- [ ] 真实触发一次闸门：未明确要求多跑时拦下并默认原生；明确要求时放行 —— 判定：看一次真实运行记录（行为）

## 范围外

- 改上游 mattpocock 技能。
- 按 token 计价/预算硬限（只做确认，不做计量）。
- 其它非 shy 技能的子代理委派（research 等另行考虑）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-23 | 四技能 + 两副本 + 路由反转 + README 落地成本闸门 | validate_skill ok；run_checks 绿 | （行为）项待首次真实触发，status 留 in-progress |
| 2 | 2026-09-23 | 仓库「Shy 技能路由」整节删除——默认原生后路由近 no-op，发现性归 skill description，省常驻 token | AGENTS.md 已无该节；REQ 验收项 3 订正 | 断桥赌注若输（链内点名升级不生效）回填一行 |

## 备注 / 待办

逼问：跳过（依据：用户给出明确原则「默认原生、明确说明才多跑、委派前询问」，方案即其直接实现；闸门措辞与两档默认为工程细节）。
静态项未走 `check:` 注册（同前）。
