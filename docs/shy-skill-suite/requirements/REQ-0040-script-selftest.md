---
id: REQ-0040
title: 给脚本加自测套件（冒烟/契约级，纯标准库）
skill: shy-skill-suite
status: done
kind: feature
iteration: 4
created: 2026-09-17
updated: 2026-09-18
blocked_by: []
related: [REQ-0002, REQ-0012, REQ-0027, REQ-0033, REQ-0040]
---

# REQ-0040 给脚本加自测套件（冒烟/契约级，纯标准库）

## 问题与目标

`scripts/` 有 9 个 CLI，但**没有任何测试**（`*test*`/`*spec*` 文件 = 0）。`reviewing-skills.md` Step 6 审的是"**接口好不好用**"（非交互 / `--help` / 结构化输出 / 幂等），**不审"代码对不对"**——脚本可以接口漂亮但结果错。

**真实证据**：2026-09-17 本会话亲手踩到多个脚本级问题——`run_checks.py` 自指误报（把自己也算进禁词扫描）、`.skill`/`args.skill` 被 grep 当打包命中、`$f:` 变量解析炸掉。

**为什么不照搬 mattpocock 的 `code-review`**：它是"审人写的 diff"（Standards 清单 + Spec），判定靠**语义**；Step 6 已是同类清单，重复。要补的是**可执行**——跑起来、退非 0、可复现。

目标：一个 `scripts/selftest.py`（纯标准库、无依赖），对每个脚本跑**冒烟 / 契约**用例（临时 fixture、断言退出码与关键输出），失败退非 0；并接进 `run_checks.py`，让 Spec 轴自动覆盖。

## 触发与分支

- 改任何 `scripts/*.py` 之后 / 发版前。
- 复审 `reviewing-skills.md` Step 6。
- 用户说"脚本测一下 / 跑自测"。

## 行为与步骤

1. **新增 `scripts/selftest.py`**：
   - 每个脚本 ≥1 条契约用例；覆盖**成功路径 + 至少一条失败路径**（退出码 / stderr）。
   - 全程在临时目录造 fixture，**不碰仓库、不弹浏览器、不装依赖**；`render_report` 一律 `--no-open`。
   - 输出每条 `PASS/FAIL` + 证据；`退出码 0 = 全过`，否则 1。
2. **`reviewing-skills.md` Step 6**：完成判据加"脚本有自测覆盖（`selftest.py`），或说明为何不需要"。
3. **`scripts/run_checks.py`**：注册 `skill-selftest`（跑 `selftest.py`，rc=0 即过）。
4. **`SKILL.md`** 资源清单标注 `selftest.py`。

## 脚本与资源

- 新增 `scripts/selftest.py`。
- 改 `references/reviewing-skills.md`（Step 6）、`scripts/run_checks.py`、`SKILL.md`。
- 不改各脚本本身的**行为**（本 REQ 只加测试；测试暴露的缺陷另开 REQ）。

## 降级与边界

- **冒烟 / 契约级，不是穷尽单测**：目标是"改了脚本能立刻知道有没有弄坏外壳"，不是 100% 行覆盖。
- 不引入 pytest 等第三方依赖（技能约束：纯标准库）。
- 需要真实 agent runner 的用例（`optimize_description --runner cmd` 真跑）**不进自测**——那是行为轴 eval，不是冒烟。
- 自测自身不参与禁词扫描（它是测试，必然会写出被测的字符串）。

## 验收标准

- [x] `selftest.py` 存在；对 9 个脚本每脚本 ≥1 条用例，且**每个脚本至少一条失败路径**断言（坏参数 / 坏输入 → 非 0 退出码） — `check:req0040-selftest-exists` ✅ 缺脚本用例=[]、含失败路径断言=True
- [x] `python scripts/selftest.py` → 退出码 **0**，全部用例 PASS（实测数量写入迭代记录） — `check:skill-selftest` ✅ 25 条用例：25 通过 / 0 失败、rc=0
- [x] `selftest.py` 纯标准库（无第三方 import）；`render_report` 用例带 `--no-open` — `check:req0040-selftest-pure` ✅
- [x] `reviewing-skills.md` Step 6 完成判据含"自测" — （episode） ✅
- [x] `python scripts/run_checks.py --list` 含 `skill-selftest` — `check:req0040-registered` ✅
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok` ✅

## 范围外

- 不做穷尽单测 / 覆盖率门禁。
- 不改脚本行为（发现 bug 另开 REQ）。
- 不做 CI 集成（本仓库无 CI 配置）。
- 不做真实 agent runner 的行为 eval（归 `running-evals.md`）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求（P1「脚本质量」收窄版：不搬 code-review，做可执行自测） | `*test*` 文件=0；本会话踩到 3 个脚本级问题 | 开工 |
| 2 | 2026-09-17 | 实施：新增 `scripts/selftest.py`（10 组用例 / 20 条断言，覆盖 9 个 CLI 的成功 + 失败路径；纯标准库；临时 fixture；`--no-open`）；`reviewing-skills.md` Step 6 完成判据加"自测"；`run_checks.py` 注册 `skill-selftest` 等 5 条；`SKILL.md` 资源清单同步 | `selftest.py` → **20 条用例：20 通过 / 0 失败**、rc=0；`run_checks` → 27 通过 / 0 失败；`validate` ok | **done** |
| 3 | 2026-09-18 | `iteration-4` 立即修：`agent_runner` 补成功路径用例（heuristic → rc0 + JSON）；docstring 删未实现的 `[--verbose]`；`--help` 补「示例」 | `selftest.py` → **21 条用例：21 通过 / 0 失败**、rc=0；`skill-selftest` PASS | done |
| 4 | 2026-09-18 | `iteration-8`–`12` 复审循环：补 4 条用例（零 REQ → n/a、空验收 → FAIL、缺 `{prompt}` → rc1、非活动 REQ 标签不计工作集）；`main` 补 `force_utf8_stdio` | `selftest.py` → **25 条用例：25 通过 / 0 失败**、rc=0（UTF-8 无乱码）；`skill-selftest` PASS | done |

## 备注 / 待办

- 来源：本会话横向比对的三家共同空白（脚本代码质量），以及 2026-09-17 的实际 bug。
- 与 `REQ-0033`（已退休）的关系：0033 是脚本行为硬化，本 REQ 是给脚本**加测试**——两者互补，不重叠。
- 待验证：若自测暴露脚本缺陷，是否值得修由证据定（可能另开 REQ）。
