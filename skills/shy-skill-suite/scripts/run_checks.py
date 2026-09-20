#!/usr/bin/env python3
"""跑需求文档（REQ）里**可执行**的验收标准。

复审的 Spec 轴默认**靠跑不靠读**：把全部 REQ 的 `## 验收标准` 里标了
`` `check:<name>` `` 的条目一次跑完，秒级出结果。只有标 `（语义）` 的条目
才需要逐条读、判通过 / 部分 / 未实现。

- 发现：扫描 `docs/<skill>/requirements/REQ-*.md` 的 `## 验收标准` 段。
- 可执行条目写法：`` - [ ] <描述> — `check:<name>` ``；条目其余部分是人读的描述。
- 语义条目写法：`` - [ ] <描述>（语义） ``——无法机械判定，交 Step 3 人/agent 判。
- episode 写法：`` - [ ] <描述>（episode） ``——一次性事实，冻结、**不进 Gate**。
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
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

from skill_utils import force_utf8_stdio, read_text

CRITERION_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s*(?P<desc>.+)$")
CHECK_TAG_RE = re.compile(r"`check:\s*(?P<name>[a-z0-9-]+)\s*`")
BEHAVIOR_RE = re.compile(r"（行为）|\(behavior\)")
SEMANTIC_RE = re.compile(r"（语义）|\(semantic\)")
EPISODE_RE = re.compile(r"[（(\[【]\s*episode\s*[）)\]】]", re.IGNORECASE)

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
    """`cleanup.md` 的 (open, fixed) 计数——Gate 消费台账。无文件返回 None。"""
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


@check("req0040-selftest-exists")
def req0040_selftest_exists(root: Path, skill: str) -> tuple[bool, str]:
    p = skill_dir(root, skill) / "scripts" / "selftest.py"
    if not p.is_file():
        return False, "selftest.py 不存在"
    text = read_text(p)
    clis = ["validate_skill.py", "scaffold_skill.py", "generate_eval_set.py",
            "optimize_description.py", "agent_runner.py", "run_effectiveness.py",
            "aggregate_benchmark.py",
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


@check("req0053-report-human")
def req0053_report_human(root: Path, skill: str) -> tuple[bool, str]:
    """HTML 报告只渲染人字段；证伪 / 证据（过程字段）不得出现。"""
    sd = skill_dir(root, skill)
    sentinel_f = "SENTINEL-FALSIFY-XYZZY"
    sentinel_e = "SENTINEL-EVIDENCE-XYZZY"
    with tempfile.TemporaryDirectory(prefix="shy-r53-") as tmp:
        ws = _make_iteration(Path(tmp), False)
        (ws / "findings.json").write_text(json.dumps({
            "skill": skill, "verdict": "可合入",
            "findings": [{
                "axis": "行为", "priority": "P1", "location": "x:1",
                "problem": "存在问题白话 {{TRIAGE_ACTIONS}}", "plain": "白话解释白话",
                "suggestion": "建议白话",
                "falsification": sentinel_f, "evidence": sentinel_e,
            }],
        }, ensure_ascii=False), encoding="utf-8")
        rc, _out, err = run_script(root, sd / "scripts" / "render_report.py",
                                   str(ws), "--skill-name", skill, "--no-open")
        report = ws / "report.html"
        html = report.read_text(encoding="utf-8") if rc == 0 and report.is_file() else ""
    # 可见字段检查 + 整份文件不得含过程字段（含内嵌数据载荷）。
    visible = re.sub(r"<script>.*?</script>", "", html, flags=re.S)
    human = all(t in visible for t in ("存在问题白话", "白话解释白话", "建议白话",
                                        "存在问题", "白话解释", "修改建议"))
    leaked = (sentinel_f in html) or (sentinel_e in html)
    match = re.search(r"const DATA = (\{.*?\});</script>", html, re.S)
    embedded_ok = bool(match)
    if match:
        try:
            json.loads(match.group(1))
        except Exception:  # noqa: BLE001 - 载荷必须可解析（数据含占位符字面量时也要成立）
            embedded_ok = False
    return (rc == 0 and human and not leaked and embedded_ok), \
        f"rc={rc} 人字段={human} 泄漏={leaked} 内嵌JSON可解析={embedded_ok}"


@check("report-evidence-banner")
def report_evidence_banner(root: Path, skill: str) -> tuple[bool, str]:
    """报告顶部按 `evidence.status` 渲染行为轴证据来源 / 降级条。

    `matched` → 绿条（带轮次）；`static` / `stale` / 缺失 → 黄条（降级）。
    """
    import render_report as rr

    template = read_text(skill_dir(root, skill) / "assets" / "report-template.html")

    def banner(evidence: object) -> str:
        return rr.build_html({
            "skill_name": "x", "iteration": 1, "generated_at": "t",
            "benchmark": None, "evals": [],
            "findings": {
                "skill": "x", "verdict": "可合入",
                "summary": {"candidates": 0, "passed": 0, "falsified": 0},
                "evidence": evidence, "findings": [],
            },
        }, template)

    matched = banner({"status": "matched", "iteration": "iteration-3"})
    static = banner({"status": "static"})
    stale = banner({"status": "stale"})
    absent = banner(None)
    ok = (
        'class="evidence ok"' in matched and "iteration-3" in matched
        and 'class="evidence warn"' in static and "（静态）待验证" in static
        and 'class="evidence warn"' in stale and "过期" in stale
        and 'class="evidence warn"' in absent and "（静态）待验证" in absent
    )
    return ok, (f"matched={('evidence ok' in matched)} static={('evidence warn' in static)} "
                f"stale={('evidence warn' in stale)} absent={('evidence warn' in absent)}")


@check("req0053-glossary")
def req0053_glossary(root: Path, skill: str) -> tuple[bool, str]:
    """套件词汇表存在且 ≥5 条（术语 / 一行白话 / `_避免_`）。"""
    p = skill_dir(root, skill) / "references" / "glossary.md"
    if not p.is_file():
        return False, "references/glossary.md 不存在"
    terms = re.findall(r"^\*\*(.+?)\*\*", read_text(p), re.M)
    return (len(terms) >= 5), f"术语数={len(terms)}"


@check("req0054-triage-ui")
def req0054_triage_ui(root: Path, skill: str) -> tuple[bool, str]:
    """serve 报告每条 finding 带三选一（默认立即修），动作栏只有「提交给 agent」。"""
    import render_report as rr

    template = read_text(skill_dir(root, skill) / "assets" / "report-template.html")
    data = {
        "skill_name": "x", "iteration": 1, "generated_at": "t",
        "benchmark": None, "evals": [],
        "findings": {"findings": [{"axis": "行为", "priority": "P1", "location": "x:1",
                                   "problem": "p", "plain": "pl", "suggestion": "s"}]},
    }
    served = re.sub(r"<script>.*?</script>", "",
                    rr.build_html(data, template, "/triage?t=TOKEN"), flags=re.S)
    need = ['data-fid="F1"', 'data-location=', 'value="立即修" checked', 'value="以后修"', 'value="丢弃"',
            'id="btnSubmit"']
    missing = [n for n in need if n not in served]
    extra = [n for n in ('id="btnCopy"', 'id="btnDownload"', 'id="btnReset"') if n in served]
    external = re.findall(r"https?://", served)
    ok = not missing and not extra and not external
    return ok, f"缺={missing} 多余按钮={extra} 外链={len(external)}"


@check("req0056-serve")
def req0056_serve(root: Path, skill: str) -> tuple[bool, str]:
    """--serve：GET 含端点、坏 token 403、正确 POST 写 triage.json 并退出；静态版无端点。"""
    import urllib.error
    import urllib.request

    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-r56-") as tmp:
        ws = _make_iteration(Path(tmp), False)
        (ws / "findings.json").write_text(json.dumps({
            "skill": skill, "verdict": "可合入",
            "findings": [{"axis": "行为", "priority": "P1", "location": "x:1",
                          "problem": "p", "impact": "i", "suggestion": "s", "expected": "e"}],
        }, ensure_ascii=False), encoding="utf-8")
        # 静态模式：页面无端点
        run_script(root, sd / "scripts" / "render_report.py",
                   str(ws), "--skill-name", skill, "--no-open")
        static_html = (ws / "report.html").read_text(encoding="utf-8")
        static_ok = 'var ENDPOINT = "";' in static_html
        # 选一个空闲端口
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = dict(os.environ, PYTHONIOENCODING="utf-8", SHY_NO_OPEN="1")
        proc = subprocess.Popen(
            [sys.executable, str(sd / "scripts" / "render_report.py"), str(ws),
             "--skill-name", skill, "--serve", "--no-open",
             "--serve-port", str(port), "--serve-timeout", "20"],
            cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", env=env)
        token = ""
        deadline = time.time() + 15
        while time.time() < deadline and not token:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1) as resp:
                    page = resp.read().decode("utf-8")
                match = re.search(r"/triage\?t=([A-Za-z0-9_\-]+)", page)
                if match:
                    token = match.group(1)
            except Exception:  # noqa: BLE001 - 服务未起时重试
                time.sleep(0.2)
        bad = post_ok = False
        if token:
            body = json.dumps({"triage": [{"id": "F1", "choice": "立即修"}]}).encode("utf-8")
            try:
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/triage?t=WRONG", data=body, method="POST",
                    headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=2)
            except urllib.error.HTTPError as exc:
                bad = exc.code == 403
            except Exception:  # noqa: BLE001
                bad = False
            try:
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/triage?t={token}", data=body, method="POST",
                    headers={"Content-Type": "application/json"})
                post_ok = urllib.request.urlopen(req, timeout=2).status == 200
            except Exception:  # noqa: BLE001
                post_ok = False
        try:
            proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
        triage = ws / "triage.json"
        written = triage.is_file() and "F1" in triage.read_text(encoding="utf-8")
    ok = static_ok and bool(token) and bad and post_ok and written
    return ok, (f"静态无端点={static_ok} token={bool(token)} 坏token403={bad} "
                f"POST={post_ok} triage.json={written}")


@check("req0057-serve-actions")
def req0057_serve_actions(root: Path, skill: str) -> tuple[bool, str]:
    """serve 底栏只有「提交给 agent」；静态报告只读（无控件 / 按钮）；两者都无顶部工具条。"""
    import render_report as rr

    template = read_text(skill_dir(root, skill) / "assets" / "report-template.html")
    data = {
        "skill_name": "x", "iteration": 1, "generated_at": "t",
        "benchmark": None, "evals": [],
        "findings": {"findings": [{"axis": "行为", "priority": "P1", "location": "x:1",
                                   "problem": "问题 {{TRIAGE_ACTIONS}}", "plain": "白话",
                                   "suggestion": "建议"}]},
    }
    served = re.sub(r"<script>.*?</script>", "",
                    rr.build_html(data, template, "/triage?t=TOKEN"), flags=re.S)
    static = re.sub(r"<script>.*?</script>", "", rr.build_html(data, template), flags=re.S)
    no_buttons = ('id="btnCopy"', 'id="btnDownload"', 'id="btnReset"')
    checks = {
        "serve有提交": 'id="btnSubmit"' in served,
        "serve提交唯一": served.count('id="btnSubmit"') == 1,
        "serve动作栏唯一": served.count('id="actions"') == 1,
        "serve无复制/下载/清空": all(x not in served for x in no_buttons),
        "serve有控件": 'data-fid="F1"' in served,
        "静态无控件": 'data-fid="F1"' not in static and 'class="triage"' not in static,
        "静态无按钮": 'id="btnSubmit"' not in static and all(x not in static for x in no_buttons),
        "静态只读提示": "只读版" in static,
        "无顶部工具条": "toolbar" not in served,
        "默认立即修": 'value="立即修" checked' in served,
        "占位符字面量保留(不注入正文)": '{{TRIAGE_ACTIONS}}' in served and '{{TRIAGE_ACTIONS}}' in static,
    }
    failed = [k for k, v in checks.items() if not v]
    return (not failed), f"未过={failed}"


@check("req0067-detect-skill-line")
def req0067_detect_skill_line(root: Path, skill: str) -> tuple[bool, str]:
    """skill-line 模式：只提及技能名不算触发，出现 `Skill "名"` 加载行才算。"""
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-r67-") as tmp:
        t = Path(tmp)
        mention = t / "mention.py"
        mention.write_text("print('see shy-skill-suite docs')\n", encoding="utf-8")
        loadline = t / "loadline.py"
        loadline.write_text("print('-> Skill \"shy-skill-suite\"')\n", encoding="utf-8")
        tpl_m = f'"{sys.executable}" "{mention}" {{prompt}}'
        tpl_l = f'"{sys.executable}" "{loadline}" {{prompt}}'
        rc1, out1, _ = run_script(root, sd / "scripts" / "agent_runner.py",
                                  "--runner", "cmd", "--cmd", tpl_m, "--detect", skill,
                                  "--detect-mode", "skill-line", "--prompt", "x")
        rc2, out2, _ = run_script(root, sd / "scripts" / "agent_runner.py",
                                  "--runner", "cmd", "--cmd", tpl_l, "--detect", skill,
                                  "--detect-mode", "skill-line", "--prompt", "x")
    mention_ok = rc1 == 1 and '"triggered": false' in out1
    load_ok = rc2 == 0 and '"triggered": true' in out2
    return (mention_ok and load_ok), f"仅提及 未触发={mention_ok}(rc={rc1})；加载行 触发={load_ok}(rc={rc2})"


@check("req0065-cwd-isolation")
def req0065_cwd_isolation(root: Path, skill: str) -> tuple[bool, str]:
    """--isolate-cwd：每次运行在基目录下用独立空目录（跑完即删），基目录零残留。"""
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-r65-") as tmp:
        t = Path(tmp)
        base = t / "runs"
        base.mkdir()
        writer = t / "writer.py"
        writer.write_text(
            "import pathlib\n"
            "pathlib.Path('artifact.txt').write_text('x', encoding='utf-8')\n"
            "print('SENTINEL-TRIGGER')\n",
            encoding="utf-8",
        )
        evals = t / "evals.json"
        evals.write_text(json.dumps({
            "skill_name": "x",
            "evals": [
                {"eval_id": i, "eval_name": f"t{i}", "prompt": f"p{i}", "input_files": [],
                 "assertions": [], "should_trigger": True}
                for i in (0, 1)
            ],
        }, ensure_ascii=False), encoding="utf-8")
        tpl = f'"{sys.executable}" "{writer}" {{prompt}}'
        rc, out, _err = run_script(root, sd / "scripts" / "optimize_description.py", str(sd),
                                   "--eval-set", str(evals), "--runner", "cmd", "--cmd", tpl,
                                   "--detect", "SENTINEL-TRIGGER", "--cwd", str(base),
                                   "--isolate-cwd", "--trials", "1")
        leftovers = sorted(p.name for p in base.iterdir()) if base.is_dir() else ["<none>"]
    try:
        mode_ok = json.loads(out).get("mode") == "agent:cmd"
    except Exception:  # noqa: BLE001
        mode_ok = False
    ok = rc == 0 and mode_ok and not leftovers
    return ok, f"rc={rc} mode_ok={mode_ok} 基目录残留={leftovers}"


@check("req0063-streaming-stop")
def req0063_streaming_stop(root: Path, skill: str) -> tuple[bool, str]:
    """命中触发标记即结束会话（不等进程跑完），避免超时误判。"""
    import time as _time

    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-r63-") as tmp:
        marker = Path(tmp) / "slow_marker.py"
        marker.write_text("import time\nprint('SENTINEL-TRIGGER', flush=True)\ntime.sleep(60)\n",
                          encoding="utf-8")
        tpl = f'"{sys.executable}" "{marker}" {{prompt}}'
        t0 = _time.monotonic()
        rc, out, _err = run_script(root, sd / "scripts" / "agent_runner.py",
                                   "--runner", "cmd", "--cmd", tpl,
                                   "--detect", "SENTINEL-TRIGGER", "--prompt", "x", "--timeout", "90")
        elapsed = _time.monotonic() - t0
    ok = rc == 0 and '"triggered": true' in out and elapsed < 30
    return ok, f"rc={rc} 用时={elapsed:.1f}s"


@check("req0060-report-summary")
def req0060_report_summary(root: Path, skill: str) -> tuple[bool, str]:
    """报告可见摘要必须含「候选 N / 通过 M / 被证伪 K」淘汰数。"""
    import render_report as rr

    template = read_text(skill_dir(root, skill) / "assets" / "report-template.html")
    data = {
        "skill_name": "x", "iteration": 1, "generated_at": "t",
        "benchmark": None, "evals": [],
        "findings": {
            "verdict": "可合入",
            "summary": {"candidates": 7, "passed": 5, "falsified": 2},
            "findings": [{"axis": "行为", "priority": "P1", "location": "x:1",
                          "problem": "问题", "plain": "白话", "suggestion": "建议"}],
        },
    }
    served = re.sub(r"<script>.*?</script>", "",
                    rr.build_html(data, template, "/triage?t=TOKEN"), flags=re.S)
    need = ["候选 7", "通过 5", "被证伪 2"]
    missing = [n for n in need if n not in served]
    return (not missing), f"缺={missing}"


@check("validate-rejects-bad")
def validate_rejects_bad(root: Path, skill: str) -> tuple[bool, str]:
    """validate_skill.py 对含多余字段的技能 → 非 0。"""
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-vrb-") as tmp:
        d = Path(tmp) / "bad"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\nname: bad\ndescription: x\nbogus_field: 坏\n---\n\n# bad\n", encoding="utf-8")
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


@check("converged-mechanical")
def converged_mechanical(root: Path, skill: str) -> tuple[bool, str]:
    """converged 由 run_checks 机械算出（行为验证）：达标 → true、带债 → false。"""
    script = skill_dir(root, skill) / "scripts" / "run_checks.py"
    base = ("---\nid: REQ-0001\ntitle: x\nskill: demo\nstatus: done\niteration: 1\n"
            "created: 2026-01-01\nupdated: 2026-01-01\nblocked_by: []\n---\n\n"
            "# REQ-0001 x\n\n## 验收标准\n\n")
    with tempfile.TemporaryDirectory(prefix="shy-cm-") as tmp:
        t = Path(tmp)
        d = t / "docs" / "demo" / "requirements"
        d.mkdir(parents=True)
        (d / "REQ-0001.md").write_text(base + "- [ ] 稳定项（语义）\n", encoding="utf-8")
        rc_ok, out_ok, _ = run_script(t, script, "--root", str(t), "--skill", "demo")
        (d / "REQ-0001.md").write_text(base + "- [ ] 未分类项\n", encoding="utf-8")
        rc_debt, out_debt, _ = run_script(t, script, "--root", str(t), "--skill", "demo")
    good = rc_ok == 0 and "converged: true" in out_ok
    bad = rc_debt != 0 and "converged: false" in out_debt
    return (good and bad), f"达标 rc={rc_ok}/true={good}；带债 rc={rc_debt}/false={bad}"


@check("req0069-effectiveness-set")
def req0069_effectiveness_set(root: Path, skill: str) -> tuple[bool, str]:
    """用例集：≥3 条任务式用例、每条 ≥1 断言，且 prompt 不点名技能。"""
    p = skill_dir(root, skill) / "evals" / "effectiveness.json"
    if not p.is_file():
        return False, "evals/effectiveness.json 不存在"
    try:
        data = json.loads(read_text(p))
    except Exception as exc:  # noqa: BLE001 - 报错即可
        return False, f"解析失败：{exc}"
    name = data.get("skill_name", "")
    cases = data.get("cases") or []
    bad = [c.get("eval_name", "?") for c in cases
           if not c.get("prompt") or not c.get("assertions")]
    named = [c.get("eval_name", "?") for c in cases if name and name in (c.get("prompt") or "")]
    ok = len(cases) >= 3 and not bad and not named
    return ok, f"用例={len(cases)} 缺 prompt/断言={bad} prompt 点名技能={named}"


@check("req0069-effectiveness-harness")
def req0069_effectiveness_harness(root: Path, skill: str) -> tuple[bool, str]:
    """运行器端到端（桩命令）：布局 + 污染字段 + 技能恢复 + 隔离根清理。"""
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-r69-") as tmp:
        t = Path(tmp)
        stub = t / "stub.py"
        stub.write_text(
            "import pathlib\n"
            "print('-> Read C:/outside/foreign.md')\n"
            "print('Skill \"other-skill\"')\n"
            "pathlib.Path('artifact.txt').write_text('x', encoding='utf-8')\n"
            "print('ANSWER-OK')\n",
            encoding="utf-8",
        )
        cases = t / "cases.json"
        cases.write_text(json.dumps({
            "skill_name": "demo",
            "cases": [{"eval_id": 0, "eval_name": "stub", "prompt": "x",
                       "assertions": [{"name": "a", "check": "c"}]}],
        }, ensure_ascii=False), encoding="utf-8")
        tpl = f'"{sys.executable}" "{stub}" {{prompt}}'
        skills = t / "skills"
        for n in ("demo", "other"):
            (skills / n).mkdir(parents=True)
            (skills / n / "SKILL.md").write_text("x", encoding="utf-8")
        ws1 = t / "ws1"
        rc, out, err = run_script(root, sd / "scripts" / "run_effectiveness.py",
                                  "--arm", "baseline", "--cases", str(cases),
                                  "--ws", str(ws1), "--trials", "1", "--workers", "1",
                                  "--cmd", tpl, "--detect-skill", "demo",
                                  "--cwd-base", str(t / "root"), "--keep",
                                  "--skills-dir", str(skills),
                                  "--disable-skills", "demo,other")
        run_dir = ws1 / "eval-0" / "baseline_0"
        response = (run_dir / "outputs" / "response.txt")
        timing_p = run_dir / "timing.json"
        timing = json.loads(timing_p.read_text(encoding="utf-8")) if timing_p.is_file() else {}
        contam = timing.get("contamination") or {}
        restored = all((skills / n / "SKILL.md").is_file() for n in ("demo", "other"))
        layout_ok = (rc == 0 and response.is_file() and "ANSWER-OK" in read_text(response)
                     and (run_dir / "outputs" / "workspace" / "artifact.txt").is_file())
        contam_ok = (timing.get("loaded_skills") == ["other-skill"]
                     and contam.get("other_skills_loaded") == ["other-skill"]
                     and any("foreign.md" in p for p in contam.get("foreign_reads") or [])
                     and contam.get("target_loaded") is False)
        # 第二跑：缺省隔离根 → 跑完应自动删除
        ws2 = t / "ws2"
        rc2, out2, _err2 = run_script(root, sd / "scripts" / "run_effectiveness.py",
                                      "--arm", "with_skill", "--cases", str(cases),
                                      "--ws", str(ws2), "--trials", "1", "--workers", "1",
                                      "--cmd", tpl, "--detect-skill", "demo")
        try:
            info2 = json.loads(out2)
        except Exception:  # noqa: BLE001
            info2 = {}
        root2 = info2.get("cwd_root")
        cleaned = bool(root2) and info2.get("cwd_root_kept") is False and not Path(root2).exists()
    ok = layout_ok and contam_ok and restored and rc2 == 0 and cleaned
    return ok, (f"rc={rc} 布局={layout_ok} 污染字段={contam_ok} 技能恢复={restored} "
                f"隔离根清理={cleaned}")


def _make_fingerprint_skill(base: Path, description: str, body: str) -> Path:
    """造一个最小技能目录，覆盖有效性轴的四类来源。"""
    d = base / "demo-skill"
    for sub in ("references", "scripts", "assets", "evals"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(
        f"---\nname: demo-skill\ndescription: {description}\n---\n\n{body}\n", encoding="utf-8")
    (d / "references" / "r.md").write_text("ref-a", encoding="utf-8")
    (d / "scripts" / "s.py").write_text("print('a')\n", encoding="utf-8")
    (d / "assets" / "a.html").write_text("<p>a</p>", encoding="utf-8")
    (d / "evals" / "effectiveness.json").write_text('{"cases":[]}', encoding="utf-8")
    return d


@check("req0071-fingerprint")
def req0071_fingerprint(root: Path, skill: str) -> tuple[bool, str]:
    """指纹分轴 + 确定性：触发只看 description；有效性看技能文件与 effectiveness.json。"""
    from skill_utils import effectiveness_fingerprint, trigger_fingerprint

    with tempfile.TemporaryDirectory(prefix="shy-r71fp-") as tmp:
        base = Path(tmp)
        d = _make_fingerprint_skill(base, "描述A", "正文A")
        t1, e1 = trigger_fingerprint(d), effectiveness_fingerprint(d)
        t1b, e1b = trigger_fingerprint(d), effectiveness_fingerprint(d)  # 确定性
        _make_fingerprint_skill(base, "描述A", "正文B")                    # 只改正文
        t2, e2 = trigger_fingerprint(d), effectiveness_fingerprint(d)
        _make_fingerprint_skill(base, "描述B", "正文B")                    # 只改 description
        t3 = trigger_fingerprint(d)
        (d / "references" / "r.md").write_text("ref-b", encoding="utf-8")  # 只改 references
        e3 = effectiveness_fingerprint(d)
        (d / "evals" / "effectiveness.json").write_text('{"cases":[1]}', encoding="utf-8")  # 只改评测集
        e4 = effectiveness_fingerprint(d)

    deterministic = t1 == t1b and e1 == e1b
    axis_split = t1 == t2 and e1 != e2          # 正文不动触发、动有效性
    desc_axis = t3 != t1                        # description 动触发
    ref_axis = e3 != e2                         # references 动有效性
    eval_axis = e4 != e3                        # effectiveness.json 动有效性
    independent = t1 != e1                      # 两轴取值不同
    ok = deterministic and axis_split and desc_axis and ref_axis and eval_axis and independent
    return ok, (f"确定性={deterministic} 正文分轴={axis_split} description→触发={desc_axis} "
                f"ref→有效性={ref_axis} eval→有效性={eval_axis} 两轴独立={independent}")


@check("req0071-evidence-meta")
def req0071_evidence_meta(root: Path, skill: str) -> tuple[bool, str]:
    """eval 跑完在 iteration-N 写 evidence.json（指纹 + 模型 ID + 时间），指纹匹配当前技能。"""
    from skill_utils import effectiveness_fingerprint

    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-r71ev-") as tmp:
        t = Path(tmp)
        skill_d = t / "demo-skill"
        (skill_d / "evals").mkdir(parents=True)
        (skill_d / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: 演示；当需要演示时使用。\n---\n\n# Demo\n",
            encoding="utf-8")
        (skill_d / "evals" / "effectiveness.json").write_text(
            '{"skill_name":"demo-skill","cases":[]}', encoding="utf-8")
        stub = t / "stub.py"
        stub.write_text("print('ANSWER-OK')\n", encoding="utf-8")
        cases = t / "cases.json"
        cases.write_text(json.dumps({
            "skill_name": "demo-skill",
            "cases": [{"eval_id": 0, "eval_name": "s", "prompt": "x",
                       "assertions": [{"name": "a", "check": "c"}]}],
        }, ensure_ascii=False), encoding="utf-8")
        tpl = f'"{sys.executable}" "{stub}" {{prompt}}'
        ws = t / "ws"
        rc, _out, err = run_script(root, sd / "scripts" / "run_effectiveness.py",
                                   "--arm", "with_skill", "--cases", str(cases), "--ws", str(ws),
                                   "--trials", "1", "--workers", "1", "--cmd", tpl,
                                   "--detect-skill", "demo-skill", "--skill-dir", str(skill_d),
                                   "--model", "test/model")
        ev = ws / "evidence.json"
        exists = ev.is_file()
        try:
            data = json.loads(ev.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        eff = (data.get("axes") or {}).get("effectiveness") or {}
        fp = eff.get("fingerprint")
        model_ok = eff.get("model") == "test/model" and data.get("model") == "test/model"
        ts = eff.get("updated_at") or data.get("generated_at")
        matches = bool(fp) and fp == effectiveness_fingerprint(skill_d)

    ok = rc == 0 and exists and model_ok and bool(ts) and matches
    return ok, (f"rc={rc} evidence.json={exists} 指纹={bool(fp)} 模型={model_ok} "
                f"时间={bool(ts)} 指纹匹配={matches} err={err[:80]}")


@check("req0071-eval-command")
def req0071_eval_command(root: Path, skill: str) -> tuple[bool, str]:
    """commands/shy-eval.md 存在：加载技能 + $ARGUMENTS + 触发/有效性/两者参数。"""
    p = skill_dir(root, skill) / "commands" / "shy-eval.md"
    if not p.is_file():
        return False, "commands/shy-eval.md 不存在"
    text = read_text(p)
    need = ["$ARGUMENTS", "触发", "有效性", "两者", "references/running-evals.md", "skill"]
    missing = [n for n in need if n not in text]
    return (not missing), f"缺={missing}"


@check("req0071-glossary-boundary")
def req0071_glossary_boundary(root: Path, skill: str) -> tuple[bool, str]:
    """glossary 含「评测（eval）」「复审（review）」两条定义 + _避免_ + 降级词。"""
    p = skill_dir(root, skill) / "references" / "glossary.md"
    if not p.is_file():
        return False, "references/glossary.md 不存在"
    text = read_text(p)
    need = ["评测（eval）", "复审（review）", "_避免_", "（静态）", "过期证据"]
    missing = [n for n in need if n not in text]
    ev = bool(re.search(r"\*\*评测（eval）\*\*.*?_避免_", text, re.S))
    rv = bool(re.search(r"\*\*复审（review）\*\*.*?_避免_", text, re.S))
    return (not missing and ev and rv), f"缺={missing} 评测含避免={ev} 复审含避免={rv}"


@check("req0071-no-auto-eval")
def req0071_no_auto_eval(root: Path, skill: str) -> tuple[bool, str]:
    """lifecycle 斜杠快捷表含 /shy-eval，且无「里程碑 / 收敛点」作为 eval 自动触发。"""
    p = skill_dir(root, skill) / "references" / "lifecycle.md"
    if not p.is_file():
        return False, "references/lifecycle.md 不存在"
    text = read_text(p)
    has_cmd = "/shy-eval" in text
    auto = [w for w in ("里程碑", "收敛点") if w in text]
    return (has_cmd and not auto), f"含/shy-eval={has_cmd} 自动触发词残留={auto}"


@check("req0071-review-completion")
def req0071_review_completion(root: Path, skill: str) -> tuple[bool, str]:
    """reviewing-skills 的 Step 1/2/3 完成判据不再硬要触发率 / delta 证据，改为静态降级。"""
    p = skill_dir(root, skill) / "references" / "reviewing-skills.md"
    if not p.is_file():
        return False, "references/reviewing-skills.md 不存在"
    text = read_text(p)
    has_degrade = "（静态）" in text and "过期证据" in text
    old = [
        "正例与负例的触发率都过阈值（默认 0.5）",
        "整技能对照有 delta 证据；每条指令都过了",
        "全部 `（行为）` 项有 with/baseline delta 证据",
    ]
    still = [s for s in old if s in text]
    return (has_degrade and not still), f"降级词={has_degrade} 旧硬要求残留={still}"


def _write_req(
    req_dir: Path, rid: str, title: str, kind: str, status: str,
    background: str = "这是背景首段。", blocked_by: str = "[]",
) -> None:
    """在 req_dir 写一个最小 REQ 文件（render_reqs 契约用例用）。"""
    req_dir.mkdir(parents=True, exist_ok=True)
    skill = req_dir.parent.name
    (req_dir / f"{rid}.md").write_text(
        f"---\nid: {rid}\ntitle: {title}\nskill: {skill}\nstatus: {status}\nkind: {kind}\n"
        f"iteration: 1\ncreated: 2026-01-01\nupdated: 2026-02-02\nblocked_by: {blocked_by}\n---\n\n"
        f"# {rid} {title}\n\n## 问题与目标\n\n{background}\n",
        encoding="utf-8",
    )


def _render_reqs_sample(root: Path, skill: str) -> tuple[int, bool, str, str]:
    """造一个技能的 REQ，跑 render_reqs.py（--skill，--no-open），返回 (rc, html_ok, html, err)。"""
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-r74rr-") as tmp:
        t = Path(tmp)
        _write_req(t / "docs" / "demo" / "requirements", "REQ-0001",
                   "演示需求白话一句", "feature", "ready", "这是背景首段。")
        rc, _out, err = run_script(root, sd / "scripts" / "render_reqs.py",
                                   "--root", str(t), "--skill", "demo", "--no-open")
        html_path = t / "reports" / "demo-reqs.html"
        html_ok = html_path.is_file()
        html = html_path.read_text(encoding="utf-8") if html_ok else ""
    return rc, html_ok, html, err


@check("req0072-reqs-command")
def req0072_reqs_command(root: Path, skill: str) -> tuple[bool, str]:
    """commands/shy-reqs.md 存在、shy-next.md 删除；含加载技能 + --skill / --kind。"""
    sd = skill_dir(root, skill)
    new = sd / "commands" / "shy-reqs.md"
    old = sd / "commands" / "shy-next.md"
    if not new.is_file():
        return False, "commands/shy-reqs.md 不存在"
    if old.exists():
        return False, "commands/shy-next.md 仍存在"
    text = read_text(new)
    need = ["skill", "shy-skill-suite", "$ARGUMENTS", "--skill", "--kind"]
    missing = [n for n in need if n not in text]
    return (not missing), f"缺={missing}"


@check("req0072-overview-view")
def req0072_overview_view(root: Path, skill: str) -> tuple[bool, str]:
    """--view overview 出人读摘要（计数 + frontier + 按技能分组），--help 含该参数。"""
    sd = skill_dir(root, skill)
    rc, out, err = run_script(root, sd / "scripts" / "track_requirements.py",
                              "--root", ".", "--view", "overview")
    if rc != 0:
        return False, f"rc={rc} err={err[:160]}"
    need = ["frontier", "kind", "status"]
    missing = [n for n in need if n not in out]
    not_json = not out.lstrip().startswith("{")
    has_skill = skill in out
    rc2, out2, _e2 = run_script(root, sd / "scripts" / "track_requirements.py", "--help")
    help_ok = rc2 == 0 and "--view" in out2
    ok = not missing and not_json and has_skill and help_ok
    return ok, f"缺={missing} 非JSON={not_json} 含技能={has_skill} help含--view={help_ok}"


@check("req0072-render-reqs")
def req0072_render_reqs(root: Path, skill: str) -> tuple[bool, str]:
    """render_reqs.py 存在、--help 完整；产出自包含 HTML（无外部资源）。"""
    sd = skill_dir(root, skill)
    script = sd / "scripts" / "render_reqs.py"
    if not script.is_file():
        return False, "render_reqs.py 不存在"
    rc, out, _err = run_script(root, script, "--help")
    help_ok = rc == 0 and all(
        k in out for k in ("示例", "退出码", "--root", "--out", "--skill", "--kind", "--no-open"))
    rc2, html_ok, html, err = _render_reqs_sample(root, skill)
    external = [t for t in ("http://", "https://", "<link", "<script", "src=") if t in html]
    ok = help_ok and rc2 == 0 and html_ok and not external
    return ok, f"help={help_ok} rc={rc2} html={html_ok} 外部资源={external} err={err[:80]}"


@check("req0072-html-structure")
def req0072_html_structure(root: Path, skill: str) -> tuple[bool, str]:
    """HTML 含 kind / status 分组与 <details> 折叠（REQ-0074 起为新的三级结构）。"""
    rc, html_ok, html, err = _render_reqs_sample(root, skill)
    need = ["REQ 报告", "<details", "新增功能", "待开工", "REQ-0001"]
    missing = [n for n in need if n not in html]
    ok = rc == 0 and html_ok and not missing
    return ok, f"rc={rc} html={html_ok} 缺={missing} err={err[:80]}"


@check("req0072-gitignore")
def req0072_gitignore(root: Path, skill: str) -> tuple[bool, str]:
    """仓库 .gitignore 忽略 reports/。"""
    gi = root / ".gitignore"
    if not gi.is_file():
        return False, ".gitignore 不存在"
    hit = any(ln.strip().rstrip("/") == "reports" for ln in read_text(gi).splitlines())
    return hit, f"忽略 reports/={hit}"


@check("req0072-skill-routing")
def req0072_skill_routing(root: Path, skill: str) -> tuple[bool, str]:
    """lifecycle.md 斜杠快捷表与 SKILL.md 资源区含 /shy-reqs、不再有 shy-next。"""
    sd = skill_dir(root, skill)
    life = read_text(sd / "references" / "lifecycle.md")
    skillmd = read_text(sd / "SKILL.md")
    checks = {
        "lifecycle含/shy-reqs": "/shy-reqs" in life,
        "lifecycle无shy-next": "shy-next" not in life,
        "SKILL含shy-reqs": "shy-reqs" in skillmd,
        "SKILL无shy-next": "shy-next" not in skillmd,
    }
    failed = [k for k, v in checks.items() if not v]
    return (not failed), f"未过={failed}"


@check("req0074-single-skill")
def req0074_single_skill(root: Path, skill: str) -> tuple[bool, str]:
    """`--skill` 必填（缺 → 非 0）；报告只含该技能的 REQ，不含别的技能。"""
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-r74s-") as tmp:
        t = Path(tmp)
        _write_req(t / "docs" / "demo" / "requirements", "REQ-0001", "演示白话", "feature", "ready")
        _write_req(t / "docs" / "other" / "requirements", "REQ-0002", "别家白话", "fix", "done")
        rc_missing, _o, _e = run_script(root, sd / "scripts" / "render_reqs.py",
                                        "--root", str(t), "--no-open")
        rc, _o2, err = run_script(root, sd / "scripts" / "render_reqs.py",
                                  "--root", str(t), "--skill", "demo", "--no-open")
        out = t / "reports" / "demo-reqs.html"
        html = out.read_text(encoding="utf-8") if out.is_file() else ""
    only = "REQ-0001" in html and "REQ-0002" not in html and "别家白话" not in html
    ok = rc_missing != 0 and rc == 0 and only
    return ok, f"缺--skill rc={rc_missing}；单技能 rc={rc}；只含本技能={only} err={err[:80]}"


@check("req0074-structure")
def req0074_structure(root: Path, skill: str) -> tuple[bool, str]:
    """三级结构 kind（白话+计数，默认展开）→ status（白话+计数）→ REQ 行；详情含元数据与背景首段。"""
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-r74st-") as tmp:
        t = Path(tmp)
        d = t / "docs" / "demo" / "requirements"
        _write_req(d, "REQ-0001", "第一句白话", "feature", "done", "这是背景第一段。")
        _write_req(d, "REQ-0002", "第二句白话", "fix", "ready", "另一段背景。")
        _write_req(d, "REQ-0003", "第三句白话", "docs", "ready", "文档背景。")
        rc, _o, err = run_script(root, sd / "scripts" / "render_reqs.py",
                                 "--root", str(t), "--skill", "demo", "--no-open")
        out = t / "reports" / "demo-reqs.html"
        html = out.read_text(encoding="utf-8") if out.is_file() else ""
    need = ["新增功能", "修复缺陷", "文档", "已完成", "待开工",
            "REQ-0001", "第一句白话", "这是背景第一段",
            "类型", "状态", "生成日期", "更新日期", "轮次", "依赖", "<details"]
    missing = [n for n in need if n not in html]
    order_ok = html.find("新增功能") < html.find("修复缺陷") < html.find("文档")
    expanded = "<details open" in html
    ok = rc == 0 and not missing and order_ok and expanded
    return ok, f"rc={rc} 缺={missing} kind顺序={order_ok} kind默认展开={expanded} err={err[:80]}"


@check("req0074-no-capability-view")
def req0074_no_capability_view(root: Path, skill: str) -> tuple[bool, str]:
    """不再有能力视图：源码不读预生成视图、不含「现在能做什么 / 计划做什么」；输出亦无。"""
    sd = skill_dir(root, skill)
    src = read_text(sd / "scripts" / "render_reqs.py")
    src_hits = [t for t in ("reqs-view", "现在能做什么", "计划做什么", "capability") if t in src]
    rc, html_ok, html, _err = _render_reqs_sample(root, skill)
    html_hits = [t for t in ("现在能做什么", "计划做什么") if t in html]
    ok = not src_hits and rc == 0 and html_ok and not html_hits
    return ok, f"源码命中={src_hits} 输出命中={html_hits}"


@check("req0074-report-file")
def req0074_report_file(root: Path, skill: str) -> tuple[bool, str]:
    """固定输出 reports/<skill>-reqs.html：单文件自包含、无外部资源、再次统计原地覆盖。"""
    sd = skill_dir(root, skill)
    with tempfile.TemporaryDirectory(prefix="shy-r74f-") as tmp:
        t = Path(tmp)
        d = t / "docs" / "demo" / "requirements"
        _write_req(d, "REQ-0001", "旧标题白话", "feature", "ready")
        rc, _o, err = run_script(root, sd / "scripts" / "render_reqs.py",
                                 "--root", str(t), "--skill", "demo", "--no-open")
        out = t / "reports" / "demo-reqs.html"
        _write_req(d, "REQ-0001", "改过的标题白话", "feature", "ready")
        rc2, _o2, _e2 = run_script(root, sd / "scripts" / "render_reqs.py",
                                   "--root", str(t), "--skill", "demo", "--no-open")
        second = out.read_text(encoding="utf-8") if out.is_file() else ""
        html_files = sorted(p.name for p in (t / "reports").glob("*.html"))
    external = [x for x in ("http://", "https://", "<link", "<script", "src=") if x in second]
    overwritten = "改过的标题白话" in second and "旧标题白话" not in second
    ok = (rc == 0 and rc2 == 0 and overwritten and not external
          and html_files == ["demo-reqs.html"])
    return ok, f"rc={rc}/{rc2} 原地覆盖={overwritten} 外部资源={external} 产物={html_files} err={err[:60]}"


@check("req0074-title-convention")
def req0074_title_convention(root: Path, skill: str) -> tuple[bool, str]:
    """writing-requirements.md 的 title 规范为「面向人的白话一句话」。"""
    p = skill_dir(root, skill) / "references" / "writing-requirements.md"
    if not p.is_file():
        return False, "references/writing-requirements.md 不存在"
    text = read_text(p)
    has = "面向人的白话一句话" in text
    uses = text.count("白话一句话") >= 2
    return (has and uses), f"含规范={has} 多处引用={uses}"


@check("req0073-apply-removed")
def req0073_apply_removed(root: Path, skill: str) -> tuple[bool, str]:
    """commands/shy-apply.md 不存在；lifecycle.md 不再引用 /shy-apply。"""
    sd = skill_dir(root, skill)
    gone = not (sd / "commands" / "shy-apply.md").exists()
    life = read_text(sd / "references" / "lifecycle.md")
    no_ref = "shy-apply" not in life
    return (gone and no_ref), f"命令删除={gone} lifecycle无引用={no_ref}"


@check("req0073-gate-preserved")
def req0073_gate_preserved(root: Path, skill: str) -> tuple[bool, str]:
    """lifecycle.md 保留「用户确认后按分拣单次实施、不自动再审」的闸门语义。"""
    life = read_text(skill_dir(root, skill) / "references" / "lifecycle.md")
    need = ["用户确认", "实施一次", "不自动再审"]
    missing = [n for n in need if n not in life]
    return (not missing), f"缺={missing}"


@check("req0073-review-closing")
def req0073_review_closing(root: Path, skill: str) -> tuple[bool, str]:
    """commands/shy-review.md 收尾为「等用户确认分拣后实施」，不指向 /shy-apply。"""
    p = skill_dir(root, skill) / "commands" / "shy-review.md"
    if not p.is_file():
        return False, "commands/shy-review.md 不存在"
    text = read_text(p)
    no_apply = "shy-apply" not in text
    has_confirm = ("确认" in text) and ("实施" in text)
    return (no_apply and has_confirm), f"无shy-apply={no_apply} 含确认/实施={has_confirm}"


@check("req0073-skill-commands")
def req0073_skill_commands(root: Path, skill: str) -> tuple[bool, str]:
    """SKILL.md 资源区命令清单不含 shy-apply。"""
    text = read_text(skill_dir(root, skill) / "SKILL.md")
    hit = "shy-apply" in text
    return (not hit), f"SKILL.md 含 shy-apply={hit}"


@check("req0075-triage-scope")
def req0075_triage_scope(root: Path, skill: str) -> tuple[bool, str]:
    """shy-review 不再无条件「不自动修改」；限定为技能行为 / findings，台账机械项当轮结清。"""
    p = skill_dir(root, skill) / "commands" / "shy-review.md"
    if not p.is_file():
        return False, "commands/shy-review.md 不存在"
    text = read_text(p)
    need = ["不自动修改", "技能行为", "findings", "台账", "当轮结清"]
    missing = [n for n in need if n not in text]
    return (not missing), f"缺={missing}"


@check("req0075-ledger-owner")
def req0075_ledger_owner(root: Path, skill: str) -> tuple[bool, str]:
    """reviewing-skills Step 8：主 agent 当轮结清，且含机械可修 / 需决策边界。"""
    p = skill_dir(root, skill) / "references" / "reviewing-skills.md"
    if not p.is_file():
        return False, "references/reviewing-skills.md 不存在"
    text = read_text(p)
    need = ["主 agent", "当轮", "机械可修", "需决策"]
    missing = [n for n in need if n not in text]
    return (not missing), f"缺={missing}"


@check("req0075-subagents-boundary")
def req0075_subagents_boundary(root: Path, skill: str) -> tuple[bool, str]:
    """subagents 副作用禁令：台账由主 agent 结清、子代理只发现（禁写不变）。"""
    p = skill_dir(root, skill) / "references" / "subagents.md"
    if not p.is_file():
        return False, "references/subagents.md 不存在"
    text = read_text(p)
    need = ["台账由主 agent 结清", "子代理只发现", "禁写不变"]
    missing = [n for n in need if n not in text]
    return (not missing), f"缺={missing}"


@check("req0075-lifecycle")
def req0075_lifecycle(root: Path, skill: str) -> tuple[bool, str]:
    """lifecycle 阶段 3 含「台账机械项当轮结清」，且「不自动再审」不变。"""
    p = skill_dir(root, skill) / "references" / "lifecycle.md"
    if not p.is_file():
        return False, "references/lifecycle.md 不存在"
    text = read_text(p)
    has_settle = "台账机械项当轮结清" in text
    has_gate = "不自动再审" in text
    return (has_settle and has_gate), f"台账机械项当轮结清={has_settle} 不自动再审={has_gate}"


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
        crits = criteria(path)
        if not skip_exec and not crits:
            # 已实现 / 已完成的 REQ 必须有验收标准——零证据不得过门。
            failed += 1
            errors.append({"req": rid, "error": "done/in-progress REQ 无验收标准"})
            rows.append({"req": rid, "check": "(空验收标准)", "passed": False,
                         "evidence": "done/in-progress REQ 必须有验收标准"})
        for desc in crits:
            tag = CHECK_TAG_RE.search(desc)
            if not tag:
                # 取行内**最后一个**类别标记：一行提到多个词时，以行尾标注为准。
                marks: list[tuple[int, str]] = []
                for kind, pattern in (("behavior", BEHAVIOR_RE),
                                      ("semantic", SEMANTIC_RE),
                                      ("episode", EPISODE_RE)):
                    marks.extend((m.start(), kind) for m in pattern.finditer(desc))
                if marks:
                    if skip_exec:
                        # 未实现 / 延后 / 不做的 REQ：标签是未来契约，不计入本轮工作集。
                        skipped += 1
                        continue
                    kind = max(marks)[1]
                    if kind == "behavior":
                        behavior += 1
                    elif kind == "semantic":
                        semantic += 1
                    else:
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
        "hint": "untagged>0 表示有验收标准没标四类之一（check: / （行为） / （语义） / （episode））——未分类项即**迁移债**（不设默认、挂 `（未定）`；含未实现 / 延后 / 不做 REQ 的未标行——分类债全局计）；episode 为一次性事实、不进 Gate；skipped 为未实现 / 延后 / 不做的 REQ 跳过的 check 与标签行数",
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

    # V6：没有 REQ = 不适用，不是"绿"（技能单独部署 / 空需求目录时不得假绿）。
    if not discover(root, args.skill):
        result["status"] = "n/a"
    # V1：带迁移债不得判绿（债门）。`state.json` 缺失按目标 0；全仓扫描时聚合各技能目标——
    # 任何路径都不得因缺文件 / 缺 `--skill` 而跳过债门。
    def _debt_target(skill_name: str) -> int:
        st = root / "docs" / skill_name / "state.json"
        if not st.is_file():
            return 0
        try:
            return int((json.loads(read_text(st)).get("debt_targets") or {})
                       .get("unclassified_criteria", 0))
        except Exception:  # noqa: BLE001
            return 0

    if args.skill:
        debt_target = _debt_target(args.skill)
    else:
        debt_target = sum(_debt_target(p.parent.name)
                          for p in root.glob("docs/*/requirements"))
    if result["untagged"] > debt_target and result["status"] == "ok":
        result["status"] = "debt"
        result["debt_target"] = debt_target
    # converged = 机械判据（非 agent 自证）：无失败 / 无未注册 check / 债达标 ⇔ status == "ok"
    result["converged"] = (result["status"] == "ok")

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    for row in result["checks"]:
        mark = "PASS" if row["passed"] else "FAIL"
        print(f"[{mark}] {row['req']} {row['check']}  {row['evidence']}")
    if result["status"] == "n/a":
        print("[n/a] 未发现任何 REQ（docs/<skill>/requirements 缺失或为空）——Gate 不适用，**不得当绿**")
    elif result["status"] == "debt":
        print(f"[debt] 未分类迁移债 {result['untagged']} > 目标 {result.get('debt_target')}——**未收敛，Gate 不判绿**")
    if cc is not None and fc is not None:
        print(f"问题: open={cc[0] + fc[0]}（台账 {cc[0]} + fix 工单 {fc[0]}） "
              f"fixed={cc[1] + fc[1]}（台账 {cc[1]} + fix 工单 {fc[1]}）")
    print(f"converged: {str(result['converged']).lower()}")
    e = result["executable"]
    cleanup_note = ""
    if result.get("cleanup_open") is not None:
        cleanup_note = f"；台账 open {result['cleanup_open']}"
    print(f"\ncheck: {e['total']} 条：{e['passed']} 通过 / {e['failed']} 失败；"
          f"（行为）{result['behavior']}；（语义）{result['semantic']}；"
          f"（episode）{result['episode']}；"
          f"未分类(迁移债) {result['untagged']}；跳过（未实现 / 延后 / 不做）{result['skipped']}"
          f"{cleanup_note}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
