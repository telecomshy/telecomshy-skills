---
id: REQ-0004
title: 核心行为（回溯补写：沉淀对话为知识库笔记）
skill: knowledge-distill
status: in-progress
kind: feature
iteration: 1
created: 2026-09-19
updated: 2026-09-19
blocked_by: []
retroactive: true
related: [REQ-0001, REQ-0002, REQ-0003]
---

# REQ-0004 核心行为（回溯补写：沉淀对话为知识库笔记）

## 问题与目标

`knowledge-distill` 的核心行为在需求体系建立前就已开发，**没有 spec**。2026-09-19 复审时按 `grilling.md` **从用户意图回溯补写**（标 `retroactive: true`），产出「这技能**应该**改变什么行为」，作为 Spec 轴的基准。**不是**读技能反推。

一句话：**把与 AI 的对话沉淀为可检索、可关联、可长期复用的知识库笔记**——是「知识沉淀」而非「摘要工具」。

## 触发与分支

用户不点名技能、按需求说话时触发。六个分支：

| 用户意图 | 分支 |
| --- | --- |
| 把对话总结/保存成笔记、沉淀到知识库 | 保存流程（Step 0 起） |
| 修改保存位置或格式、重新配置目录 | 配置修改 |
| 查找、检索之前记过的笔记 | 检索已有笔记 |
| 检查笔记库 / 断线 / 索引对齐 / 整理 | 健康检查 |
| 把笔记回退到历史版本 / 撤销改写 | 回退笔记 |

**边界（Q2 决策）**：只在用户**明确要存进知识库/笔记**时触发；「把对话整理成 spec / 纪要 / 文章」归相邻技能（`to-spec` / `handoff` 等），不由本技能抢答。负向句**暂不写进 `description`**，等触发评测证据再定（见 `REQ-0003`）。

## 行为与步骤

1. **保存**：读取配置 → 主题切分（默认偏保守，多篇先给方案表一次确认；单篇新建归已有分类走快速通道）→ 按内容判「新建 / 合并」（多关键词 OR 检索 + `--full` 读候选）→ `check-name` 查重 → 撰写 → `write-note` 事务化写入 → 更新根目录索引。
2. **沉淀而非压缩**：只剔除与主题无关的寒暄，主题相关细节原样保留。
3. **绝不编造（红线）**：忠实对话实际信息；推断加 `(推断)`、无法核实加 `(待核实)`、易变事实加 `(as of YYYY-MM-DD)`；外部客观易失效事实**可联网核验并标注出处，但不整段摘录**（Q4 决策）。
4. **合并**：用户逐行选「追加」（不改既有内容）或「改写优化」（保留旧内容独有信息）；结论冲突不覆盖，先标注并登记疑问。
5. **关联**：Obsidian 只写单向双链、反链交原生；普通 Markdown 手工补反链（仅 `AI笔记` 内）；主动回链 Step 2 检索到的同主题旧笔记。
6. **索引**：根目录 `总目录.md`（导航）+ `收录疑问.md`（疑问），分类目录为纯笔记文件夹；先笔记后索引。
7. **检索**：确定性排序（标题命中优先 → 命中多 → 日期新），只读不写。
8. **回退**：`write-note` 覆盖前自动备份（滚动 10 份），可恢复到指定版本。
9. **健康检查**：八类确定性检查（链接结构五类 + 内容质量三类）+ 合并候选；只读，修改一律先经用户确认。
10. **有道后端（Q3 决策：核心范围）**：与 Obsidian / 普通 Markdown 同为一级后端；就绪失败（装不上 CLI / 无 Key）**明确报错并引导用户完成，不静默退回本地**（R2Q3 决策）。

## 脚本与资源

- `scripts/skill_tools.py`：`discover-vaults` / `youdao-check` / `load-config` / `save-config` / `list-structure` / `list-index` / `list-questions` / `check-name` / `search-notes` / `lint-notes` / `write-note` / `list-backups` / `restore-note` / `append-index-entry` / `append-index-question` / `migrate-index`。
- `references/`：`obsidian-best-practices.md` / `plain-markdown-best-practices.md` / `youdao-best-practices.md` / `design-boundaries.md`。

## 降级与边界

- 有道：无原生标签 / 双链 / 版本 API，lint 部分能力缺失并如实列 `not_checked`（见 `REQ-0002`）。
- 平台：定位 TeleAgent 单平台（跨平台适配**暂缓**，见下）。
- 脚本一律用绝对路径调用；有道用逻辑路径。

## 验收标准

- [x] 六个分支存在且各有明确触发说法。 — （语义）判定：`SKILL.md` 分支路由表 + 各分支章节齐全
- [x] 沉淀而非压缩、绝不编造、事实/推断/易变事实标注规则齐全。 — （语义）判定：`SKILL.md` Step 5 真实性一节
- [x] 主题切分默认保守、多篇先给方案表一次确认。 — （语义）
- [x] 写入前 `check-name` 查重；合并分「追加 / 改写优化」两种且冲突先标注。 — （语义）
- [x] 索引为根目录 `总目录.md` + `收录疑问.md`，分类纯笔记，先笔记后索引。 — （语义）
- [x] 检索确定性排序、只读；回退写前备份、可按版本恢复。 — （语义）
- [x] 健康检查八类确定性检查、只读、修改先确认。 — （语义）
- [x] 有道为一级后端；就绪失败明确报错、不静默退回。 — （语义）
- [x] 触发率：正例与负例均 ≥ 0.5（模型 ID 记录在案）。 — （行为）v2 train 12/12、test 8/8；模型 `hubeitelecom/deepseek-v4-flash`（见 `REQ-0003`）
- [x] with/baseline（保存分支）：有 delta 证据。 — （行为）with_skill 100% vs baseline 75%；差异 = baseline 未生成根索引 `总目录.md`（`eval-0`）
- [x] with/baseline（健康检查分支）：有 delta 证据。 — （行为）断言两臂均过，但技能报 5 项确定性检查、baseline 手动只报 3 项（`eval-1`）
- [ ] with/baseline（合并 / 冲突 / 检索 分支）：待补。 — （行为）本轮未覆盖
- [x] 范围外六项不实现：向量/语义检索、跨平台适配、网页/外部资料接入、MOC、自动 hooks/定时巡检、文风偏好写入长期记忆。 — （语义）判定：`references/design-boundaries.md`

## 范围外

- **不做**：向量 / 语义检索；网页 / 外部资料接入沉淀；MOC / 知识地图；自动 hooks / 定时巡检；文风偏好写入长期记忆。
- **暂缓**：跨平台适配（`deferred`：暂时不做，以后可能考虑；触发条件 = 需要部署到 TeleAgent 以外的平台时）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-19 | 回溯补写核心行为 REQ（逼问 3 轮）；跑触发率与 with/baseline 有效性对照 | 触发 v2 20/20；有效性 with_skill 1.0 vs baseline 0.875（1.14x）；模型 `hubeitelecom/deepseek-v4-flash`；产物 `knowledge-distill-workspace/iteration-1/benchmark.json` | in-progress：合并/冲突/检索 分支对照待补 |

## 备注 / 待办

- 来源：2026-09-19 复审，Spec 轴 Step 0（无 REQ → 回溯补写）。
- 逼问：已过 3 轮（Q1 职责边界 / Q2 相邻边界 / Q3 有道核心 / Q4 真实性 / Q5 验收证据 / Q6 范围外；R2 范围外澄清 / 负向边界 / 有道降级；R3 三项逐项）。依据：本轮对话记录。
