---
id: REQ-0048
title: run_checks.py 自包含（去掉写死的 REQ 文件名）
skill: shy-skill-suite
status: done
kind: fix
iteration: 2
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0030, REQ-0040, REQ-0042]
---

# REQ-0048 run_checks.py 自包含（去掉写死的 REQ 文件名）

## 问题与目标

`iteration-3` 复审（2026-09-18）标准轴 P2：`scripts/run_checks.py` 有两条检查把本仓库的**具体需求文件名**写死在代码里——

```
:177  root / "docs" / skill / "requirements" / "REQ-0025-spec-regression-sweep.md"
:440  root / "docs" / skill / "requirements" / "REQ-0026-req-doc-consistency.md"
```

技能会被单独复制到 `~/.agents/skills/` 部署，`docs/` 不随行。这两个写死路径在别处就是**悬空指针**（找不到文件，或误读同名文件），违反本仓库 `AGENTS.md`「技能必须自包含：技能文件只引用技能自身，不引用仓库级 `docs/`」。

目标：`scripts/` 里不再出现具体 REQ 文件名（slug）；按 id 查找、对 slug 改名免疫。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 7 自包含审查 / Step 6 脚本审查。
- 用户说"这脚本能不能单独拷走用"。

## 行为与步骤

1. `run_checks.py` 增加通用助手 `find_req(root, skill, rid)`：在 `docs/<skill>/requirements/` 下按 `<rid>-*.md` 匹配，**只认 id、不认 slug**。
2. `req0030-req0025-superseded`、`req0042-count-free` 改用 `find_req`；找不到时返回清晰失败（不抛异常）。
3. 去掉合成 fixture 文件名里的 slug（`REQ-9001-ready.md` → `REQ-9001.md`、`REQ-0001-a.md` → `REQ-0001.md`），否则新检查会命中测试代码自身。
4. 注册检查 `req0048-no-hardcoded-req-file`、`req0048-find-req-helper`。

## 脚本与资源

- 改 `scripts/run_checks.py`（助手 + 两条检查 + fixture 名）。
- 改 `scripts/selftest.py`（fixture 名）。
- 不新增文件、不引入依赖。

## 降级与边界

- 只改查找方式，**不改**检查语义（仍校验 `superseded_by: REQ-0030` / `status: out-of-scope` / 「不写死数量」）。
- 按 id 查找仍依赖目标仓库存在该 id 的 REQ；找不到时明确失败，不静默通过。
- 不引入目录级快照 / 缓存。

## 验收标准

- [x] `scripts/*.py` 内 0 命中 `REQ-\d{4}-[a-z]`（无硬编码 REQ 文件名） — `check:req0048-no-hardcoded-req-file`
- [x] `run_checks.py` 含通用助手 `find_req` — `check:req0048-find-req-helper`
- [x] `python skills/shy-skill-suite/scripts/validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不改检查的判定内容、不改 `--help`、不改退出码语义。
- 不移除为 out-of-scope REQ 注册的检查（它们在 REQ 复活时仍需可用）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 落盘（`iteration-3` 复审标准轴 P2，用户分拣「立即修」） | 实测 `run_checks.py:177,440` 命中硬编码 REQ 文件名 | 待实施 |
| 2 | 2026-09-18 | 实施：加 `find_req`；两条检查改用它；fixture 去 slug；注册 `req0048-*` 两条检查 | 见下方「备注 / 待办」的门禁输出 | **done** |

## 备注 / 待办

- 来源：`skills/shy-skill-suite-workspace/iteration-3/findings.json` 标准轴 P2。
- 门禁证据（2026-09-18）：`run_checks.py --root . --skill shy-skill-suite` 全过、`req0048-*` 通过；`selftest.py` 20/20；`validate_skill.py` → `status: ok`。
