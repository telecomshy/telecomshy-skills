#!/usr/bin/env python3
"""把一条 prompt 跑过一个 agent 客户端，并判断目标技能是否被触发。

这是"客户端无关"的适配层：脚本本身不知道 TeleAgent / opencode 的细节，
只执行一条命令模板（含 ``{prompt}`` 占位符），再在输出里检测技能是否被激活。

命令模板**按 argv 切分、不经 shell**（``shell=False``）：``{prompt}`` 始终作为
**参数内容**注入，模板里的 ``&`` / ``|`` / 反引号不会被 shell 解释。代价是模板
不能用 shell 语法（管道、重定向）；需要时请写一个包装脚本再让本脚本调用它。

支持的 runner:
    heuristic  不调用 agent，返回 triggered=None（调用方改用离线启发式）
    opencode   默认命令 ``opencode run "{prompt}"``
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
import re
import shlex
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
    try:
        proc = subprocess.run(
            argv,
            shell=False,
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
    except OSError as exc:
        return {
            "runner": runner,
            "triggered": None,
            "command": command,
            "returncode": None,
            "output": "",
            "error": f"could not run command: {exc}",
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
    parser = argparse.ArgumentParser(
        description="把一条 prompt 跑过 agent 客户端，并检测目标技能是否被触发。命令模板按 argv 切分、不经 shell。",
        epilog=(
            "示例:\n"
            '  python agent_runner.py --runner opencode --detect shy-skill-suite --prompt "帮我写个技能需求"\n'
            '  python agent_runner.py --runner cmd --cmd "my-cli --json {prompt}" --detect my-skill --prompt "帮我写个技能需求"\n'
            "\n"
            "退出码:\n"
            "  0  triggered 为 true（检测到技能被激活）\n"
            "  1  triggered 为 false，或运行错误 / 超时\n"
            "  2  参数错误\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
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
