#!/usr/bin/env python3
"""跑需求文档（REQ）里**可执行**的验收标准。

复审的 Spec 轴默认**靠跑不靠读**：把全部 REQ 的 `## 验收标准` 里标了
`` `check:<name>` `` 的条目一次跑完，秒级出结果。只有标 `（语义）` 的条目
才需要逐条读、判通过 / 部分 / 未实现。

- 发现：扫描 `docs/<skill>/requirements/REQ-*.md` 的 `## 验收标准` 段。
- 可执行条目写法：`` - [ ] <描述> — `check:<name>` ``；条目其余部分是人读的描述。
- 语义条目写法：`` - [ ] <描述>（语义） ``——无法机械判定，交 Step 3 人/agent 判。
- episode 写法：`` - [ ] <描述>（episode） ``——一次性事实，冻结、**不进 Gate**（见设计 §4.2）。
- 检查实现：本文件底部的注册表（按 REQ 追加）。名称用 kebab-case，前缀 REQ id 防撞。

用法:
    python run_checks.py [--root .] [--skill <name>] [--list] [--output <path>]

默认打有界摘要（每条 check 一行 + 计数）；`--list` 只列注册的检查名。

退出码:
    0  全部可执行条目通过，且无未清迁移债
    1  有失败 / 引用了未注册的 check / 带迁移债未收敛 / 无 docs（n/a）
    2  参数错误
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

from skill_utils import force_utf8_stdio, read_text

CRITERION_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s*(?P<desc>.+)$")
CHECK_TAG_RE = re.compile(r"`check:\s*(?P<name>[a-z0-9-]+)\s*`")
BEHAVIOR_RE = re.compile(r"（行为）|\(behavior\)")
SEMANTIC_RE = re.compile(r"（语义）|\(semantic\)")
EPISODE_RE = re.compile(r"（episode）|\(episode\)")

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


def find_req(root: Path, skill: str, rid: str) -> Path | None:
    """按 id 在技能需求目录里找 REQ 文件。

    只按 ``<id>-*.md`` 匹配、不写死 slug——这样技能脚本不嵌入本仓库的具体
    文件名，复制到别处也不会留下悬空指针（技能必须自包含）。
    """
    base = root / "docs" / skill / "requirements"
    if not base.is_dir():
        return None
    hits = sorted(base.glob(f"{rid}-*.md"))
    return hits[0] if hits else None


def cleanup_counts(root: Path, skill: str) -> tuple[int, int] | None:
    """`cleanup.md` 的 (open, fixed) 计数——Gate 消费台账（设计 §4.3）。无文件返回 None。"""
    p = root / "docs" / skill / "cleanup.md"
    if not p.is_file():
        return None
    o = f = 0
    for ln in read_text(p).splitlines():
        s = ln.lstrip()
        if s.startswith("| CL-"):
            cols = [c.strip().strip("*").strip() for c in s.strip().strip("|").split("|")]
            if len(cols) >= 5:
                if cols[4] == "open":
                    o += 1
                elif cols[4] == "fixed":
                    f += 1
    return o, f


def fix_counts(root: Path, skill: str) -> tuple[int, int]:
    """fix 类工单的 (open, fixed)：open = ready/in-progress，fixed = done。"""
    base = root / "docs" / skill / "requirements"
    o = f = 0
    if base.is_dir():
        for p in base.glob("REQ-*.md"):
            fm = req_frontmatter(p)
            if fm.get("kind") != "fix":
                continue
            st = fm.get("status", "")
            if st in ("ready", "in-progress"):
                o += 1
            elif st == "done":
                f += 1
    return o, f


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


@check("req0046-unimplemented-skipped")
def req0046_unimplemented_skipped(root: Path, skill: str) -> tuple[bool, str]:
    """未实现的 REQ（ready/draft）的 `check:` 应跳过，不因未注册而报红。"""
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-skip-") as tmp:
        t = Path(tmp)
        d = t / "docs" / skill / "requirements"
        d.mkdir(parents=True)
        (d / "REQ-9001.md").write_text(
            f"---\nid: REQ-9001\ntitle: r\nskill: {skill}\nstatus: ready\niteration: 1\n"
            "created: 2026-01-01\nupdated: 2026-01-01\nblocked_by: []\n---\n\n"
            "## 验收标准\n\n- [ ] x — `check:no-such-check`\n", encoding="utf-8")
        rc, _out, _err = run_script(root, sd / "scripts" / "run_checks.py",
                                    "--root", str(t), "--skill", skill)
    return (rc == 0), f"ready REQ 的未注册 check 被跳过 → rc={rc}"


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


@check("req0048-no-hardcoded-req-file")
def req0048_no_hardcoded_req_file(root: Path, skill: str) -> tuple[bool, str]:
    """技能脚本不得嵌入具体 REQ 文件名（slug），否则复制部署即悬空。"""
    hits: list[str] = []
    for p in sorted((skill_dir(root, skill) / "scripts").glob("*.py")):
        for ln, line in enumerate(read_text(p).splitlines(), 1):
            if re.search(r"REQ-\d{4}-[a-z]", line):
                hits.append(f"{p.name}:{ln}")
    return (not hits), f"硬编码 REQ 文件名={hits}"


@check("req0048-find-req-helper")
def req0048_find_req_helper(root: Path, skill: str) -> tuple[bool, str]:
    text = read_text(skill_dir(root, skill) / "scripts" / "run_checks.py")
    ok = "def find_req(" in text
    return ok, f"run_checks 含 find_req 助手={ok}"


@check("req0049-evals-present")
def req0049_evals_present(root: Path, skill: str) -> tuple[bool, str]:
    p = skill_dir(root, skill) / "evals" / "evals.json"
    if not p.is_file():
        return False, "evals/evals.json 不存在"
    try:
        data = json.loads(read_text(p))
    except Exception as exc:  # noqa: BLE001 - 报错即可
        return False, f"解析失败：{exc}"
    evals = data.get("evals") or []
    pos = any(e.get("should_trigger") for e in evals)
    neg = any(not e.get("should_trigger", True) for e in evals)
    return (bool(evals) and pos and neg), f"evals={len(evals)} 正例={pos} 负例={neg}"


@check("req0050-retired")
def req0050_retired(root: Path, skill: str) -> tuple[bool, str]:
    """4 条文档措辞子串 check 已退休：不在注册表、REQ-0046 里标了 （episode）。"""
    gone = [n for n in ("req0046-two-paths", "req0046-user-triggered",
                        "req0046-triage", "req0046-skill-rule") if n in CHECKS]
    ep = 0
    p = find_req(root, skill, "REQ-0046")
    if p:
        m = re.search(r"^##\s+验收标准\s*$\n(.*?)(?=^##\s|\Z)", read_text(p), re.S | re.M)
        ep = m.group(1).count("（episode）") if m else 0
    return (not gone and ep >= 4), f"仍注册={gone} REQ-0046 episode={ep}"


@check("req0050-episode-recognized")
def req0050_episode_recognized(root: Path, skill: str) -> tuple[bool, str]:
    """run_checks 识别 （episode） 并单独计数（不再算未标）。"""
    src = read_text(skill_dir(root, skill) / "scripts" / "run_checks.py")
    ok = "EPISODE_RE" in src and '"episode": episode' in src
    return ok, f"run_checks 识别 episode={ok}"


@check("validate-rejects-bad")
def validate_rejects_bad(root: Path, skill: str) -> tuple[bool, str]:
    """validate_skill.py 对含多余字段的技能 → 非 0。"""
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-vrb-") as tmp:
        d = Path(tmp) / "bad"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\nname: bad\ndescription: x\nname_cn: 坏\n---\n\n# bad\n", encoding="utf-8")
        rc, _o, _e = run_script(root, sd / "scripts" / "validate_skill.py", str(d))
    return rc != 0, f"多余字段 → rc={rc}"


@check("scaffold-ok")
def scaffold_ok(root: Path, skill: str) -> tuple[bool, str]:
    """scaffold：创建 / 幂等 / 非法名拒绝 / --force 留 .bak。"""
    s = skill_dir(root, skill) / "scripts" / "scaffold_skill.py"
    with tempfile.TemporaryDirectory(prefix="shy-sco-") as tmp:
        t = Path(tmp)
        rc1, _o1, _e1 = run_script(root, s, "demo", "--path", str(t), "--description", "x")
        created = (t / "demo" / "SKILL.md").is_file()
        rc2, o2, _e2 = run_script(root, s, "demo", "--path", str(t), "--description", "x")
        idem = rc2 == 0 and "skipped" in o2
        rc3, _o3, _e3 = run_script(root, s, "Bad_Name", "--path", str(t))
        bad = rc3 != 0
        rc4, _o4, _e4 = run_script(root, s, "demo", "--path", str(t), "--force", "--description", "y")
        bak = (t / "demo" / "SKILL.md.bak").is_file()
    ok = rc1 == 0 and created and idem and bad and rc4 == 0 and bak
    return ok, f"create={created} idem={idem} bad={bad} bak={bak}"


@check("scripts-help-ok")
def scripts_help_ok(root: Path, skill: str) -> tuple[bool, str]:
    """全部脚本 --help → rc 0 且输出非空。"""
    fails = []
    for p in sorted((skill_dir(root, skill) / "scripts").glob("*.py")):
        if p.name == "skill_utils.py":
            continue
        rc, out, err = run_script(root, p, "--help")
        if rc != 0 or not (out or err).strip():
            fails.append(f"{p.name}(rc={rc})")
    return (not fails), f"--help 失败={fails}"


@check("render-report-ok")
def render_report_ok(root: Path, skill: str) -> tuple[bool, str]:
    """render_report：有数据 rc 0 + report.html；无数据 rc 非 0 + stderr；--help 含 --no-open。"""
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-rro-") as tmp:
        ws = _make_iteration(Path(tmp), False)
        rc1, _o1, _e1 = run_script(root, sd / "scripts" / "render_report.py",
                                   str(ws), "--skill-name", skill, "--no-open")
        html = (ws / "report.html").is_file()
        rc2, _o2, err2 = run_script(root, sd / "scripts" / "render_report.py",
                                    str(Path(tmp) / "empty"), "--no-open")
        nodata = rc2 != 0 and bool((err2 or "").strip())
        rc3, out3, _e3 = run_script(root, sd / "scripts" / "render_report.py", "--help")
        helpok = rc3 == 0 and "--no-open" in out3
    ok = rc1 == 0 and html and nodata and helpok
    return ok, f"rc={rc1} html={html} nodata={nodata} help={helpok}"


@check("agent-runner-error")
def agent_runner_error(root: Path, skill: str) -> tuple[bool, str]:
    """agent_runner 坏命令 → rc 非 0、stderr 非空、stdout 空。"""
    rc, out, err = run_script(root, skill_dir(root, skill) / "scripts" / "agent_runner.py",
                              "--runner", "cmd", "--cmd", "no-such-exe {prompt}", "--prompt", "x")
    ok = rc != 0 and bool(err.strip()) and not out.strip()
    return ok, f"rc={rc} stderr={bool(err.strip())} stdout_empty={not out.strip()}"


@check("track-ok")
def track_ok(root: Path, skill: str) -> tuple[bool, str]:
    """track_requirements → status ok。"""
    rc, out, _e = run_script(root, skill_dir(root, skill) / "scripts" / "track_requirements.py",
                             "--root", ".", "--skill", skill)
    try:
        ok = rc == 0 and json.loads(out).get("status") == "ok"
    except Exception:  # noqa: BLE001
        ok = False
    return ok, f"rc={rc}"


@check("optimize-ok")
def optimize_ok(root: Path, skill: str) -> tuple[bool, str]:
    """optimize_description 启发式 → rc 0、mode heuristic。"""
    sd = skill_dir(root, skill)
    rc, out, _e = run_script(root, sd / "scripts" / "optimize_description.py", str(sd),
                             "--eval-set", str(sd / "evals" / "evals.json"))
    try:
        ok = rc == 0 and json.loads(out).get("mode") == "heuristic"
    except Exception:  # noqa: BLE001
        ok = False
    return ok, f"rc={rc}"


@check("benchmark-json")
def benchmark_json(root: Path, skill: str) -> tuple[bool, str]:
    """aggregate_benchmark → rc 0 + 合法 JSON。"""
    with tempfile.TemporaryDirectory(prefix="shy-bj-") as tmp:
        ws = _make_iteration(Path(tmp), False)
        rc, out, _e = run_script(root, skill_dir(root, skill) / "scripts" / "aggregate_benchmark.py",
                                 str(ws), "--skill-name", skill)
    try:
        json.loads(out)
        ok = rc == 0
    except Exception:  # noqa: BLE001
        ok = False
    return ok, f"rc={rc}"


@check("generate-eval-set-ok")
def generate_eval_set_ok(root: Path, skill: str) -> tuple[bool, str]:
    """generate_eval_set → rc 0 + 产出 JSON。"""
    with tempfile.TemporaryDirectory(prefix="shy-ges-") as tmp:
        outp = Path(tmp) / "evals.json"
        rc, _o, _e = run_script(root, skill_dir(root, skill) / "scripts" / "generate_eval_set.py",
                                str(skill_dir(root, skill)), "-o", str(outp))
        produced = outp.is_file()
    return (rc == 0 and produced), f"rc={rc} produced={produced}"


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
    episode = 0
    untagged = 0
    skipped = 0
    passed = 0
    failed = 0
    cache: dict[tuple[str, str], tuple[bool, str]] = {}
    seen: set[tuple[str, str]] = set()   # 每个 check 只出一行、只计一次

    # 预跑：把所有被引用的 check **去重**后**并行**跑一次。
    # 两个目的：① 全局 check（skill-validate-ok 等）不随引用条数放大；② 子进程为主，串行太慢。
    jobs: set[tuple[str, str]] = set()
    for path in discover(root, skill):
        fm0 = req_frontmatter(path)
        if (fm0.get("status") or "").strip() not in ("in-progress", "done"):
            continue
        for desc in criteria(path):
            tag = CHECK_TAG_RE.search(desc)
            if tag and tag.group("name") in CHECKS:
                jobs.add((tag.group("name"), fm0.get("skill", "")))
    if jobs:
        with ThreadPoolExecutor(max_workers=min(8, len(jobs))) as ex:
            futs = {j: ex.submit(CHECKS[j[0]], root, j[1]) for j in jobs}
            for j, fut in futs.items():
                try:
                    cache[j] = fut.result()
                except Exception as exc:  # noqa: BLE001
                    cache[j] = (False, f"check 异常: {exc}")

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
                elif EPISODE_RE.search(desc):
                    episode += 1
                else:
                    untagged += 1
                continue
            if skip_exec:
                skipped += 1
                continue
            name = tag.group("name")
            fn = CHECKS.get(name)
            if fn is None:
                if (name, req_skill) not in seen:
                    seen.add((name, req_skill))
                    failed += 1
                    errors.append({"req": rid, "check": name, "error": "未注册的 check"})
                    rows.append({"req": rid, "check": name, "passed": False,
                                 "evidence": "未注册的 check"})
                continue
            ckey = (name, req_skill)
            if ckey not in cache:          # 全局 check 整轮只跑 1 次，不随引用条数放大
                cache[ckey] = fn(root, req_skill)
            ok, evidence = cache[ckey]
            if ckey not in seen:           # 同一个 check 只出一行、只计一次
                seen.add(ckey)
                passed += 0 if not ok else 1
                failed += 0 if ok else 1
                rows.append({"req": rid, "check": name, "passed": ok, "evidence": evidence})

    total = passed + failed
    return {
        "status": "ok" if failed == 0 and not errors else "fail",
        "executable": {"total": total, "passed": passed, "failed": failed},
        "behavior": behavior,
        "semantic": semantic,
        "episode": episode,
        "untagged": untagged,
        "skipped": skipped,
        "checks": rows,
        "errors": errors,
        "hint": "untagged>0 表示有验收标准没标四类之一（check: / （行为） / （语义） / （episode））——未分类项即**迁移债**（不设默认、挂 `（未定）`）；episode 为一次性事实、不进 Gate；skipped 为 deferred / out-of-scope 的 REQ 跳过的 check 数",
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
            "  0  全部可执行条目通过，且无未清迁移债\n"
            "  1  有失败 / 未注册 check / 带迁移债未收敛 / 无 docs（n/a）\n"
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
    cc = cleanup_counts(root, args.skill) if args.skill else None
    fc = fix_counts(root, args.skill) if args.skill else None
    result["cleanup_open"] = cc[0] if cc else None

    # V6：没有 REQ = 不适用，不是"绿"（技能单独部署时不得假绿）。
    if not result["checks"] and not result["executable"]["total"]:
        if args.skill and not (root / "docs" / args.skill / "requirements").is_dir():
            result["status"] = "n/a"
    # V1：带迁移债不得判绿（债门，设计 §4.7）。
    if args.skill:
        st = root / "docs" / args.skill / "state.json"
        if st.is_file():
            try:
                target = int((json.loads(read_text(st)).get("debt_targets") or {})
                             .get("unclassified_criteria", 0))
            except Exception:  # noqa: BLE001
                target = 0
            if result["untagged"] > target and result["status"] == "ok":
                result["status"] = "debt"
                result["debt_target"] = target

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    for row in result["checks"]:
        mark = "PASS" if row["passed"] else "FAIL"
        print(f"[{mark}] {row['req']} {row['check']}  {row['evidence']}")
    if result["status"] == "n/a":
        print("[n/a] 未发现任何 REQ（docs/<skill>/requirements 缺失）——Gate 不适用，**不得当绿**")
    elif result["status"] == "debt":
        print(f"[debt] 未分类迁移债 {result['untagged']} > 目标 {result.get('debt_target')}——**未收敛，Gate 不判绿**")
    if cc is not None and fc is not None:
        print(f"问题: open={cc[0] + fc[0]}（台账 {cc[0]} + fix 工单 {fc[0]}） "
              f"fixed={cc[1] + fc[1]}（台账 {cc[1]} + fix 工单 {fc[1]}）")
    e = result["executable"]
    cleanup_note = ""
    if result.get("cleanup_open") is not None:
        cleanup_note = f"；台账 open {result['cleanup_open']}"
    print(f"\ncheck: {e['total']} 条：{e['passed']} 通过 / {e['failed']} 失败；"
          f"（行为）{result['behavior']}；（语义）{result['semantic']}；"
          f"（episode）{result['episode']}；"
          f"未分类(迁移债) {result['untagged']}；跳过（deferred/out-of-scope）{result['skipped']}"
          f"{cleanup_note}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
