# 逆向分析场景联调说明

本文档记录 E 侧对新增 `reverse_expert` 逆向分析场景的测试期望。当前不新增后端接口，仍沿用 v2 后端的 `POST /task`。

## 1. 场景定位

逆向分析场景用于授权样本、隔离沙箱和教学/比赛演示环境中的二进制分析、动态行为跟踪和测试哈希样本分析。该场景不用于未授权样本分析、真实口令破解、真实恶意样本运行或绕过沙箱限制。

E 侧本轮负责：

- 编写逆向分析端到端测试用例。
- 在 Streamlit 前端提供逆向用例选择入口。
- 验证后端接入后，前端能展示 `plan`、`execution_results` 和 `final_report`。

## 2. 请求格式

接口不变：

```text
POST http://127.0.0.1:8008/task
```

请求体示例：

```json
{
  "input_text": "我已获得授权，请对隔离沙箱中的样本 /samples/reverse/hello_elf 进行基础逆向分析。",
  "thread_id": "demo-reverse-basic"
}
```

## 3. 推荐 Planner 输出结构

后端接入逆向场景后，推荐 Planner 在 `plan` 中保留 `workflow=reverse-analysis`，并把逆向分析步骤路由到 `reverse` 专家。

```json
{
  "workflow": "reverse-analysis",
  "steps": [
    {
      "step_id": 1,
      "expert": "reverse",
      "instruction": "对授权样本进行基础逆向分析",
      "tool_id": "rizin",
      "params": {
        "target": "/samples/reverse/hello_elf",
        "analysis_depth": "basic"
      }
    },
    {
      "step_id": 2,
      "expert": "analyze",
      "instruction": "研判逆向分析结果中的危险函数和安全属性缺失"
    },
    {
      "step_id": 3,
      "expert": "report",
      "instruction": "生成逆向分析报告"
    }
  ]
}
```

## 4. 状态传递期望

| 阶段 | E 侧验收重点 |
| --- | --- |
| Planner | 能识别“逆向分析”“二进制分析”“危险函数”“动态跟踪”“哈希样本”等意图，并生成 `reverse -> analyze -> report` 链路。 |
| ReverseExpert | 能输出工具调用建议，包括 `rizin`、`ghidra`、`strace`、`john` 及对应参数。 |
| Execution | 能捕获逆向工具标准输出、标准错误、退出码和执行状态，并写入 `execution_results` 或内部 `execution_result`。 |
| AnalyzeExpert | 能从逆向输出中提取文件类型、架构、入口点、函数、字符串、危险函数、安全属性和动态行为摘要。 |
| ReportExpert | 能生成 Markdown 报告，包含任务概述、工具动作、关键证据、分析结论、建议和合规说明。 |
| Frontend | 能展示请求体、接口状态、计划、执行结果、最终报告和错误信息。 |

## 5. 前端测试入口

`frontend/app.py` 已提供以下逆向测试用例：

- `REV-001 基础二进制信息分析`
- `REV-002 深度危险函数分析`
- `REV-003 动态行为跟踪分析`
- `REV-004 哈希/口令样本分析`

前端只向后端发送请求，不执行本地逆向工具。若后端尚未接入 reverse 节点，前端应展示真实失败信息，不应伪造成成功。

## 6. 依赖与分工

| 依赖项 | 负责人 | E 侧对接方式 |
| --- | --- | --- |
| Planner 意图识别和步骤规划 | 姜楠 | 检查返回 `plan.workflow` 和 `plan.steps[].expert`。 |
| reverse_expert 节点和工作流集成 | 柯婧怡 | 检查 `reverse` 步骤是否被执行，并确认状态传递到 Analyze/Report。 |
| Execution 命令拼接和输出捕获 | 宋家硕 | 检查 `execution_results` 中的 command/stdout/stderr/exit_code/success。 |
| 沙箱工具可用性和输出解析器 | 胡文芳 | 检查 rizin、ghidra、strace、john 的可用性和解析结果。 |
| 测试用例和前端展示 | 黄宇轩 | 使用前端 REV 用例进行端到端验收并记录结果。 |
