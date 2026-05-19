# API 与状态字段约定

## 1. AgentState 建议字段

| 字段 | 类型建议 | 含义 |
| --- | --- | --- |
| `user_input` | `str` | 用户原始输入。 |
| `plan` | `dict \| list` | Planner 生成的任务计划，可包含步骤、专家类型和执行顺序。 |
| `current_step` | `int` | 当前步骤编号。 |
| `current_expert` | `str` | 当前专家类型，例如 `recon`、`exploit`、`analyze`、`report`。 |
| `current_instruction` | `str` | 当前专家收到的任务指令。 |
| `current_command` | `dict` | 专家生成的工具命令，建议包含 `tool` 和 `command`。 |
| `execution_result` | `dict` | Execution 节点返回的工具执行结果。 |
| `analysis_result` | `dict` | AnalyzeExpert 输出的结构化分析。 |
| `final_report` | `str` | ReportExpert 输出的 Markdown 报告。 |
| `messages` | `list` | 可选，用于多轮对话或状态追踪。 |
| `task_status` | `str` | 任务状态，例如 `pending`、`running`、`success`、`failed`。 |

`execution_result` 建议结构：

```json
{
  "tool": "nmap",
  "command": "nmap -sV -p 1100 127.0.0.1",
  "stdout": "PORT     STATE SERVICE VERSION\n1100/tcp open  http    mock-service",
  "stderr": "",
  "exit_code": 0,
  "success": true
}
```

`analysis_result` 建议结构：

```json
{
  "summary": "本次扫描发现目标主机存在开放端口或可访问服务。",
  "risk_level": "medium",
  "key_findings": [
    {
      "title": "发现开放端口",
      "evidence": "stdout 中出现 open 字段",
      "recommendation": "确认该端口对应服务是否为业务必要服务，并检查访问控制策略。"
    }
  ],
  "evidence": [
    "1100/tcp open  http    mock-service"
  ],
  "next_steps": [
    "建议结合服务版本进行进一步授权验证。",
    "建议检查该端口的访问控制、暴露范围和最小化开放策略。"
  ]
}
```

## 2. POST /task 输入格式

```json
{
  "input": "扫描 127.0.0.1 的 1100 端口"
}
```

## 3. POST /task 返回格式

当前阶段可以先支持最终返回：

```json
{
  "task_status": "success",
  "execution_result": {},
  "analysis_result": {},
  "final_report": "..."
}
```

后续如果 C 同学实现 SSE 或 WebSocket，可扩展为事件流，例如按 `planning`、`executing`、`analyzing`、`reporting`、`done` 推送阶段状态。

## 4. 前端展示字段

`frontend/app.py` 需要展示以下字段：

- `task_status`
- `current_command`
- `execution_result.stdout`
- `execution_result.stderr`
- `execution_result.exit_code`
- `analysis_result.summary`
- `analysis_result.risk_level`
- `analysis_result.key_findings`
- `final_report`

## 5. 联调说明

当前前端使用 mock 数据；后续只需要把 mock state 替换为真实后端 API 返回值。

建议联调步骤：

1. C 同学提供 `POST /task`，接收用户输入并返回约定字段。
2. 前端将 `build_mock_state()` 替换为后端请求。
3. 如果后端已经在 LangGraph 内部调用 AnalyzeExpert 和 ReportExpert，前端直接展示返回结果。
4. 如果后端只返回 Execution 输出，则前端不建议自行分析，应该由后端统一调用 E 模块节点，避免状态逻辑分散。
