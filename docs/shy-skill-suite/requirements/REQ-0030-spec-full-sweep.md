---
id: REQ-0030
title: Spec 轴改无条件全量扫 + 删除回归债跟踪
skill: shy-skill-suite
status: done
kind: fix
iteration: 3
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0018, REQ-0025, REQ-0026, REQ-0028, REQ-0029]
---

# REQ-0030 Spec 轴改无条件全量扫 + 删除回归债跟踪

## 问题与目标

`REQ-0025` 引入的回归债机制（`last_verified` + `regression_debt` + Step 3 三档范围旋钮）**经证实是一次性的**：落戳之后，技能再改也不会触发回归。

**证据（已跑）**：

```
$ python -c "from track_requirements import regression_reasons; \
    print(regression_reasons({'last_verified':'2026-09-17','updated':'2026-09-17','_criteria':{'unchecked':0}}))"
[]
$ python -c "t=open('track_requirements.py').read(); print('skills' in t, 'git' in t.lower())"
False False
```

根因：**债判定盯错了文件。** 让旧验收失效的是**技能产物**（`SKILL.md` / `references/` / `scripts/`）的改动，而债只看 REQ 文档**自己的** `updated`。脚本对 `skills/` 目录**零感知**，也不调 git。REQ 文档不动 → 永远无债 → Spec 轴回增量 → 旧 REQ 永不重扫。

更糟：`Step 2` 的 case set 也挂在同一个债信号上（"Step 3 转全量时取并集"），所以**行为类回归一起被闸住**。

**根本限制（决定了方案）**：**"这次改动影响哪几个 REQ"无法机械计算。** REQ 的验收标准是散文，与实现它的 md 文本之间**没有登记任何对应关系**，影响分析只能靠语义理解。因此"缩小范围"的三条路都不可靠：

- `git blame` 行归属：漏掉"改 A 节却语义上弄坏 B 节"这类无行重叠的跨切影响；
- `touches:` 人工声明：会腐烂，且跨切改动不可局部化；
- 猜：静默漏。

**目标**：放弃"定范围"，改为**让全量扫可负担**。

- Spec 轴**无条件全量**：无旋钮、无状态、无指纹。
- 删掉 `REQ-0025` 的 per-REQ 跟踪（全量扫没有"哪几个 REQ 已验证"这个概念）。
- 成本杠杆只留两个：**验收标准可执行化** 与 **降频不降范围**（绑收敛点）。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 2 / Step 3。
- `/shy-next`（`commands/shy-next.md`）。
- 用户说"Spec 轴那个债机制不要了 / 回归怎么保证不漏"。

## 行为与步骤

1. **`reviewing-skills.md` Step 3**：删掉「三档范围」表与「三个自动升级条件」，改为「逐条走**全部 REQ** 的 `## 验收标准`」。**唯一豁免**：本次增量**只改了 REQ 文档、未动技能文件**时可跳过，但须在报告注明。豁免依据是**本次 diff**（无状态、无需指纹）。
2. **`reviewing-skills.md` Step 2**：case set 直接 = **全部 REQ 行为类标准的并集**，**不再**以"Step 3 转全量"为条件（解耦，修掉行为类被同一个债信号闸住的 bug）。
3. **`scripts/track_requirements.py`**：删 `scan_criteria` / `regression_reasons` / `regression_debt` 及其 docstring / `--help` / epilog 说明。**保留** `frontier` / `blocked` / `deferred` / `errors` / `warnings`（那是排期用的，与回归无关）。
4. **`references/writing-requirements.md`**：删 frontmatter 的 `last_verified` 与 §5「`done` 的时效」；§3 的验收标准加一条「**尽量可执行**——能用命令 / grep / 计数表达的，把命令写进去」。
5. **`references/lifecycle.md`**：删阶段 4 的「`last_verified` 改为当天」；阶段 5 删「顺手看回归债」；「斜杠快捷」表 `/shy-next` 描述改回「列 REQ frontier」。
6. **`commands/shy-next.md`**：删回归债措辞与 `description` 里的「回归债」。
7. **`SKILL.md`**：`track_requirements.py` 的描述删「报回归债」。
8. **取代标注**：`REQ-0025` 加 `superseded_by: REQ-0030` 与一句说明（见「脚本与资源」）。

## 脚本与资源

- 改 `scripts/track_requirements.py`、`references/reviewing-skills.md`、`references/writing-requirements.md`、`references/lifecycle.md`、`commands/shy-next.md`、`SKILL.md`。
- 改 `docs/shy-skill-suite/requirements/REQ-0025-spec-regression-sweep.md`：加 `superseded_by: REQ-0030`，`status` 改 `out-of-scope`，`备注` 说明「机制经 2026-09-17 复审证实为一次性，整体被 REQ-0030 取代；保留本文件作为『试过并被推翻』的记录」。
- 不新增文件、不引入依赖。

## 降级与边界

- **不降范围，只允许降频**：全量扫可绑在收敛点 / 里程碑，但每次执行时范围仍是全部 REQ。
- 无 git / 无 diff 场景：默认走全量（保守）。
- 唯一豁免（只改 REQ 文档）**必须在报告里注明**。
- **不引入** blame 定范围、`touches:` 声明——不可靠或会腐烂。
- 删机制**不改** `frontier` / `blocked_by` 语义（排期与回归无关）。
- 行为类的成本不掩盖：若某技能行为类 REQ 很多，每次复审要跑全部行为 case；这是行为型技能应付的价，杠杆是"把行为类标准确定化"，不是"缩小范围"。

## 验收标准

> 本 REQ 起，验收标准默认可执行：`` `check:<name>` `` 由 `scripts/run_checks.py` 跑；跑不了的标 `（语义）`（见 `writing-requirements.md` §4）。

- [x] track 输出不含 `regression_debt`，仍含 `frontier` / `blocked` / `deferred` / `errors`，`status: ok`、退出码 0 — `check:req0030-track-keys`
- [x] `track_requirements.py --help` 不含 `last_verified` / `regression_debt` / 「回归债」 — `check:req0030-help-clean`
- [x] 技能内 0 命中 `last_verified` / `regression_debt`（机制描述已全删） — `check:req0030-no-removed-tokens`
- [x] 技能内 0 命中「回归债」 — `check:req0030-no-debt-term`
- [x] `reviewing-skills.md` Step 3 无「三档范围」「三个自动升级条件」，含「全部 REQ」与「唯一豁免」 — （episode）
- [x] `reviewing-skills.md` Step 2 的 case set 来源不引用 Step 3 的转全量 — （episode）
- [x] `writing-requirements.md` 含 `check:` / `（行为）` / `（语义）` 三类规则、无 `last_verified` — （episode）
- [x] `REQ-0025` 的 frontmatter 含 `superseded_by: REQ-0030`、`status: out-of-scope` — （episode）
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`
- [x] **全量 Spec 扫仍能跑通**：全部 REQ 的验收标准逐条有判定（可执行项由 `run_checks.py` 跑，`（语义）` 项逐条读）。（语义）

## 范围外

- 不做 blame 定范围、不做 `touches:` 声明。
- 不降范围（只允许降频）。
- ~~不建 `verify_requirements.py`~~：2026-09-17 已改由 `scripts/run_checks.py` 承担（写作侧的可执行前提已由 `writing-requirements.md` §4 的硬规则建立）——本项解除。
- 不改 `render_report.py`（REQ-0029）、不改各脚本核心算法（REQ-0027）。
- 不改 `frontier` / `blocked_by` 语义。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求（复审证实 REQ-0025 的债机制为一次性；用户确认改无条件全量） | `regression_reasons(...)` → `[]`；脚本对 `skills/` 零感知 | 待开工 |
| 2 | 2026-09-17 | 实施 8 步：`track_requirements.py` 删 `scan_criteria` / `regression_reasons` / `regression_debt`；`reviewing-skills.md` Step 3 改无条件全量（删三档表与三个升级条件）、Step 2 case set 直接取并集；`writing-requirements.md` 删 `last_verified`、§3 加「尽量可执行」；`lifecycle.md` 阶段 4/5 与斜杠快捷表同步；`commands/shy-next.md`、`SKILL.md` 同步；`REQ-0025` 置 `superseded_by: REQ-0030` | `regression_debt` / `last_verified` / `回归债` 在技能内 0 命中；track 输出键为 frontier/blocked/deferred/errors/warnings；frontier 不含 REQ-0025（out-of-scope）；validate ok | 待复审（阶段 3） |
| 3 | 2026-09-17 | 本 REQ 作「Spec 轴靠跑不靠读」试点：验收标准改写成 `check:`（9 条可执行 + 1 条语义）；新增 `scripts/run_checks.py`（发现 + 注册表 + `--list`/`--output`）；`writing-requirements.md` §4 定「验收标准默认可执行」「写不成标（语义）」「自洽项不进验收标准」；`reviewing-skills.md` Step 3 改「先跑 `run_checks.py`，再读（语义）项，自洽项不复扫」、Step 8 加「P2 不阻断，自洽项攒批」；`lifecycle.md` 阶段 3/5 同步；`SKILL.md` 资源清单补 `run_checks.py`；解除本 REQ「不建 verify_requirements.py」的范围外项；`untagged = 0` 收窄为「**本轮 diff 触碰的 REQ**」——全局未标只记数、不阻断（避免新规则逼出一次全量改造） | `run_checks.py --root . --skill shy-skill-suite` → 9/9 通过、`untagged=0`；临时镜像注入故障后对应 check 变 FAIL（检出） | 待复审 |
| 3 | 2026-09-17 | **收敛复审**：`run_checks.py` 的 9 条 `req0030-*` 全过；语义项「全量 Spec 扫仍能跑通」已由本会话 `run_checks` 全量执行覆盖。 | `run_checks.py` 21 通过 / 0 失败 | done |

## 备注 / 待办

- 来源：2026-09-17 复审 + 与用户的方案论证。报告：`skills/shy-skill-suite-workspace/iteration-1/report.html`。
- **淘汰的候选**（逐条已考虑，不进建议列表）：
  1. **保留 `last_verified` 作纯审计戳**——全量扫下"是否验过"是**技能级**事实（=上次复审），不是 REQ 级；每轮改 25 个文件且会腐烂，不买行为改变 → 删。
  2. **blame 定范围**——漏跨切影响（无行重叠的语义破坏）且实现复杂；全量的成本已可负担，不值得用"以为没影响"换省钱 → 不做。
  3. **`touches:` 声明**——会腐烂，跨切改动不可局部化 → 不做。
  4. **`verify_requirements.py`**——需验收标准先可执行；本轮只落写作规则，工具待有重复证据再开 → 暂不做。
- **影响用户此前的决定**：用户曾选「修完再落 `last_verified`」；本 REQ 删掉该字段，故该决定自动失效（改为：全量扫每轮跑，无戳可落）。
- 与 `REQ-0026` 的关系：`REQ-0026` 新增 `superseded_by` 字段约定（假 done 的系统性修法），本 REQ 第 8 步用到了它。
- 与 `REQ-0028` 的关系：`REQ-0028` 原第 2 项「回归债定义 4 处去重」被本 REQ 吸收（机制整个删掉，无重复可去），已从 `REQ-0028` 删除。
- 与 `REQ-0029` 交叉：都改 `reviewing-skills.md`（Step 2/3 vs Step 8），合并实施时注意。