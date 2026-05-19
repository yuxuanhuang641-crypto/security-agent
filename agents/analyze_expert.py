"""AnalyzeExpert node for the first-week security-agent demo.

This module is a minimal rule-based placeholder for the E module. It does not
execute commands or call external services. Later, the rule logic can be
replaced by LLM-assisted analysis or richer parsers while keeping the same
state-dictionary interface for LangGraph integration.
"""

from __future__ import annotations

from typing import Any


def _as_text(value: Any, default: str = "") -> str:
    """Return a stable string representation for optional state fields."""
    if value is None:
        return default
    return str(value)


def _extract_evidence(stdout: str, stderr: str) -> list[str]:
    """Extract short, useful output snippets for the mock analysis result."""
    keywords = ("open", "filtered", "closed", "error", "failed", "vulnerable")
    evidence: list[str] = []

    for line in stdout.splitlines():
        normalized = line.strip()
        if normalized and any(keyword in normalized.lower() for keyword in keywords):
            evidence.append(normalized)

    if not evidence:
        for line in stdout.splitlines():
            normalized = line.strip()
            if normalized:
                evidence.append(normalized)
                break

    if stderr.strip():
        evidence.append(f"stderr: {stderr.strip()[:300]}")

    return evidence[:5]


def analyze_expert_node(state: dict) -> dict:
    """Analyze tool execution output and write structured findings to state.

    The function mimics a LangGraph node: it reads fields from ``state`` and
    returns the updated state. This first-week version is intentionally simple
    and rule-based, so it is safe for authorized lab demos and easy to replace
    during later integration.
    """
    execution_result = state.get("execution_result") or {}
    stdout = _as_text(execution_result.get("stdout"))
    stderr = _as_text(execution_result.get("stderr"))
    exit_code = execution_result.get("exit_code")
    success = execution_result.get("success")

    stdout_lower = stdout.lower()
    key_findings: list[dict[str, str]] = []
    next_steps: list[str] = []

    if exit_code not in (0, None) or success is False:
        summary = "工具执行未成功完成，当前结果不足以形成明确安全结论。"
        risk_level = "unknown"
        key_findings.append(
            {
                "title": "工具执行失败",
                "evidence": "exit_code 非 0 或 success 为 false",
                "recommendation": "检查工具参数、目标地址、沙箱权限和后端执行日志后重试。",
            }
        )
        next_steps.extend(
            [
                "建议先确认任务输入和工具参数是否符合授权测试范围。",
                "建议查看 stderr 或后端执行日志定位失败原因。",
            ]
        )
    elif not stdout.strip():
        summary = "工具未返回有效 stdout，当前无法提取可分析结果。"
        risk_level = "unknown"
        key_findings.append(
            {
                "title": "缺少有效输出",
                "evidence": "stdout 为空",
                "recommendation": "确认 Execution 节点是否正确捕获工具输出。",
            }
        )
        next_steps.extend(
            [
                "建议补充工具原始输出或执行上下文。",
                "建议由 Planner 生成更明确的目标和参数。",
            ]
        )
    elif "open" in stdout_lower:
        summary = "本次扫描发现目标主机存在开放端口或可访问服务。"
        risk_level = "medium"
        key_findings.append(
            {
                "title": "发现开放端口",
                "evidence": "stdout 中出现 open 字段",
                "recommendation": "确认该端口对应服务是否为业务必要服务，并检查访问控制策略。",
            }
        )
        next_steps.extend(
            [
                "建议结合服务版本进行进一步授权验证。",
                "建议检查该端口的访问控制、暴露范围和最小化开放策略。",
            ]
        )
    elif "filtered" in stdout_lower:
        summary = "本次扫描显示目标端口可能被过滤，暂未发现明确开放服务。"
        risk_level = "low"
        key_findings.append(
            {
                "title": "端口被过滤",
                "evidence": "stdout 中出现 filtered 字段",
                "recommendation": "保留现有访问控制策略，并结合业务需求确认过滤规则是否合理。",
            }
        )
        next_steps.extend(
            [
                "建议结合授权范围确认防火墙或安全组策略。",
                "建议在后续联调中补充更完整的端口状态解析。",
            ]
        )
    elif "closed" in stdout_lower:
        summary = "本次扫描显示目标端口关闭，当前未发现开放服务证据。"
        risk_level = "low"
        key_findings.append(
            {
                "title": "端口关闭",
                "evidence": "stdout 中出现 closed 字段",
                "recommendation": "如该端口不承载业务服务，建议保持关闭状态。",
            }
        )
        next_steps.extend(
            [
                "建议记录当前基线结果，便于后续变更对比。",
                "建议继续检查授权范围内的其他目标或端口。",
            ]
        )
    else:
        summary = "工具返回了输出，但当前规则未识别到明确风险特征。"
        risk_level = "unknown"
        key_findings.append(
            {
                "title": "未识别明确风险",
                "evidence": "stdout 中未命中 open/filtered/closed 等基础规则",
                "recommendation": "后续可接入 LLM 或专用解析器提升分析覆盖率。",
            }
        )
        next_steps.extend(
            [
                "建议人工复核原始输出。",
                "建议在后续版本中扩展针对不同工具的解析规则。",
            ]
        )

    state["analysis_result"] = {
        "summary": summary,
        "risk_level": risk_level,
        "key_findings": key_findings,
        "evidence": _extract_evidence(stdout, stderr),
        "next_steps": next_steps,
    }
    return state
