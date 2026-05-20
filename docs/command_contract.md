# B 任务专家输出与沙箱命令约定

## 1. 专家输出 JSON

`ReconExpert` 与 `ExploitExpert` 都输出同一类结构，最小字段如下：

```json
{
  "tool": "nmap",
  "command": "nmap -sV -Pn -p 1100 127.0.0.1",
  "status": "ready"
}
```

字段说明：

- `tool`: 本周允许 `nmap` 或 `sqlmap`。
- `command`: 传给 D 同学沙箱函数 `execute(command: str, timeout: int = 120)` 的原始字符串。
- `status`: `ready` 表示可以执行；`need_more_info` 和 `blocked` 不应进入 Execution。
- `target`、`purpose`、`reason`: 便于前端展示和调试，可选但推荐保留。

## 2. State 读写约定

专家节点会尽量兼容多种队列写法：

- `state["recon_messages"][-1]["content"]`
- `state["exploit_messages"][-1]["content"]`
- `state["messages"]["recon"][-1]["content"]`
- `state["plan"]["steps"][state["current_step"]]["instruction"]`

节点输出会写入：

- `state["last_expert"]`
- `state["last_expert_output"]`
- `state["recon_output"]` 或 `state["exploit_output"]`
- `state["pending_tool"]`
- `state["pending_command"]`

只有当 `status == "ready"` 时才写入 `pending_command`。

## 3. 推荐接入 LangGraph 的方式

```python
from langgraph.graph import StateGraph
from agents import recon_expert_node, exploit_expert_node

graph = StateGraph(AgentState)
graph.add_node("ReconExpert", recon_expert_node)
graph.add_node("ExploitExpert", exploit_expert_node)
```

等 A 同学完成统一模型接口后，如果项目根目录存在 `llm_client.py` 且提供：

```python
def call_llm(system_prompt: str, user_prompt: str, state: dict) -> str:
    ...
```

本模块会自动调用它；也可以通过 `build_recon_expert(llm_call=...)` 显式注入。

## 4. 安全边界

本周 B 模块只生成授权靶场/本机测试命令。命令校验会拒绝 shell 拼接、管道、重定向、脚本解释器、下载器、系统破坏类命令，以及未列入白名单的高风险参数。
