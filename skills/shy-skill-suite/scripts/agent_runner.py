#!/usr/bin/env python3
"""把一条 prompt 跑过一个 agent 客户端，并判断目标技能是否被触发。

这是"客户端无关"的适配层：脚本本身不知道 TeleAgent / opencode 的细节，
只执行一条命令模板（含 ``{prompt}`` 占位符），再在输出里检测技能是否被激活。

支持的 runner:
    heuristic  不调用 agent，返回 triggered=None（调用方改用离线启发式）
    opencode   默认命令 ``opencode run "{prompt}"``
    teleagent  命令取自 ``--cmd`` 或环境变量 ``TELEAGENT_RUN_CMD``
    cmd        完全自定义命令模板（必须含 ``{prompt}``）

用法:
    python agent_runner.py --runner opencode --detect shy-skill-suite --prompt "帮我写个技能需求"
    python agent_runner.py --runner cmd --cmd "echo {prompt}" --detect hello --prompt "hello world"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any

from skill_utils import force_utf8_stdio

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


def detect(output: str, pattern: str) -> bool:
    """在输出里检测触发标记；优先按正则，失败则退化为子串匹配。"""
    if not pattern:
        return False
    try:
        return re.search(pattern, output, re.IGNORECASE) is not None
    except re.error:
        return pattern.lower() in output.lower()


def run_prompt(
    prompt: str,
    runner: str = "heuristic",
    cmd: str | None = None,
    detect_pattern: str | None = None,
    cwd: str | None = None,
    timeout: int = 120,
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

    command = template.replace("{prompt}", prompt.replace('"', '\\"'))
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {
            "runner": runner,
            "triggered": False,
            "command": command,
            "returncode": None,
            "output": "",
            "error": f"timeout after {timeout}s",
        }

    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    pattern = detect_pattern or ""
    return {
        "runner": runner,
        "triggered": detect(output, pattern),
        "command": command,
        "returncode": proc.returncode,
        "output": output,
    }


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(description="Run a prompt through an agent and detect skill activation")
    parser.add_argument("--prompt", required=True, help="The user prompt to run")
    parser.add_argument("--runner", default="heuristic", choices=sorted(DEFAULT_COMMANDS), help="Agent client to use")
    parser.add_argument("--cmd", help="Command template containing {prompt} (overrides runner default)")
    parser.add_argument("--detect", help="Substring or regex marking skill activation (default: none)")
    parser.add_argument("--cwd", help="Working directory for the command")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds (default: 120)")
    args = parser.parse_args()

    result = run_prompt(
        prompt=args.prompt,
        runner=args.runner,
        cmd=args.cmd,
        detect_pattern=args.detect,
        cwd=args.cwd,
        timeout=args.timeout,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("triggered") is not False else 1


if __name__ == "__main__":
    sys.exit(main())
