#!/usr/bin/env python3
"""跑需求文档（REQ）里**可执行**的验收标准。

复审的 Spec 轴默认**靠跑不靠读**：把全部 REQ 的 `## 验收标准` 里标了
`` `check:<name>` `` 的条目一次跑完，秒级出结果。只有标 `（语义）` 的条目
才需要逐条读、判通过 / 部分 / 未实现。

- 发现：扫描 `docs/<skill>/requirements/REQ-*.md` 的 `## 验收标准` 段。
- 可执行条目写法：`` - [ ] <描述> — `check:<name>` ``；条目其余部分是人读的描述。
- 语义条目写法：`` - [ ] <描述>（语义） ``——无法机械判定，交 Step 3 人/agent 判。
- 检查实现：本文件底部的注册表（按 REQ 追加）。名称用 kebab-case，前缀 REQ id 防撞。

用法:
    python run_checks.py [--root .] [--skill <name>] [--list] [--output <path>]

默认打有界摘要（每条 check 一行 + 计数）；`--list` 只列注册的检查名。

退出码:
    0  全部可执行条目通过
    1  有失败，或引用了未注册的 check
    2  参数错误
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from skill_utils import force_utf8_stdio, read_text

CRITERION_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s*(?P<desc>.+)$")
CHECK_TAG_RE = re.compile(r"`check:\s*(?P<name>[a-z0-9-]+)\s*`")
BEHAVIOR_RE = re.compile(r"（行为）|\(behavior\)")
SEMANTIC_RE = re.compile(r"（语义）|\(semantic\)")

CheckFn = Callable[[Path, str], "tuple[bool, str]"]
CHECKS: dict[str, CheckFn] = {}


def check(name: str) -> Callable[[CheckFn], CheckFn]:
    def deco(fn: CheckFn) -> CheckFn:
        CHECKS[name] = fn
        return fn

    return deco


# --------------------------------------------------------------------------- #
# 通用工具
# --------------------------------------------------------------------------- #

def run_script(root: Path, script: Path, *args: str) -> tuple[int, str, str]:
    """用当前解释器跑技能脚本（sys.executable，避免依赖 PATH 里的 python）。"""
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=root, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    return proc.returncode, proc.stdout, proc.stderr


def skill_files(
    root: Path, skill: str, exclude_names: tuple[str, ...] = ()
) -> list[Path]:
    """技能目录下的文本文件（排除 pyc / __pycache__ / 指定的文件名）。

    `exclude_names` 用于排除**检查器自身**——测试文件必然会写出被测的禁词。
    """
    base = root / "skills" / skill
    if not base.is_dir():
        return []
    return [
        p for p in base.rglob("*")
        if p.is_file() and p.suffix != ".pyc" and "__pycache__" not in p.parts
        and p.name not in exclude_names
    ]


def req_frontmatter(path: Path) -> dict[str, str]:
    text = read_text(path)
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)[1]
    out: dict[str, str] = {}
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return out


def skill_dir(root: Path, skill: str) -> Path:
    return root / "skills" / skill


# --------------------------------------------------------------------------- #
# 检查注册表（按 REQ 追加；实现只依赖 root + skill，不硬编码仓库路径）
# --------------------------------------------------------------------------- #

@check("req0030-track-keys")
def req0030_track_keys(root: Path, skill: str) -> tuple[bool, str]:
    rc, out, err = run_script(
        root, skill_dir(root, skill) / "scripts" / "track_requirements.py",
        "--root", ".", "--skill", skill,
    )
    if rc != 0:
        return False, f"track rc={rc} err={err[:200]}"
    data = json.loads(out)
    missing = [k for k in ("frontier", "blocked", "deferred", "errors") if k not in data]
    banned = [k for k in ("regression_debt",) if k in data]
    ok = data.get("status") == "ok" and not missing and not banned
    return ok, f"status={data.get('status')} missing={missing} banned={banned}"


@check("req0030-help-clean")
def req0030_help_clean(root: Path, skill: str) -> tuple[bool, str]:
    rc, out, err = run_script(
        root, skill_dir(root, skill) / "scripts" / "track_requirements.py", "--help",
    )
    hits = [t for t in ("last_verified", "regression_debt", "回归债") if t in (out + err)]
    return (not hits), f"hits={hits}"


@check("req0030-no-removed-tokens")
def req0030_no_removed_tokens(root: Path, skill: str) -> tuple[bool, str]:
    hits: set[str] = set()
    for p in skill_files(root, skill, exclude_names=("run_checks.py",)):
        text = read_text(p)
        for tok in ("last_verified", "regression_debt"):
            if tok in text:
                hits.add(tok)
    return (not hits), f"命中={sorted(hits)}"


@check("req0030-no-debt-term")
def req0030_no_debt_term(root: Path, skill: str) -> tuple[bool, str]:
    hits = [p.name for p in skill_files(root, skill, exclude_names=("run_checks.py",))
            if "回归债" in read_text(p)]
    return (not hits), f"含『回归债』的文件={hits}"


@check("req0030-step3-terms")
def req0030_step3_terms(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "reviewing-skills.md")
    need = {k: (k in text) for k in ("全部 REQ", "唯一豁免")}
    banned = {k: (k in text) for k in ("三档范围", "自动升级条件")}
    ok = all(need.values()) and not any(banned.values())
    return ok, f"need={need} banned={banned}"


@check("req0030-step2-no-sweep-ref")
def req0030_step2_no_sweep_ref(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "reviewing-skills.md")
    m = re.search(r"### Step 2[^\n]*\n(.*?)(?=\n### Step 3)", text, re.S)
    if not m:
        return False, "未找到 Step 2 段落"
    seg = m.group(1)
    return ("转全量" not in seg), f"Step2 含『转全量』={'转全量' in seg}"


@check("req0030-writing-req-executable")
def req0030_writing_req_executable(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "writing-requirements.md")
    has_rule = all(m in text for m in ("check:", "（行为）", "（语义）"))
    no_stale = "last_verified" not in text
    return (has_rule and no_stale), f"含 check:/（行为）/（语义）={has_rule} 含 last_verified={not no_stale}"


@check("req0030-req0025-superseded")
def req0030_req0025_superseded(root: Path, skill: str) -> tuple[bool, str]:
    fm = req_frontmatter(root / "docs" / skill / "requirements" / "REQ-0025-spec-regression-sweep.md")
    ok = fm.get("superseded_by") == "REQ-0030" and fm.get("status") == "out-of-scope"
    return ok, f"superseded_by={fm.get('superseded_by')} status={fm.get('status')}"


@check("skill-validate-ok")
def skill_validate_ok(root: Path, skill: str) -> tuple[bool, str]:
    """通用：validate_skill.py 对本技能返回 ok 且退出码 0（各 REQ 复用）。"""
    rc, out, err = run_script(
        root, skill_dir(root, skill) / "scripts" / "validate_skill.py",
        str(skill_dir(root, skill).relative_to(root)),
    )
    try:
        status = json.loads(out).get("status")
    except Exception:
        status = f"<parse-fail> {out[:120]}"
    return (rc == 0 and status == "ok"), f"rc={rc} status={status}"


def _make_iteration(base: Path, with_notes: bool, note_text: str = "PROBE-NOTE") -> Path:
    """造一个最小 iteration 工作区（with_skill + baseline 各 1 个 run）。"""
    ws = base / "it" / "iteration-1"
    for run, pass_rate in (("with_skill", 1.0), ("baseline", 0.5)):
        d = ws / "eval-0" / run
        d.mkdir(parents=True, exist_ok=True)
        (d / "grading.json").write_text(json.dumps({"pass_rate": pass_rate}), encoding="utf-8")
        (d / "timing.json").write_text(
            json.dumps({"total_tokens": 10, "total_duration_seconds": 1.0}), encoding="utf-8")
    (ws / "eval-0" / "eval_metadata.json").write_text(
        json.dumps({"eval_id": 0, "eval_name": "e0"}), encoding="utf-8")
    if with_notes:
        (ws / "analyzer_notes.json").write_text(
            json.dumps({"notes": [note_text]}, ensure_ascii=False), encoding="utf-8")
    return ws


@check("req0034-grader-duties")
def req0034_grader_duties(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "subagents.md")
    m = re.search(r"### grader.*?(?=\n### |\Z)", text, re.S)
    seg = m.group(0) if m else ""
    need = {k: (k in seg) for k in ("隐式主张", "评测集", "claims[]", "eval_feedback[]")}
    return all(need.values()), f"need={need}"


@check("req0034-analyzer-notes-doc")
def req0034_analyzer_notes_doc(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "subagents.md")
    m = re.search(r"### analyzer.*?(?=\n### |\Z)", text, re.S)
    seg = m.group(0) if m else ""
    need = {k: (k in seg) for k in ("恒过", "恒败", "analyzer_notes.json")}
    return all(need.values()), f"need={need}"


@check("req0034-schema-docs")
def req0034_schema_docs(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "running-evals.md")
    need = {k: (k in text) for k in ("claims[]", "eval_feedback[]", "analyzer_notes.json")}
    return all(need.values()), f"need={need}"


@check("req0034-notes-pipeline")
def req0034_notes_pipeline(root: Path, skill: str) -> tuple[bool, str]:
    sd = skill_dir(root, skill)
    note = "PROBE-NOTE-契约可追溯"
    with tempfile.TemporaryDirectory(prefix="shy-r34a-") as tmp:
        ws = _make_iteration(Path(tmp), True, note)
        rc, _out, err = run_script(root, sd / "scripts" / "aggregate_benchmark.py",
                                   str(ws), "--skill-name", skill)
        if rc != 0:
            return False, f"aggregate rc={rc} err={err[:160]}"
        bench = json.loads((ws / "benchmark.json").read_text(encoding="utf-8"))
        in_json = note in (bench.get("notes") or [])
        rc2, _out2, _err2 = run_script(root, sd / "scripts" / "render_report.py",
                                       str(ws), "--skill-name", skill, "--no-open")
        report = ws / "report.html"
        in_html = rc2 == 0 and report.is_file() and note in report.read_text(encoding="utf-8")
    return (in_json and in_html), f"benchmark.json.notes={in_json} report.html={in_html}"


@check("req0034-notes-optional")
def req0034_notes_optional(root: Path, skill: str) -> tuple[bool, str]:
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-r34b-") as tmp:
        ws = _make_iteration(Path(tmp), False)
        rc, _out, err = run_script(root, sd / "scripts" / "aggregate_benchmark.py",
                                   str(ws), "--skill-name", skill)
        if rc != 0:
            return False, f"aggregate rc={rc} err={err[:160]}"
        bench = json.loads((ws / "benchmark.json").read_text(encoding="utf-8"))
    return (not bench.get("notes")), f"无 notes 文件时 notes={bench.get('notes')!r} rc={rc}"


@check("req0034-negative-trigger")
def req0034_negative_trigger(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "writing-skills.md")
    need = {k: (k in text) for k in ("负向触发", "Do NOT use for")}
    return all(need.values()), f"need={need}"


@check("req0035-stop-rule")
def req0035_stop_rule(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "reviewing-skills.md")
    need = {k: (k in text) for k in ("迭代停止规则", "5 轮", "结构性写法")}
    return all(need.values()), f"need={need}"


@check("req0038-plain-language")
def req0038_plain_language(root: Path, skill: str) -> tuple[bool, str]:
    sd = skill_dir(root, skill)
    review = read_text(sd / "references" / "reviewing-skills.md")
    skill_md = read_text(sd / "SKILL.md")
    need_review = {k: (k in review) for k in ("说人话", "说 why", "白话")}
    need_skill = "输出面向人" in skill_md
    ok = all(need_review.values()) and need_skill
    return ok, f"reviewing={need_review} SKILL.输出面向人={need_skill}"


@check("skill-selftest")
def skill_selftest(root: Path, skill: str) -> tuple[bool, str]:
    rc, out, err = run_script(root, skill_dir(root, skill) / "scripts" / "selftest.py")
    tail = (out or err).strip().splitlines()[-1] if (out or err).strip() else ""
    return (rc == 0), f"rc={rc} {tail[:120]}"


@check("req0044-trials")
def req0044_trials(root: Path, skill: str) -> tuple[bool, str]:
    rc, out, _err = run_script(root, skill_dir(root, skill) / "scripts" / "optimize_description.py", "--help")
    ok = (rc == 0) and ("--trials" in out)
    return ok, f"optimize --help 含 --trials={('--trials' in out)}"


@check("req0044-doc")
def req0044_doc(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "running-evals.md")
    ok = "--trials" in text
    return ok, f"running-evals 含 --trials={ok}"


@check("req0045-migration-debt")
def req0045_migration_debt(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "reviewing-skills.md")
    m = re.search(r"### Step 3.*?(?=\n### |\Z)", text, re.S)
    seg = m.group(0) if m else ""
    need = {k: (k in seg) for k in ("迁移债", "只报数", "新写")}
    return all(need.values()), f"need={need}"


@check("req0046-unimplemented-skipped")
def req0046_unimplemented_skipped(root: Path, skill: str) -> tuple[bool, str]:
    """未实现的 REQ（ready/draft）的 `check:` 应跳过，不因未注册而报红。"""
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-skip-") as tmp:
        t = Path(tmp)
        d = t / "docs" / skill / "requirements"
        d.mkdir(parents=True)
        (d / "REQ-9001-ready.md").write_text(
            f"---\nid: REQ-9001\ntitle: r\nskill: {skill}\nstatus: ready\niteration: 1\n"
            "created: 2026-01-01\nupdated: 2026-01-01\nblocked_by: []\n---\n\n"
            "## 验收标准\n\n- [ ] x — `check:no-such-check`\n", encoding="utf-8")
        rc, _out, _err = run_script(root, sd / "scripts" / "run_checks.py",
                                    "--root", str(t), "--skill", skill)
    return (rc == 0), f"ready REQ 的未注册 check 被跳过 → rc={rc}"


@check("req0046-two-paths")
def req0046_two_paths(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "lifecycle.md")
    need = {k: (k in text) for k in ("实现路", "评审路")}
    return all(need.values()), f"need={need}"


@check("req0046-user-triggered")
def req0046_user_triggered(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "lifecycle.md")
    need = {k: (k in text) for k in ("用户主动触发", "实现路不会自动进这里")}
    return all(need.values()), f"need={need}"


@check("req0046-triage")
def req0046_triage(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "lifecycle.md")
    need = {k: (k in text) for k in ("立即修", "以后修", "丢弃", "不落盘", "不自动再审")}
    return all(need.values()), f"need={need}"


@check("req0046-skill-rule")
def req0046_skill_rule(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "SKILL.md")
    ok = "实现 / 评审两路分离" in text
    return ok, f"SKILL 含『实现 / 评审两路分离』={ok}"


@check("req0046-superseded")
def req0046_superseded(root: Path, skill: str) -> tuple[bool, str]:
    ok = True
    ev = {}
    for rid in ("REQ-0041", "REQ-0043"):
        p = list((root / "docs" / skill / "requirements").glob(rid + "-*.md"))
        if not p:
            ev[rid] = "缺失"
            ok = False
            continue
        fm = read_text(p[0]).split("---", 2)[1]
        hit = "superseded_by: REQ-0046" in fm
        ev[rid] = hit
        ok = ok and hit
    return ok, f"{ev}"


@check("req0043-auto-writeback")
def req0043_auto_writeback(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "lifecycle.md")
    need = {k: (k in text) for k in ("机械记账", "不停", "有 P0/P1")}
    return all(need.values()), f"need={need}"


@check("req0043-html-timing")
def req0043_html_timing(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "lifecycle.md")
    ok = "HTML 报告的时机" in text
    return ok, f"含『HTML 报告的时机』={ok}"


@check("req0043-stage4-trigger")
def req0043_stage4_trigger(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "lifecycle.md")
    ok = "机械记账不需确认" in text
    return ok, f"阶段4 含『机械记账不需确认』={ok}"


@check("req0043-review-step8")
def req0043_review_step8(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "reviewing-skills.md")
    m = re.search(r"### Step 8.*?(?=\n### |\Z)", text, re.S)
    seg = m.group(0) if m else ""
    ok = ("呈现门禁" in seg) and ("机械记账" in seg) and ("不回写需求文档" not in seg)
    return ok, f"Step8 引呈现门禁且去掉旧措辞={ok}"


@check("req0042-token-caveat")
def req0042_token_caveat(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "running-evals.md")
    ok = ("没测到" in text) and ("token_ratio" in text) and ("无效" in text)
    return ok, f"含没测到/无效/token_ratio={ok}"


@check("req0042-baseline-method")
def req0042_baseline_method(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "running-evals.md")
    need = {k: (k in text) for k in ("旧版快照", "无技能", "污染")}
    return all(need.values()), f"need={need}"


@check("req0042-pycache-warn")
def req0042_pycache_warn(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "scripts" / "selftest.py")
    ok = ("__pycache__" in text) and ("WARN" in text)
    return ok, f"selftest 含 __pycache__ 警告={ok}"


@check("req0042-count-free")
def req0042_count_free(root: Path, skill: str) -> tuple[bool, str]:
    p = root / "docs" / skill / "requirements" / "REQ-0026-req-doc-consistency.md"
    if not p.is_file():
        return False, "REQ-0026 未找到"
    text = read_text(p)
    m = re.search(r"^##\s+验收标准\s*$(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    seg = m.group(1) if m else ""
    # 只认正向证据（去数字化措辞）——订正标注里引用旧值不算违反
    ok = "不写死数量" in seg
    return ok, f"验收判据含去数字化措辞『不写死数量』={ok}"


@check("req0041-stage2-gate")
def req0041_stage2_gate(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "lifecycle.md")
    m = re.search(r"### 2 · 实现.*?(?=\n### |\Z)", text, re.S)
    seg = m.group(0) if m else ""
    ok = ("findings.json" in seg) and ("阶段 3" in seg)
    return ok, f"阶段2 完成判据含 findings.json={('findings.json' in seg)} 含阶段3={('阶段 3' in seg)}"


@check("req0041-layered")
def req0041_layered(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "lifecycle.md")
    need = {k: (k in text) for k in ("秒级门", "行为 eval", "跳过")}
    return all(need.values()), f"need={need}"


@check("req0041-skill-rule")
def req0041_skill_rule(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "SKILL.md")
    ok = "实现 → 必审" in text
    return ok, f"SKILL 含『实现 → 必审』={ok}"


@check("req0040-selftest-exists")
def req0040_selftest_exists(root: Path, skill: str) -> tuple[bool, str]:
    p = skill_dir(root, skill) / "scripts" / "selftest.py"
    if not p.is_file():
        return False, "selftest.py 不存在"
    text = read_text(p)
    clis = ["validate_skill.py", "scaffold_skill.py", "generate_eval_set.py",
            "optimize_description.py", "agent_runner.py", "aggregate_benchmark.py",
            "render_report.py", "track_requirements.py", "run_checks.py"]
    missing = [c for c in clis if c not in text]
    has_failure = ("!= 0" in text) or ("== 1" in text)
    return (not missing and has_failure), f"缺脚本用例={missing} 含失败路径断言={has_failure}"


@check("req0040-selftest-pure")
def req0040_selftest_pure(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "scripts" / "selftest.py")
    no_open = "--no-open" in text
    third_party = [m for m in ("import pytest", "import requests", "import yaml") if m in text]
    return (no_open and not third_party), f"含--no-open={no_open} 第三方import={third_party}"


@check("req0040-step6-selftest")
def req0040_step6_selftest(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "references" / "reviewing-skills.md")
    m = re.search(r"### Step 6.*?(?=\n### |\Z)", text, re.S)
    seg = m.group(0) if m else ""
    return ("自测" in seg), f"Step6 含『自测』={'自测' in seg}"


@check("req0040-registered")
def req0040_registered(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "scripts" / "run_checks.py")
    return ('"skill-selftest"' in text), f"注册 skill-selftest={chr(34) + 'skill-selftest' + chr(34) in text}"


@check("req0039-negative-boundary")
def req0039_negative_boundary(root: Path, skill: str) -> tuple[bool, str]:
    fm = read_text(skill_dir(root, skill) / "SKILL.md")
    m = re.search(r"^description:\s*(.+)$", fm, re.M)
    desc = m.group(1) if m else ""
    has_boundary = "不适用于" in desc
    return (has_boundary and len(desc) <= 1024), f"含『不适用于』={has_boundary} 长度={len(desc)}"


# --------------------------------------------------------------------------- #
# 发现与执行
# --------------------------------------------------------------------------- #

def discover(root: Path, skill: str | None) -> list[Path]:
    if skill:
        base = root / "docs" / skill / "requirements"
        return sorted(base.glob("REQ-*.md")) if base.is_dir() else []
    return sorted(root.glob("docs/*/requirements/REQ-*.md"))


def criteria(path: Path) -> list[str]:
    """抽出 `## 验收标准` 段内的 `- [ ]` / `- [x]` 行。"""
    text = read_text(path)
    m = re.search(r"^##\s+验收标准\s*$\n(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    if not m:
        return []
    return [ln.strip() for ln in m.group(1).splitlines() if CRITERION_RE.match(ln)]


def analyze(root: Path, skill: str | None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    behavior = 0
    semantic = 0
    untagged = 0
    skipped = 0
    passed = 0
    failed = 0

    for path in discover(root, skill):
        fm = req_frontmatter(path)
        req_skill = fm.get("skill", "")
        rid = fm.get("id", path.stem)
        # 只有「已实现中 / 已完成」的 REQ 才跑 check:。
        # 未实现的（draft / ready）与不做的（deferred / out-of-scope）一律跳过——
        # 它们的 check: 是"未来契约"，此刻跑必红，是噪声。
        skip_exec = (fm.get("status") or "").strip() not in ("in-progress", "done")
        for desc in criteria(path):
            tag = CHECK_TAG_RE.search(desc)
            if not tag:
                if BEHAVIOR_RE.search(desc):
                    behavior += 1
                elif SEMANTIC_RE.search(desc):
                    semantic += 1
                else:
                    untagged += 1
                continue
            if skip_exec:
                skipped += 1
                continue
            name = tag.group("name")
            fn = CHECKS.get(name)
            if fn is None:
                failed += 1
                errors.append({"req": rid, "check": name, "error": "未注册的 check"})
                rows.append({"req": rid, "check": name, "passed": False,
                             "evidence": "未注册的 check"})
                continue
            ok, evidence = fn(root, req_skill)
            passed += 0 if not ok else 1
            failed += 0 if ok else 1
            rows.append({"req": rid, "check": name, "passed": ok, "evidence": evidence})

    total = passed + failed
    return {
        "status": "ok" if failed == 0 and not errors else "fail",
        "executable": {"total": total, "passed": passed, "failed": failed},
        "behavior": behavior,
        "semantic": semantic,
        "untagged": untagged,
        "skipped": skipped,
        "checks": rows,
        "errors": errors,
        "hint": "untagged>0 表示有验收标准没标三类之一（check: / （行为） / （语义））——按 writing-requirements.md §3 补标；skipped 为 deferred / out-of-scope 的 REQ 跳过的 check 数",
    }


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description=(
            "跑 REQ `## 验收标准` 里标了 `check:<name>` 的可执行条目。"
            "Spec 轴默认靠跑不靠读；标（语义）的条目另由人/agent 判。"
        ),
        epilog=(
            "示例:\n"
            "  python run_checks.py --root .\n"
            "  python run_checks.py --root . --skill shy-skill-suite\n"
            "  python run_checks.py --list\n"
            "  python run_checks.py --root . --output checks.json\n"
            "\n"
            "退出码:\n"
            "  0  全部可执行条目通过\n"
            "  1  有失败，或引用了未注册的 check\n"
            "  2  参数错误\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", default=".", help="Repo root to scan (default: .)")
    parser.add_argument("--skill", help="Limit to docs/<skill>/requirements/")
    parser.add_argument("--list", action="store_true", help="List registered check names and exit")
    parser.add_argument("--output", "-o", help="Write the full JSON to this path")
    args = parser.parse_args()

    if args.list:
        print("\n".join(sorted(CHECKS)))
        return 0

    root = Path(args.root).resolve()
    result = analyze(root, args.skill)
    result["root"] = str(root)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    for row in result["checks"]:
        mark = "PASS" if row["passed"] else "FAIL"
        print(f"[{mark}] {row['req']} {row['check']}  {row['evidence']}")
    e = result["executable"]
    print(f"\ncheck: {e['total']} 条：{e['passed']} 通过 / {e['failed']} 失败；"
          f"（行为）{result['behavior']}；（语义）{result['semantic']}；"
          f"未标型 {result['untagged']}；跳过（deferred/out-of-scope）{result['skipped']}")
    return 1 if result["status"] != "ok" else 0


if __name__ == "__main__":
    sys.exit(main())
