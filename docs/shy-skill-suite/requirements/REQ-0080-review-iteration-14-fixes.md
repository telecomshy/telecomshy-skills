---
id: REQ-0080
title: iteration-14 复审整改批：13 条（多跑口径统一、Spec 范围、脚本判据、自包含、破坏性护栏等）
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-24
updated: 2026-09-24
blocked_by: []
related: [REQ-0079, REQ-0069, REQ-0066]
---

# REQ-0080 iteration-14 复审整改批：13 条

## 问题与目标

`/shy-skill-review` 对 `shy-skill-suite` 的第 14 轮复审（工作区 `skills/shy-skill-suite-workspace/iteration-14/`）产出 13 条 findings，用户分拣为**全部「立即修」**。本 REQ 承载这批整改的实施契约（来源：`findings.json`）。

目标：逐条修掉 13 条 finding，改动过 Gate，不引入新回归。

## 触发与分支

- 触发：复审报告提交分拣（`triage.json` 13 条全「立即修」）。
- 分支：`references/` 文档 + `scripts/`（`run_effectiveness.py`、`agent_runner.py`）+ `evals/effectiveness.json` + `SKILL.md`。

## 行为与步骤

1. **F1**（行为 P1）：统一「多跑」模型口径——`glossary.md` 与 `reviewing-skills.md` 一致：默认同一模型多跑，用户显式给多个模型时才逐跑轮换；并去掉 glossary 与闸门冲突的「默认 3 跑」。
2. **F2**（需求 P1）：`lifecycle.md` 的 Spec 轴范围与 `reviewing-skills.md` 统一为「`（语义）` + `（未定）` 逐条读」。
3. **F3**（标准 P1）：`reviewing-skills.md` Step 6 完成判据不再用套件自身 `selftest.py` 代替——改为核对被审技能自己的测试。
4. **F4**（标准 P1）：去掉对仓库级 `REQ-0069` 的悬空引用（`running-evals.md`、`run_effectiveness.py` docstring、`evals/effectiveness.json` note）。
5. **F5**（标准 P1）：`run_effectiveness.py` 的 `disable_skills` 加护栏：`--skills-dir` 无效时显式报错、报告被移出/缺失的技能、把 moved 清单落盘以便恢复、加 `--dry-run`。
6. **F6**（标准 P1）：定义 `<SKILL_DIR>`（与指被审技能的 `<skill_dir>` 区分）。
7. **F7**（行为 P2）：`SKILL.md` description 补「跑评测 / 触发率 / 有效性对照」等说法。
8. **F8**（行为 P2）：`SKILL.md` 写明与 `skill-creator` / `writing-for-agents` 的边界。
9. **F9**（需求 P2）：统一 P2 的分拣去向——P2 一律进 `cleanup.md` 台账、不走 findings 分拣、不开 REQ。
10. **F10**（需求 P2）：`agent_runner.py` 的 argparse `--help` 补「必须钉模型」提示（现只在 docstring）。
11. **F11**（标准 P2）：`lifecycle.md` 去掉对外部项目 `skill-forge` 的悬空指名。
12. **F12**（标准 P2）：`writing-skills.md` 单一事实源补 `SKILL.en.md` 的地位。
13. **F13**（标准 P2）：`SKILL.md` 斜杠快捷补 TeleAgent 下的降级（或不支持时改用自然语言点名）。

## 脚本与资源

- 改 `references/{glossary,lifecycle,reviewing-skills,running-evals,writing-skills}.md`、`SKILL.md`。
- 改 `scripts/run_effectiveness.py`（护栏）、`scripts/agent_runner.py`（`--help`）。
- 改 `evals/effectiveness.json`（去掉 REQ 引用）。
- 改 `scripts/run_checks.py`：新增 `req0080-*` 检查。

## 降级与边界

- 不改 findings 的判定口径；不新增功能，只整改。
- `disable_skills` 护栏保持既有 CLI 兼容（不加必填参数），`--dry-run` 为可选。

## 验收标准

- [x] 多跑口径两处一致（默认同一模型、多模型才轮换；跑数由闸门定） —— `check:req0080-multirun-consistent`
- [x] Spec 轴范围统一为 `（语义）+（未定）` —— `check:req0080-spec-range`
- [x] Step 6 判据不再用套件 selftest 代替 —— `check:req0080-step6-selftest`
- [x] 技能文件与 evals 内不再出现 `REQ-0069` —— `check:req0080-no-req0069`
- [x] `run_effectiveness.py` 含 `--dry-run`、落盘 moved 清单、无效 `--skills-dir` 报错 —— `check:req0080-disable-guard`
- [x] `<SKILL_DIR>` 在套件内有定义 —— `check:req0080-skilldir-defined`
- [x] `SKILL.md` description 含「评测」、并写明与 `skill-creator`/`writing-for-agents` 的边界 —— `check:req0080-desc-eval-boundary`
- [x] P2 分拣去向统一（进台账、不开 REQ） —— `check:req0080-p2-triage`
- [x] `agent_runner.py --help` 含「钉模型」提示 —— `check:req0080-pin-model-help`
- [x] `lifecycle.md` 不再指名 `skill-forge` —— `check:req0080-no-skillforge`
- [x] `writing-skills.md` 单一事实源含 `SKILL.en.md` —— `check:req0080-skill-en`
- [x] `SKILL.md` 斜杠快捷含 TeleAgent 降级 —— `check:req0080-teleagent-degrade`
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok` —— 判定：跑该命令看输出（语义）
- [x] `python "skills/shy-skill-suite/scripts/track_requirements.py" --root .` → `status: ok` —— 判定：跑该命令看输出（语义）

## 范围外

- 台账 open 项（`CL-0038`~`CL-0062` 里的重复/措辞类）不在本批；它们按台账路径结清。
- 不改评测/复审的判定口径。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-24 | 落盘 REQ（复审 iteration-14 的 13 条「立即修」） | — | 实现 |
| 2 | 2026-09-24 | 实现 13 条：F1 多跑口径统一；F2 Spec 范围含（未定）；F3 Step 6 改核被审技能测试；F4 去 REQ-0069 悬空引用；F5 `run_effectiveness` 加 `--dry-run`/落盘 moved/无效目录报错；F6 定义 `<SKILL_DIR>`；F7 description 补评测；F8 边界写明；F9 P2 分拣统一；F10 `agent_runner --help` 补钉模型提示；F11 去 skill-forge；F12 单一事实源补 SKILL.en.md；F13 TeleAgent 降级。新增 `req0080-*` 12 条 | `validate_skill` ok；`run_checks` **86/86**（含 `req0080-*`）；`selftest` 39/39；`track_requirements` ok | 全部验收过，转 done |

## 备注 / 待办

逼问：跳过（依据：来源是复审 findings + 用户已逐条分拣「立即修」，无决策缺口）。
来源：`skills/shy-skill-suite-workspace/iteration-14/{findings.json,triage.json}`。
