---
id: REQ-0001
title: 一次性模型配置环节：插槽推荐制挑对拍矩阵，用户级矩阵跟人走
skill: shy-setup-models
status: done
kind: feature
iteration: 1
created: 2026-09-23
updated: 2026-09-23
blocked_by: []
related: [shy-code-review:REQ-0001]
---

# REQ-0001 一次性模型配置环节：插槽推荐制挑对拍矩阵，用户级矩阵跟人走

## 问题与目标

shy 系列的子代理模型 ID 此前只住**仓库级** `docs/agents/subagent-models.md`（跟仓库走）+ 本机 provider 配置（跟机器走）：换电脑 / 换项目就断。且模型目录动辄几百条（本机 457 条），翻列表交互不可用。目标：一次性配置环节 `shy-setup-models`——**插槽 + 推荐 + 确认制**（用户最多看 6 行、默认「按推荐」）、连通性探测、写**用户级**矩阵 `~/.config/opencode/shy-models.md`（跟人走）；四个 shy 技能的 ID 查找顺序升级为三级（仓库约定 → 用户级矩阵 → 问用户/降级）。

## 触发与分支

「/shy-setup-models」「shy 配置模型」「换机器配 shy 子代理模型」；或 shy-* 技能找不到模型约定时提示补跑。一次性环节（先例：setup-matt-pocock-skills），换机器/凭据重跑。

## 行为与步骤

1. 分片拉目录（按 provider 过滤，几百条不进上下文；`all: true` 补查非最新代）；逃生门：直接报 ID 跳过全程。
2. 机器筛：排除 TTS/语音克隆/Vision/嵌入/旧版本变体。
3. 插槽推荐：A=快便宜基线、B=不同家族互查、C=第三方视角（凑不齐三家注明「2 模型凑 3 跑」）；每槽 1 推荐 + 至多 1 备选（≤ 6 行）。
4. 确认制拍板 + 选型 why 落盘。
5. 一句话 ping 连通性探测；不通换备选再探；仍不通矩阵标注降级凑满。
6. 写 `~/.config/opencode/shy-models.md`（写盘工具、UTF-8 无 BOM）。
7. 四个 shy 技能 SKILL.md 的 ID 查找顺序改为：仓库 `docs/agents/subagent-models.md` → 用户级矩阵 → 问用户/同模型凑满并标注。

## 脚本与资源

- `~/.agents/skills/shy-setup-models/SKILL.md`（无 scripts/references）。
- 产物：`~/.config/opencode/shy-models.md`（槽位表 + why + 探测结果 + 日期）。

## 降级与边界

- 查无此模型：加 `all: true` 再查；仍无则如实说，不猜 ID。
- 只挑目录里已可用的模型；不改 `opencode.jsonc`（provider 与凭据归 OpenCode 管）。
- shy-* 现有兜底（问用户 / 同模型凑满并标注）不变。

## 验收标准

- [x] `shy-setup-models` SKILL.md 落盘：插槽推荐制（≤6 行确认）、逃生门、探测、矩阵格式、完成判据与边界 —— 本次交付事实（episode）
- [x] 四个 shy 技能的 ID 查找顺序均为三级（仓库约定 → 用户级矩阵 → 问用户）—— 判定：逐文件 grep 查找顺序句（语义）。**（已被 REQ-0002 取代）**
- [x] `validate_skill.py` 对 shy-setup-models 输出 `status: ok` —— 判定：跑该命令看输出（语义）
- [x] 真实跑一次 `/shy-setup-models`：产出用户级矩阵且三槽带 why、探测结果落盘 —— 判定：看一次真实运行的矩阵文件（行为）

## 范围外

- 管理 provider / 凭据 / 改 opencode.jsonc。
- 模型评测与推荐打分脚本化（目录规模吃紧、上下文被灌爆时再上 `scripts/`）。
- 自动同步仓库约定与用户级矩阵。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-23 | 骨架 + SKILL.md + 四技能查找顺序升级 + 本 REQ 落盘 | validate_skill `status: ok`；run_checks 绿 | （行为）项待首验（下次真实跑 /shy-setup-models 时勾销），status 留 in-progress |
| 2 | 2026-09-23 | 首次真实运行：三 ID 目录核实（均 active）+ 三槽探测全通 + 写用户级矩阵 `~/.config/opencode/shy-models.md`（A/B/C 各带 why 与降级备注） | 矩阵文件 + 三份探测回应 | 全部验收过，转 done |
| 3 | 2026-09-24 | 顺序变更为**用户级矩阵唯一来源**（REQ-0002）：删除仓库级 `docs/agents/subagent-models.md` 的优先地位；5 处技能表述同步 | 本轮 Gate 重跑绿；`grep -rn "subagent-models" skills/` 无输出 | 原「三级顺序」验收由 REQ-0002 取代；status 保持 done |

## 备注 / 待办

逼问：跳过（依据：用户确认方案并点出「大列表交互不可用」——插槽 + 推荐 + 确认制即其解法，逃生门与探测为既有经验固化）。
静态项未走 `check:` 注册（同前，注册表属 shy-skill-suite，范围外），以 `（语义）`+判定命令代替。
