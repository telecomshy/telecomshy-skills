#!/usr/bin/env python3
"""把一条 prompt 跑过一个 agent 客户端，并判断目标技能是否被触发。

这是"客户端无关"的适配层：脚本本身不知道 TeleAgent / opencode 的细节，
只执行一条命令模板（含 ``{prompt}`` 占位符），再在输出里检测技能是否被激活。

命令模板**按 argv 切分、不经 shell**（``shell=False``）：``{prompt}`` 始终作为
**参数内容**注入，模板里的 ``&`` / ``|`` / 反引号不会被 shell 解释。代价是模板
不能用 shell 语法（管道、重定向）；需要时请写一个包装脚本再让本脚本调用它。

支持的 runner:
    heuristic  不调用 agent，返回 triggered=None（调用方改用离线启发式）
    opencode   默认命令 ``opencode run "{prompt}"``；**真跑评测请用 --cmd 钉模型**
               （``opencode run --model <provider>/<id> "{prompt}"``）——默认模型
               解析不可控，换一次跑结果就变，结论不可复现。
    teleagent  命令取自 ``--cmd`` 或环境变量 ``TELEAGENT_RUN_CMD``
    cmd        完全自定义命令模板（必须含 ``{prompt}``）

用法:
    python agent_runner.py --runner opencode --detect shy-skill-suite --prompt "帮我写个技能需求"
    python agent_runner.py --runner cmd --cmd "my-cli --json {prompt}" --detect my-skill --prompt "帮我写个技能需求"
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shlex
import subprocess
import sys
import threading
import time
from typing import Any

from skill_utils import force_utf8_stdio, merge_evidence

DEFAULT_COMMANDS: dict[str, str] = {
    "opencode": 'opencode run "{prompt}"',
    "teleagent": "",
    "cmd": "",
    "heuristic": "",
}


def resolve_command(runner: str, cmd: str | None) -> str:
    """确定要执行的命令模板；teleagent 允许从环境变量取。"""
    if cmd:
        return cmd
    if runner == "teleagent":
        return os.environ.get("TELEAGENT_RUN_CMD", "")
    return DEFAULT_COMMANDS.get(runner, "")


def _strip_quotes(token: str) -> str:
    """去掉 token 最外层成对的引号（``posix=False`` 切分会保留引号）。"""
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    return token


def build_argv(template: str, prompt: str) -> list[str]:
    """把命令模板切成 argv，并把 prompt 作为参数注入（不经过 shell）。

    - ``shlex.split(template, posix=False)``：保留 Windows 路径里的反斜杠；
    - 逐 token 去掉最外层成对引号；
    - 把每个 token 内的 ``{prompt}`` 替换为 prompt——prompt 始终是参数内容，
      永不参与切分，因此不会被 shell / argv 解析。
    """
    argv: list[str] = []
    for token in shlex.split(template, posix=False):
        argv.append(_strip_quotes(token).replace("{prompt}", prompt))
    return argv


def detect(output: str, pattern: str, mode: str = "substring") -> bool:
    """在输出里检测触发标记。

    ``mode``:
      substring   子串 / 正则（兼容任意客户端；"提到名字"也算触发）
      skill-line  锚定技能加载行（``Skill "名"``）——防"只是提到名字"被算作触发
    """
    if not pattern:
        return False
    if mode == "skill-line":
        return re.search(r'Skill\s*"?\s*' + re.escape(pattern) + r'"?',
                         output, re.IGNORECASE) is not None
    try:
        return re.search(pattern, output, re.IGNORECASE) is not None
    except re.error:
        return pattern.lower() in output.lower()


def resolve_detect_mode(runner: str, cmd: str | None, mode: str) -> str:
    """``auto``：opencode 客户端用 skill-line（它打印加载行），其余用 substring。"""
    if mode != "auto":
        return mode
    if runner == "opencode" or "opencode" in (cmd or ""):
        return "skill-line"
    return "substring"


def run_prompt(
    prompt: str,
    runner: str = "heuristic",
    cmd: str | None = None,
    detect_pattern: str | None = None,
    cwd: str | None = None,
    timeout: int = 120,
    detect_mode: str = "auto",
) -> dict[str, Any]:
    """执行一条 prompt，返回 {runner, triggered, command, returncode, output}。

    ``triggered`` 为 True/False；runner 为 heuristic 或命令模板为空时返回 None。
    """
    if runner == "heuristic":
        return {
            "runner": runner,
            "triggered": None,
            "command": "",
            "returncode": None,
            "output": "",
        }

    template = resolve_command(runner, cmd)
    if not template:
        return {
            "runner": runner,
            "triggered": None,
            "command": "",
            "returncode": None,
            "output": "",
            "error": f"No command for runner '{runner}' (use --cmd or TELEAGENT_RUN_CMD)",
        }
    if "{prompt}" not in template:
        return {
            "runner": runner,
            "triggered": None,
            "command": template,
            "returncode": None,
            "output": "",
            "error": "命令模板必须包含 {prompt}，例如 --cmd \"my-cli {prompt}\"",
        }

    try:
        argv = build_argv(template, prompt)
    except ValueError as exc:
        return {
            "runner": runner,
            "triggered": None,
            "command": template,
            "returncode": None,
            "output": "",
            "error": f"invalid command template (unbalanced quotes?): {exc}",
        }
    command = subprocess.list2cmdline(argv)
    pattern = detect_pattern or ""
    mode = resolve_detect_mode(runner, cmd, detect_mode)
    try:
        proc = subprocess.Popen(
            argv,
            shell=False,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except OSError as exc:
        return {
            "runner": runner,
            "triggered": None,
            "command": command,
            "returncode": None,
            "output": "",
            "error": f"could not run command: {exc}",
        }

    # 流式检测：命中触发标记立即结束会话——正例常会继续干活到超时，等它跑完纯属浪费，
    # 且超时会把"已触发"误记成"未触发"。
    chunks: list[str] = []
    triggered = False
    timed_out = False
    line_queue: queue.Queue[str | None] = queue.Queue()

    def _pump() -> None:
        stream = proc.stdout
        try:
            if stream is not None:
                for line in stream:
                    line_queue.put(line)
        finally:
            line_queue.put(None)

    threading.Thread(target=_pump, daemon=True).start()
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            break
        try:
            item = line_queue.get(timeout=min(remaining, 0.5))
        except queue.Empty:
            continue
        if item is None:
            break
        chunks.append(item)
        if pattern and detect(item, pattern, mode):
            triggered = True
            break

    if triggered or timed_out:
        try:
            proc.terminate()
        except OSError:
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    output = "".join(chunks)
    if timed_out and not triggered:
        return {
            "runner": runner,
            "triggered": False,
            "command": command,
            "returncode": None,
            "output": output,
            "error": f"timeout after {timeout}s",
        }
    return {
        "runner": runner,
        "triggered": triggered,
        "command": command,
        "returncode": proc.returncode,
        "output": output,
    }


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="把一条 prompt 跑过 agent 客户端，并检测目标技能是否被触发。命令模板按 argv 切分、不经 shell。",
        epilog=(
            "示例:\n"
            '  python agent_runner.py --runner opencode --detect shy-skill-suite --prompt "帮我写个技能需求"\n'
            '  python agent_runner.py --runner cmd --cmd "my-cli --json {prompt}" --detect my-skill --prompt "帮我写个技能需求"\n'
            "\n"
            "退出码:\n"
            "  0  triggered 为 true，或 heuristic 未判定（triggered: null）\n"
            "  1  triggered 为 false，或运行错误 / 超时\n"
            "  2  参数错误\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--prompt", required=True, help="The user prompt to run")
    parser.add_argument("--runner", default="heuristic", choices=sorted(DEFAULT_COMMANDS), help="Agent client to use")
    parser.add_argument("--cmd", help="Command template containing {prompt} (overrides runner default)")
    parser.add_argument("--detect", help="Substring or regex marking skill activation (default: none)")
    parser.add_argument("--detect-mode", default="auto", choices=["auto", "substring", "skill-line"],
                        help='检测方式：auto（opencode→skill-line）/ substring / skill-line（锚定 Skill "名" 行）')
    parser.add_argument("--cwd", help="Working directory for the command")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds (default: 120)")
    parser.add_argument("--skill-dir", help="技能目录；与 --evidence-ws 同给时写触发轴证据")
    parser.add_argument("--evidence-ws", help="iteration 目录；写触发轴证据到 <dir>/evidence.json")
    parser.add_argument("--model", help="所用模型 ID（写触发轴证据时记录）")
    args = parser.parse_args()

    result = run_prompt(
        prompt=args.prompt,
        runner=args.runner,
        cmd=args.cmd,
        detect_pattern=args.detect,
        cwd=args.cwd,
        timeout=args.timeout,
        detect_mode=args.detect_mode,
    )
    if args.skill_dir and args.evidence_ws and not result.get("error"):
        result["evidence"] = str(merge_evidence(
            args.evidence_ws, args.skill_dir, ("trigger",), model=args.model))
    if result.get("error"):
        print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("triggered") is not False else 1


if __name__ == "__main__":
    sys.exit(main())
