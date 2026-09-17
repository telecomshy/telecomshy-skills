---
id: REQ-0032
title: 技能文档去重与判据补齐（第二批）
skill: shy-skill-suite
status: ready
iteration: 1
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0028, REQ-0029, REQ-0030, REQ-0031]
---

# REQ-0032 技能文档去重与判据补齐（第二批）

## 问题与目标

2026-09-17 第二轮复审在**标准轴 · Step 4（结构/预算）与 Step 5（步骤/完成判据）**发现的 8 处问题。全部已证伪确认。

**其中 5 处是 `REQ-0029`/`REQ-0030` 那轮**新引入**的**——加规则时顺手把同一句写了几处，或留了指向不存在内容的指针。这正是套件自己说的「改一处忘另一处即漂移」。

目标：判据可判定、同一含义只写一处、引用基准唯一。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 4 / Step 5 收工后，用户确认落盘。
- 用户说"把新加的东西再清一遍"。

## 行为与步骤

只改技能文件（`SKILL.md` / `references/`），**不改 REQ 文档**（见 `REQ-0031`）。

1. **「优先删，其次改，最后才加」两处逐字重复（P2）**：`SKILL.md:30` 与 `reviewing-skills.md:21` 完全相同。规范句留 `reviewing-skills.md` §1（它的语境），`SKILL.md` 共用原则改为指针「先删后加：见 `references/reviewing-skills.md` §1」。
2. **报告守卫规则写了 4 处（P2）**：`subagents.md:65`、`running-evals.md:80`、`reviewing-skills.md:155`、`render_report.py:343`（`--help` 文案），措辞已分叉。权威句留 `reviewing-skills.md` Step 8；其余三处只留「见 Step 8」的指针。
3. **`superseded_by` 的理由两处近乎逐字重复（P2）**：`lifecycle.md:75` 与 `writing-requirements.md:51`。理由留 `writing-requirements.md` §3，`lifecycle.md` 改为「加 `superseded_by: REQ-NNNN`（定义与理由见 `writing-requirements.md` §3）」。
4. **`reviewing-skills.md:60` 否定句（P2）**：删「不要只取本次 REQ 的：」，保留前面的正面并集句（§6）。
5. **`SKILL.md:40` 漏 `references/` 前缀（P2）**：「说明见 `lifecycle.md`」→「说明见 `references/lifecycle.md`」（`writing-skills.md` §3 刚明确该前缀只在 `references/` 内部可省）。
6. **`subagents.md:69` 悬空类别指针（P2）**：该行说「违反的轨迹按『复审自身反模式』记」，但 `reviewing-skills.md` §4 的 3 条反模式里没有副作用条。在 §4 增一条「子 agent 触发用户可见副作用」，或把该句改为指向 `subagents.md` 本节的禁令。
7. **`reviewing-skills.md:95` 判据未覆盖「降级」（P2）**：Step 3 完成判据只列「唯一豁免」，未覆盖 `:79` 定义的降级路径 → 括注补「或已降级（`no spec available`，须注明）」。
8. **`lifecycle.md:77` 判据括注漏 `superseded_by`（P2）**：括注改为「（REQ 仍可解析、`blocked_by` / `superseded_by` 无悬空）」——脚本两者都查。

## 脚本与资源

- 改 `SKILL.md`、`references/reviewing-skills.md`、`references/lifecycle.md`、`references/subagents.md`、`references/running-evals.md`、`references/writing-requirements.md`。
- 若第 2 条要动 `render_report.py` 的 `--help` 文案，一并改 `scripts/render_report.py`。
- 不新增文件。

## 降级与边界

- **只做减法与搬迁**，不新增规则。第 1/2/3 条是删重复、留指针。
- 第 4 条只删否定半句，不改正面句。
- 第 5 条只改前缀，不改目标文件。
- 第 6 条二选一（增 §4 条目 或 改指向），不两套并存。
- 安全 / 规则类否定句（"不得出现密钥"）**保留**。

## 验收标准

- [ ] `grep -rn "优先删，其次改，最后才加" skills/shy-skill-suite` → 只命中 1 处（`reviewing-skills.md` §1）。
- [ ] `grep -rn "终局产物\|只在 Step 8" skills/shy-skill-suite` → 1 处权威句（`reviewing-skills.md` Step 8）+ 指针，不再是 4 处完整规则。
- [ ] `grep -rn "假 .done." skills/shy-skill-suite` → `superseded_by` 的理由只命中 1 处（`writing-requirements.md` §3）。
- [ ] `reviewing-skills.md:60` 段内不含「不要只取本次 REQ 的」。
- [ ] `grep -n "\`lifecycle\.md\`" SKILL.md` → 0 命中（应为 `references/lifecycle.md`）。
- [ ] `subagents.md` 的「按『复审自身反模式』记」有对应条目：`reviewing-skills.md` §4 含副作用条，或该句已改为指向 `subagents.md` 本节。
- [ ] `reviewing-skills.md` Step 3 完成判据括注含 `no spec available`（降级路径）。
- [ ] `lifecycle.md:77` 判据括注含 `superseded_by`。
- [ ] `python skills/shy-skill-suite/scripts/validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。
- [ ] 改动后 `SKILL.md` 行数不增（只做减法或持平）。

## 范围外

- 不改 REQ 文档（见 `REQ-0031`）。
- 不改脚本行为（`render_report.py` 只动 `--help` 文案）。
- 不新增 lever、不改 `writing-skills.md` §1–§10 的 lever 集合。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求（2026-09-17 第二轮复审标准轴 Step 4/5 的 8 条 findings） | — | 待开工 |

## 备注 / 待办

- 来源：2026-09-17 第二轮复审 findings（标准轴 P2 ×8）。报告：`skills/shy-skill-suite-workspace/iteration-2/report.html`。
- **8 条里 5 条是 `REQ-0029`/`REQ-0030` 新引入的**（第 1/2/3/6/8 条）——上一轮 REQ-0028 才刚做过去重，这轮加规则又造出新的。这是套件自身反复出现的模式，值得在下一轮复盘（`lifecycle.md` 阶段 6）时留意。
- 与 `REQ-0028` 同类；REQ-0028 修的是首轮，本 REQ 修的是大改引入的。
