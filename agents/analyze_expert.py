"""第一周演示用的分析专家节点。

本模块是 E 模块的最小可用规则分析占位实现，不执行系统命令，也不调用外部服务。
后续可以在保持 `state` 字典接口不变的前提下，将规则逻辑替换为大模型辅助分析
或更完整的工具输出解析器，方便接入 LangGraph。
"""

from __future__ import annotations

from typing import Any


def _as_text(value: Any, default: str = "") -> str:
    """把可选字段稳定转换为字符串。"""
    if value is None:
        return default
    return str(value)


def _extract_evidence(stdout: str, stderr: str) -> list[str]:
    """从工具输出中提取简短、可展示的关键证据片段。"""
    keywords = (
        "open",
        "filtered",
        "closed",
        "error",
        "failed",
        "vulnerable",
        "injectable",
        "sql injection",
        "need_more_info",
        "blocked",
        "isolation",
    )
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
    """分析工具执行结果，并把结构化结论写入 `state["analysis_result"]`。

    函数行为模拟 LangGraph 节点：从 `state` 读取约定字段，处理后返回更新后的
    `state`。当前版本刻意保持简单，采用规则判断，适合授权靶场演示和后续替换。
    """
    execution_result = state.get("execution_result") or {}
    stdout = _as_text(execution_result.get("stdout"))
    stderr = _as_text(execution_result.get("stderr"))
    exit_code = execution_result.get("exit_code")
    success = execution_result.get("success")
    status = _as_text(execution_result.get("status")).lower()

    stdout_lower = stdout.lower()
    key_findings: list[dict[str, str]] = []
    next_steps: list[str] = []

    if status == "blocked" or "blocked" in stdout_lower:
        summary = "系统识别到疑似危险输入，当前任务已被拦截，未进入真实命令执行。"
        risk_level = "unknown"
        key_findings.append(
            {
                "title": "危险输入已拦截",
                "evidence": "执行结果中出现 blocked 或策略拦截信息",
                "recommendation": "要求用户提供明确授权范围，并通过沙箱白名单重新生成安全命令。",
            }
        )
        next_steps.extend(
            [
                "建议保留拦截日志，便于后续审计。",
                "建议由规划节点或执行节点继续强化命令白名单校验。",
            ]
        )
    elif status == "need_more_info" or "need_more_info" in stdout_lower:
        summary = "当前任务意图或目标信息不足，系统需要更多输入后才能继续分析。"
        risk_level = "unknown"
        key_findings.append(
            {
                "title": "需要补充任务信息",
                "evidence": "执行结果中出现 need_more_info 或缺少目标信息提示",
                "recommendation": "补充目标地址、端口、授权范围和期望检测类型后重新提交任务。",
            }
        )
        next_steps.extend(
            [
                "建议前端提示用户补充目标和授权范围。",
                "建议规划节点生成澄清问题，而不是直接进入执行节点。",
            ]
        )
    elif "sql injection" in stdout_lower or "injectable" in stdout_lower:
        summary = "本次检测发现疑似 SQL 注入风险，需要在授权环境中进一步人工确认。"
        risk_level = "high"
        key_findings.append(
            {
                "title": "疑似 SQL 注入风险",
                "evidence": "stdout 中出现 sql injection 或 injectable 字段",
                "recommendation": "仅在授权靶场中复核参数过滤、预编译语句和后端日志，不进行未授权利用。",
            }
        )
        next_steps.extend(
            [
                "建议确认该 URL 是否属于授权测试范围。",
                "建议检查参数化查询、输入校验和错误回显配置。",
            ]
        )
    elif "isolation" in stdout_lower or "task_id" in stdout_lower or "session" in stdout_lower:
        summary = "本次并发/多用户模拟检查显示任务状态具备隔离标识，暂未发现状态污染迹象。"
        risk_level = "low"
        key_findings.append(
            {
                "title": "任务状态隔离检查",
                "evidence": "stdout 中出现 task_id、session 或 isolation 字段",
                "recommendation": "后续后端联调时继续为每个任务保留 task_id 或 session_id。",
            }
        )
        next_steps.extend(
            [
                "建议 C 同学在 FastAPI/LangGraph 状态中保留任务 ID。",
                "建议前端展示任务 ID，便于多用户请求排查。",
            ]
        )
    elif exit_code not in (0, None) or success is False:
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
                "recommendation": "确认执行节点是否正确捕获工具输出。",
            }
        )
        next_steps.extend(
            [
                "建议补充工具原始输出或执行上下文。",
                "建议由规划节点生成更明确的目标和参数。",
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
