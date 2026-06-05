# API 与状态字段约定

本文档对齐 `security_agent_v2_containerized.zip` 中已经跑通的 v2 容器化后端，供 E 模块前端、测试用例和后续联调使用。

## 1. POST /task

v2 后端接口地址：

```text
http://127.0.0.1:8008/task
```

请求方法：

```text
POST
```

请求头：

```text
Content-Type: application/json; charset=utf-8
```

请求体：

```json
{
  "input_text": "请检查本地靶场 Juice Shop 服务是否可访问，目标为 http://range-juice-shop:3000，只允许进行连通性检查或端口识别。",
  "thread_id": "demo"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `input_text` | `str` | 是 | 用户输入的安全任务描述。v2 后端读取该字段作为规划智能体的初始输入。 |
| `thread_id` | `str` | 否 | LangGraph/InMemorySaver 的会话 ID，默认可用 `demo` 或 `default`。用于多轮状态隔离。 |

## 2. 成功返回格式

```json
{
  "status": "success",
  "plan": {
    "steps": [
      {
        "step_id": 1,
        "expert": "recon",
        "instruction": "扫描目标主机端口",
        "tool_id": "nmap",
        "params": {
          "target": "range-juice-shop",
          "args": "-sV -p 3000"
        }
      }
    ]
  },
  "final_report": "# 安全评估报告\n...",
  "execution_results": {
    "tool_id": "nmap",
    "command": "nmap -sV -p 3000 range-juice-shop",
    "status": "success",
    "output": "...",
    "errors": ""
  }
}
```

字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `status` | `str` | 接口执行状态。成功时为 `success`。 |
| `plan` | `dict` | 规划智能体生成的结构化计划，核心字段为 `steps`。 |
| `final_report` | `str` | 报告专家生成的 Markdown 报告。 |
| `execution_results` | `dict` | 后端响应中的工具执行结果字段。注意是复数形式。 |

## 3. 失败返回格式

```json
{
  "status": "failed",
  "error_type": "ValueError",
  "error": "错误信息",
  "trace_tail": "最近几层 traceback"
}
```

字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `status` | `str` | 失败时为 `failed`。 |
| `error_type` | `str` | Python 异常类型，便于定位后端错误。 |
| `error` | `str` | 简短错误信息。 |
| `trace_tail` | `str` | 截断后的 traceback，便于联调排查。 |

## 4. AgentState 内部字段

v2 后端内部状态字段来自 `graph/state.py`，建议各模块按以下字段对齐：

| 字段 | 类型建议 | 说明 |
| --- | --- | --- |
| `messages` | `list[AnyMessage]` | 全局消息记录，用于汇总执行过程。 |
| `planner_messages` | `list[AnyMessage]` | 规划智能体的输入/输出消息队列。 |
| `recon_messages` | `list[AnyMessage]` | 侦察专家的消息队列。 |
| `exploit_messages` | `list[AnyMessage]` | 验证专家的消息队列。 |
| `analyze_messages` | `list[AnyMessage]` | 分析专家的消息队列。 |
| `report_messages` | `list[AnyMessage]` | 报告专家的消息队列。 |
| `recon_updated` | `bool` | 是否激活侦察专家。 |
| `exploit_updated` | `bool` | 是否激活验证专家。 |
| `analyze_updated` | `bool` | 是否激活分析专家。 |
| `report_updated` | `bool` | 是否激活报告专家。 |
| `plan` | `dict` | 规划智能体输出，统一结构为 `{"steps": [...]}`。 |
| `current_step` | `int` | 当前执行步骤索引。 |
| `expert_output` | `dict` | 当前专家输出，通常包含 `tool_id` 和 `params`。 |
| `generated_command` | `str` | ToolMapper 根据 `tool_id/params` 生成的命令字符串。 |
| `execution_result` | `dict` | 内部 state 中的执行结果字段。 |
| `final_report` | `str` | 报告专家输出的 Markdown 报告。 |

命名注意：

- 后端响应字段是 `execution_results`。
- LangGraph 内部 state 字段是 `execution_result`。
- 前端展示时应优先读取响应中的 `execution_results`，必要时兼容旧字段 `execution_result`。

## 5. 规划智能体输出格式

规划智能体必须输出纯 JSON。当前 v2 后端工具执行链路的核心结构如下：

```json
{
  "steps": [
    {
      "step_id": 1,
      "expert": "recon",
      "instruction": "扫描目标主机的 3000 端口",
      "tool_id": "nmap",
      "params": {
        "target": "range-juice-shop",
        "args": "-sV -p 3000"
      }
    }
  ]
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `expert` | 可选值包括 `recon`、`exploit`、`analyze`、`report`。 |
| `tool_id` | 工具 ID，例如 `nmap`、`sqlmap`、`httpx`、`nuclei`。无需工具时可为 `null`。 |
| `params.target` | 靶场目标。v2 推荐使用 `range-juice-shop`、`range-webgoat`、`range-dvwa`。 |
| `params.args` | 工具参数，例如 `-sV -p 3000`。 |

若接入 AI 安全审计版规划智能体，推荐保留顶层 `workflow`，并在步骤中增加 `template_id`。`template_id` 应优先引用 `knowledge_base/ai_safety_knowledge_base.json` 中的 snake_case 模板 ID：

```json
{
  "workflow": "prompt-injection-test",
  "steps": [
    {
      "step_id": 1,
      "expert": "exploit",
      "instruction": "使用提示词注入模板进行授权安全审计。",
      "template_id": "prompt_injection_basic",
      "params": {
        "target": "demo-ai-assistant",
        "prompt": "授权测试用提示词",
        "session_id": "demo",
        "extra_args": {}
      }
    },
    {
      "step_id": 2,
      "expert": "analyze",
      "instruction": "分析模型响应并判断风险等级。",
      "template_id": null,
      "params": {
        "target": "demo-ai-assistant",
        "prompt": null,
        "session_id": "demo",
        "extra_args": {}
      }
    },
    {
      "step_id": 3,
      "expert": "report",
      "instruction": "汇总审计结果并生成报告。",
      "template_id": null,
      "params": {
        "target": "demo-ai-assistant",
        "prompt": null,
        "session_id": "demo",
        "extra_args": {}
      }
    }
  ]
}
```

AI 安全审计版新增字段说明：

| 字段 | 说明 |
| --- | --- |
| `workflow` | 本次任务选择的工作流，例如 `prompt-injection-test`、`jailbreak-test`、`sensitive-leakage-test`、`comprehensive-ai-audit`。 |
| `template_id` | 知识库中的检测模板 ID，例如 `prompt_injection_basic`、`rag_poisoning_basic`、`memory_cross_session_leakage`。没有固定模板时可为 `null`。 |
| `params.prompt` | 授权安全测试使用的测试提示词或样本。 |
| `params.session_id` | 与 `thread_id` 对齐的会话标识，便于多轮审计和状态隔离。 |
| `params.extra_args` | 扩展参数，例如检测轮次、语言、模型版本、风险项开关等。 |

## 6. 前端展示字段

`frontend/app.py` 需要展示以下内容：

- 请求体：`input_text`、`thread_id`
- 接口状态：`status`
- 计划：`plan`
- 执行结果：`execution_results`
- 最终报告：`final_report`
- 错误信息：`error_type`、`error`、`trace_tail`

## 7. 联调说明

1. 按 v2 部署说明启动后端，确保接口可访问：

   ```text
   http://127.0.0.1:8008/task
   ```

2. 启动 E 模块测试前端：

   ```powershell
   streamlit run frontend/app.py
   ```

3. 在前端选择测试用例，确认请求体为 `input_text/thread_id` 格式。

4. 若返回 `status=success`，前端应展示 `plan`、`execution_results` 和 `final_report`。

5. 若后端未启动或返回失败，前端应展示清晰错误信息，不应伪造成功结果。
