"""Minimal Streamlit frontend for the first-week security-agent demo."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


# Week-1 demo shortcut: allow running `streamlit run frontend/app.py` directly.
# Later this should be replaced by a formal package layout or backend API call.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.analyze_expert import analyze_expert_node  # noqa: E402
from agents.report_expert import report_expert_node  # noqa: E402


def build_mock_state(user_input: str) -> dict:
    """Build a safe mock state for local demo without executing commands."""
    mock_command = "nmap -sV -p 1100 127.0.0.1"
    return {
        "user_input": user_input,
        "task_status": "running",
        "current_command": {
            "tool": "nmap",
            "command": mock_command,
        },
        "execution_result": {
            "tool": "nmap",
            "command": mock_command,
            "stdout": "PORT     STATE SERVICE VERSION\n1100/tcp open  http    mock-service",
            "stderr": "",
            "exit_code": 0,
            "success": True,
        },
    }


st.set_page_config(page_title="security-agent 安全智能体演示界面", layout="wide")
st.title("security-agent 安全智能体演示界面")

user_input = st.text_area(
    "任务输入",
    value="扫描 127.0.0.1 的 1100 端口",
    height=100,
)

if st.button("开始分析", type="primary"):
    state = build_mock_state(user_input)
    state = analyze_expert_node(state)
    state = report_expert_node(state)
    state["task_status"] = "success"

    st.subheader("执行状态")
    st.success(state["task_status"])

    st.subheader("工具执行结果")
    st.json(state["current_command"])
    execution_result = state["execution_result"]
    st.write(f"exit_code: {execution_result.get('exit_code')}")
    st.write(f"success: {execution_result.get('success')}")
    st.caption("stdout")
    st.code(execution_result.get("stdout", ""), language="text")
    st.caption("stderr")
    st.code(execution_result.get("stderr", ""), language="text")

    st.subheader("分析摘要")
    analysis_result = state["analysis_result"]
    st.write(f"风险等级：{analysis_result.get('risk_level', 'unknown')}")
    st.write(analysis_result.get("summary", "暂无数据"))
    st.json(analysis_result.get("key_findings", []))

    st.subheader("Markdown 报告")
    st.markdown(state["final_report"])
else:
    st.info("输入授权测试任务后点击开始分析。当前版本使用 mock 数据演示分析与报告链路。")
