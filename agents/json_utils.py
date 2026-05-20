"""Utilities for extracting and validating expert JSON output."""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass
from typing import Any


class ExpertOutputError(ValueError):
    """Raised when an expert model response cannot be used safely."""


@dataclass(frozen=True)
class CommandPolicy:
    tool: str
    allowed_flags: frozenset[str]
    required_prefix: str


COMMAND_POLICIES: dict[str, CommandPolicy] = {
    "nmap": CommandPolicy(
        tool="nmap",
        required_prefix="nmap",
        allowed_flags=frozenset(
            {
                "-sV",
                "-sT",
                "-Pn",
                "-n",
                "-p",
                "-T2",
                "-T3",
                "--top-ports",
                "--version-light",
            }
        ),
    ),
    "sqlmap": CommandPolicy(
        tool="sqlmap",
        required_prefix="sqlmap",
        allowed_flags=frozenset(
            {
                "-u",
                "--url",
                "--batch",
                "--level",
                "--risk",
                "--threads",
                "--random-agent",
                "--current-user",
                "--current-db",
                "--dbs",
                "--forms",
                "--crawl",
                "--cookie",
                "--method",
                "--data",
            }
        ),
    ),
}

FORBIDDEN_COMMAND_SUBSTRINGS = (
    "\n",
    "\r",
    ";",
    "&&",
    "||",
    "|",
    "`",
    "$(",
    ">",
    "<",
)

FORBIDDEN_TOKENS = {
    "bash",
    "sh",
    "cmd",
    "powershell",
    "pwsh",
    "python",
    "python3",
    "perl",
    "ruby",
    "curl",
    "wget",
    "nc",
    "netcat",
    "rm",
    "del",
    "format",
    "mkfs",
    "dd",
    "shutdown",
    "reboot",
    "sudo",
    "su",
    "apt",
    "apt-get",
    "yum",
    "docker",
}


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract a JSON object from direct JSON or a fenced model response."""

    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            raise ExpertOutputError("LLM output does not contain a JSON object")
        value = json.loads(match.group(0))

    if not isinstance(value, dict):
        raise ExpertOutputError("LLM output JSON must be an object")
    return value


def validate_expert_output(output: dict[str, Any], expected_tool: str | None = None) -> dict[str, Any]:
    """Validate the common expert output contract.

    A command is considered executable only when status is "ready". Skeleton
    experts may return status "need_more_info" with an empty command.
    """

    if "tool" not in output or "command" not in output:
        raise ExpertOutputError('expert output must contain "tool" and "command" fields')

    tool = str(output["tool"]).strip().lower()
    command = str(output["command"]).strip()
    status = str(output.get("status", "ready")).strip().lower()

    if expected_tool and tool != expected_tool:
        raise ExpertOutputError(f'expected tool "{expected_tool}", got "{tool}"')
    if tool not in COMMAND_POLICIES:
        raise ExpertOutputError(f'unsupported tool "{tool}"')
    if status not in {"ready", "need_more_info", "blocked"}:
        raise ExpertOutputError('status must be one of "ready", "need_more_info", "blocked"')

    normalized = dict(output)
    normalized["tool"] = tool
    normalized["command"] = command
    normalized["status"] = status

    if status != "ready":
        return normalized

    validate_command(tool, command)
    return normalized


def validate_command(tool: str, command: str) -> None:
    """Apply a conservative command policy before passing to the sandbox."""

    if not command:
        raise ExpertOutputError("ready expert output must include a non-empty command")
    for bad in FORBIDDEN_COMMAND_SUBSTRINGS:
        if bad in command:
            raise ExpertOutputError(f'command contains forbidden shell operator "{bad}"')

    try:
        parts = shlex.split(command, posix=True)
    except ValueError as exc:
        raise ExpertOutputError(f"command cannot be parsed safely: {exc}") from exc

    if not parts:
        raise ExpertOutputError("command is empty")
    if parts[0] != COMMAND_POLICIES[tool].required_prefix:
        raise ExpertOutputError(f'command must start with "{COMMAND_POLICIES[tool].required_prefix}"')

    lower_tokens = {part.lower() for part in parts}
    if lower_tokens & FORBIDDEN_TOKENS:
        blocked = ", ".join(sorted(lower_tokens & FORBIDDEN_TOKENS))
        raise ExpertOutputError(f"command contains forbidden token(s): {blocked}")

    allowed_flags = COMMAND_POLICIES[tool].allowed_flags
    for part in parts[1:]:
        if part.startswith("-") and part not in allowed_flags and not _is_nmap_timing(part):
            raise ExpertOutputError(f'flag "{part}" is not allowed for tool "{tool}"')


def _is_nmap_timing(flag: str) -> bool:
    return flag in {"-T0", "-T1", "-T2", "-T3"} or re.fullmatch(r"-T[0-3]", flag) is not None
