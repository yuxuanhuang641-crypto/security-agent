"""LangGraph-compatible expert nodes for reconnaissance and exploit planning."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, MutableMapping, Protocol

from .json_utils import ExpertOutputError, extract_json_object, validate_expert_output

AgentState = MutableMapping[str, Any]


class ExpertNodeError(RuntimeError):
    """Raised when an expert node cannot produce a valid state update."""


class LLMCallable(Protocol):
    def __call__(self, *, system_prompt: str, user_prompt: str, state: AgentState) -> str:
        ...


ROOT_DIR = Path(__file__).resolve().parents[1]
PROMPT_DIR = ROOT_DIR / "prompts"


def build_recon_expert(llm_call: LLMCallable | None = None) -> Callable[[AgentState], AgentState]:
    """Build a ReconExpert node with an injectable LLM client."""

    return _build_expert(
        expert_name="recon",
        expected_tool="nmap",
        prompt_path=PROMPT_DIR / "recon.md",
        llm_call=llm_call,
    )


def build_exploit_expert(llm_call: LLMCallable | None = None) -> Callable[[AgentState], AgentState]:
    """Build an ExploitExpert node with an injectable LLM client."""

    return _build_expert(
        expert_name="exploit",
        expected_tool="sqlmap",
        prompt_path=PROMPT_DIR / "exploit.md",
        llm_call=llm_call,
    )


def recon_expert_node(state: AgentState) -> AgentState:
    """Default ReconExpert node, ready to register in a LangGraph StateGraph."""

    return build_recon_expert()(state)


def exploit_expert_node(state: AgentState) -> AgentState:
    """Default ExploitExpert skeleton node, ready to register in a StateGraph."""

    return build_exploit_expert()(state)


def _build_expert(
    *,
    expert_name: str,
    expected_tool: str,
    prompt_path: Path,
    llm_call: LLMCallable | None,
) -> Callable[[AgentState], AgentState]:
    system_prompt = prompt_path.read_text(encoding="utf-8")
    actual_llm_call = llm_call or _load_project_llm_client() or _mock_llm_call

    def node(state: AgentState) -> AgentState:
        instruction = _get_expert_instruction(state, expert_name)
        if not instruction:
            return _record_error(state, expert_name, "No instruction found for expert")

        user_prompt = f"专家类型: {expert_name}\n任务指令: {instruction}"
        try:
            raw_output = actual_llm_call(system_prompt=system_prompt, user_prompt=user_prompt, state=state)
            parsed = extract_json_object(raw_output)
            normalized = validate_expert_output(parsed, expected_tool=expected_tool)
        except (ExpertOutputError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return _record_error(state, expert_name, str(exc))

        next_state = dict(state)
        next_state["last_expert"] = expert_name
        next_state["last_expert_output"] = normalized
        next_state[f"{expert_name}_output"] = normalized

        messages_key = f"{expert_name}_messages"
        messages = list(next_state.get(messages_key, []))
        messages.append({"role": "user", "content": instruction})
        messages.append({"role": "assistant", "content": json.dumps(normalized, ensure_ascii=False)})
        next_state[messages_key] = messages

        if normalized["status"] == "ready":
            next_state["pending_command"] = normalized["command"]
            next_state["pending_tool"] = normalized["tool"]
        else:
            next_state.pop("pending_command", None)
            next_state.pop("pending_tool", None)

        return next_state

    return node


def _get_expert_instruction(state: AgentState, expert_name: str) -> str:
    queue_keys = [
        f"{expert_name}_queue",
        f"{expert_name}_messages",
        expert_name,
    ]
    for key in queue_keys:
        value = state.get(key)
        instruction = _extract_last_content(value)
        if instruction:
            return instruction

    messages = state.get("messages")
    if isinstance(messages, dict):
        instruction = _extract_last_content(messages.get(expert_name))
        if instruction:
            return instruction

    plan_instruction = _get_current_plan_instruction(state, expert_name)
    if plan_instruction:
        return plan_instruction

    return str(state.get("instruction", "")).strip()


def _extract_last_content(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list) and value:
        last = value[-1]
        if isinstance(last, dict):
            return str(last.get("content") or last.get("instruction") or "").strip()
        return str(last).strip()
    if isinstance(value, dict):
        return str(value.get("content") or value.get("instruction") or "").strip()
    return ""


def _get_current_plan_instruction(state: AgentState, expert_name: str) -> str:
    plan = state.get("plan") or {}
    current_step = int(state.get("current_step", 0) or 0)
    steps = plan.get("steps") if isinstance(plan, dict) else None
    if not isinstance(steps, list) or current_step >= len(steps):
        return ""
    step = steps[current_step]
    if not isinstance(step, dict):
        return ""
    if str(step.get("expert", "")).lower() != expert_name:
        return ""
    return str(step.get("instruction", "")).strip()


def _record_error(state: AgentState, expert_name: str, message: str) -> AgentState:
    next_state = dict(state)
    errors = list(next_state.get("errors", []))
    errors.append({"expert": expert_name, "message": message})
    next_state["errors"] = errors
    next_state["last_expert"] = expert_name
    next_state["last_expert_output"] = {
        "tool": "nmap" if expert_name == "recon" else "sqlmap",
        "command": "",
        "status": "blocked",
        "reason": message,
    }
    next_state.pop("pending_command", None)
    next_state.pop("pending_tool", None)
    return next_state


def _load_project_llm_client() -> LLMCallable | None:
    """Use A student's future llm_client.py when it is available."""

    try:
        from llm_client import call_llm  # type: ignore
    except Exception:
        return None

    def adapter(*, system_prompt: str, user_prompt: str, state: AgentState) -> str:
        return call_llm(system_prompt=system_prompt, user_prompt=user_prompt, state=state)

    return adapter


def _mock_llm_call(*, system_prompt: str, user_prompt: str, state: AgentState) -> str:
    """Deterministic local fallback for integration tests before API keys exist."""

    del system_prompt, state
    instruction = user_prompt.split("任务指令:", 1)[-1].strip()
    lowered = instruction.lower()
    if "recon" in user_prompt or "扫描" in instruction or "nmap" in lowered:
        target = _extract_target(instruction) or "127.0.0.1"
        ports = _extract_ports(instruction) or "1-1000"
        return json.dumps(
            {
                "tool": "nmap",
                "command": f"nmap -sV -Pn -p {ports} {target}",
                "status": "ready",
                "target": target,
                "purpose": "scan requested TCP service/version information",
            },
            ensure_ascii=False,
        )

    url = _extract_url(instruction)
    if url:
        return json.dumps(
            {
                "tool": "sqlmap",
                "command": f"sqlmap -u {url} --batch --level 1 --risk 1",
                "status": "ready",
                "target": url,
                "purpose": "authorized SQL injection check with low-risk options",
            },
            ensure_ascii=False,
        )
    return json.dumps(
        {
            "tool": "sqlmap",
            "command": "",
            "status": "need_more_info",
            "reason": "ExploitExpert skeleton needs an explicit authorized URL before generating sqlmap command.",
        },
        ensure_ascii=False,
    )


def _extract_target(text: str) -> str:
    ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
    if ip_match:
        return ip_match.group(0)
    host_match = re.search(r"\b(?:localhost|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b", text)
    return host_match.group(0) if host_match else ""


def _extract_ports(text: str) -> str:
    port_match = re.search(r"(\d{1,5}(?:-\d{1,5})?)(?:\s*(?:端口|port|ports))", text, flags=re.IGNORECASE)
    if port_match:
        return port_match.group(1)
    port_after_keyword = re.search(r"(?:端口|port|ports)\s*(\d{1,5}(?:-\d{1,5})?)", text, flags=re.IGNORECASE)
    return port_after_keyword.group(1) if port_after_keyword else ""


def _extract_url(text: str) -> str:
    match = re.search(r"https?://[^\s\"']+", text)
    return match.group(0).rstrip(".,，。") if match else ""
