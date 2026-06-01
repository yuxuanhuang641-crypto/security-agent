"""第一周演示用的报告专家节点。

本节点把当前 `state` 字典整理成 Markdown 安全分析报告。当前实现保持简单、
稳定、可预测，便于前端展示和 LangGraph 联调。
"""

from __future__ import annotations

from typing import Any


DEFAULT_TEXT = "暂无数据"


def _as_text(value: Any, default: str = DEFAULT_TEXT) -> str:
    if value is None or value == "":
        return default
    return str(value)


def _command_info(current_command: Any, execution_result: dict) -> tuple[str, str]:
    if isinstance(current_command, dict):
        tool = current_command.get("tool") or execution_result.get("tool")
        command = current_command.get("command") or execution_result.get("command")
    else:
        tool = execution_result.get("tool")
        command = current_command or execution_result.get("command")
    return _as_text(tool), _as_text(command)


def _format_bullets(items: Any) -> str:
    if not items:
        return f"- {DEFAULT_TEXT}"
    if isinstance(items, str):
        return f"- {_as_text(items)}"
    return "\n".join(f"- {_as_text(item)}" for item in items)


def _format_key_findings(findings: Any) -> str:
    if not findings:
        return f"- {DEFAULT_TEXT}"

    lines: list[str] = []
    for finding in findings:
        if not isinstance(finding, dict):
            lines.append(f"- {_as_text(finding)}")
            continue
        title = _as_text(finding.get("title"))
        evidence = _as_text(finding.get("evidence"))
        recommendation = _as_text(finding.get("recommendation"))
        lines.append(f"- **{title}**")
        lines.append(f"  - 证据：{evidence}")
        lines.append(f"  - 建议：{recommendation}")
    return "\n".join(lines)


def _collect_recommendations(analysis_result: dict) -> list[str]:
    recommendations: list[str] = []
    next_steps = analysis_result.get("next_steps") or []
    if isinstance(next_steps, str):
        next_steps = [next_steps]

    for step in next_steps:
        text = _as_text(step)
        if text not in recommendations:
            recommendations.append(text)

    for finding in analysis_result.get("key_findings") or []:
        if isinstance(finding, dict) and finding.get("recommendation"):
            text = _as_text(finding.get("recommendation"))
            if text not in recommendations:
                recommendations.append(text)

    return recommendations


def report_expert_node(state: dict) -> dict:
    """生成 Markdown 安全分析报告，并写入 `state["final_report"]`。"""
    user_input = _as_text(state.get("user_input"))
    current_command = state.get("current_command") or {}
    execution_result = state.get("execution_result") or {}
    analysis_result = state.get("analysis_result") or {}

    tool, command = _command_info(current_command, execution_result)
    stdout = _as_text(execution_result.get("stdout"))
    stderr = _as_text(execution_result.get("stderr"))
    exit_code = _as_text(execution_result.get("exit_code"))
    success = _as_text(execution_result.get("success"))

    summary = _as_text(analysis_result.get("summary"))
    risk_level = _as_text(analysis_result.get("risk_level"))
    key_findings = _format_key_findings(analysis_result.get("key_findings"))
    evidence = _format_bullets(analysis_result.get("evidence"))
    recommendations = _format_bullets(_collect_recommendations(analysis_result))

    report = f"""# 安全分析报告

## 1. 任务概述

用户输入任务：{user_input}

## 2. 执行动作

- 工具：{tool}
- 命令：{command}

## 3. 执行结果摘要

- exit_code：{exit_code}
- success：{success}
- stdout：

```text
{stdout}
```

- stderr：

```text
{stderr}
```

## 4. 分析结论

- 摘要：{summary}
- 风险等级：{risk_level}

{key_findings}

## 5. 证据链

{evidence}

## 6. 处置建议

{recommendations}

## 7. 合规说明

本报告仅适用于授权安全测试、本地靶场、安全运维辅助和教学演示环境，不用于未授权攻击、绕过审计、隐藏痕迹或真实攻击扩散。
"""

    state["final_report"] = report
    return state
