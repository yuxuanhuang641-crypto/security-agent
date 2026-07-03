# 逆向分析场景端到端测试用例

本文档用于黄宇轩负责的逆向分析场景验收。当前只定义端到端测试用例和前端查看方式，不实现 `reverse_expert`、不修改工作流、不直接执行逆向工具。所有测试仅限授权样本、隔离沙箱和教学/比赛演示环境。

默认接口仍为：

```text
POST http://127.0.0.1:8008/task
```

统一请求体：

```json
{
  "input_text": "逆向分析任务描述",
  "thread_id": "demo-reverse-basic"
}
```

| 编号 | 测试名称 | 用户输入 | thread_id | 涉及模块 | 预期 Planner 结果 | 预期工具 | 预期 Analyze 判断 | 前端查看方式 | 当前依赖状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REV-001 | 基础二进制信息分析 | 我已获得授权，请对隔离沙箱中的样本 `/samples/reverse/hello_elf` 进行基础逆向分析。请规划 `reverse -> analyze -> report` 链路，优先使用 rizin 或 ghidra，提取文件类型、架构、入口点、关键函数和字符串摘要，不执行样本的破坏性行为。 | `demo-reverse-basic` | 前端、Planner、ReverseExpert、Execution、AnalyzeExpert、ReportExpert | `plan.workflow` 为 `reverse-analysis` 或类似名称；`plan.steps[].expert` 至少包含 `reverse`、`analyze`、`report`；reverse 步骤带 `analysis_depth=basic`。 | `rizin` 或 `ghidra` | 能从工具输出中整理文件格式、架构、入口点、函数列表、字符串摘要；未发现高危行为时给出低风险或信息性结论。 | 在前端选择 `REV-001 基础二进制信息分析`，检查请求体、`plan`、`execution_results` 和 `final_report`。 | 依赖 reverse 节点、逆向工具模板、沙箱样本路径和输出解析器。 |
| REV-002 | 深度危险函数分析 | 我已获得授权，请对隔离沙箱中的样本 `/samples/reverse/suspicious_elf` 进行深度逆向分析。请规划 `reverse -> analyze -> report` 链路，重点关注 `system`、`exec`、`strcpy`、`memcpy`、`socket`、`connect` 等危险函数，以及 NX、PIE、RELRO 等安全属性缺失。 | `demo-reverse-deep` | 前端、Planner、ReverseExpert、Execution、AnalyzeExpert、ReportExpert | `plan.steps[].expert` 应路由到 `reverse`；reverse 步骤带 `analysis_depth=deep`；分析步骤说明需要研判危险函数和安全属性。 | `ghidra` 或 `rizin` | 能识别危险函数、可疑调用链、字符串线索、导入表和安全属性缺失；报告中区分证据、风险和建议。 | 在前端选择 `REV-002 深度危险函数分析`，重点查看 `plan.steps`、工具输出和报告中的危险函数判断。 | 依赖 ghidra/rizin 可用性、深度分析输出格式和 Analyze 规则更新。 |
| REV-003 | 动态行为跟踪分析 | 我已获得授权，请在隔离沙箱中对样本 `/samples/reverse/io_trace_sample` 进行动态行为跟踪分析。请规划 `reverse -> execution -> analyze -> report` 链路，优先使用 strace 捕获文件访问、进程行为、网络尝试和异常退出信息。 | `demo-reverse-trace` | 前端、Planner、ReverseExpert、Execution、AnalyzeExpert、ReportExpert | `plan.workflow` 应体现动态逆向或行为跟踪；步骤中出现 `reverse` 或 execution 工具调用；参数包含沙箱样本路径和 trace 类型。 | `strace` | 能总结 `open/read/write/execve/connect` 等 syscall，判断是否存在异常文件访问、进程派生、网络尝试或异常退出。 | 在前端选择 `REV-003 动态行为跟踪分析`，查看 `execution_results` 中的 syscall 输出和 `final_report`。 | 依赖沙箱安全运行策略、strace 安装和输出解析器。 |
| REV-004 | 哈希/口令样本分析 | 我已获得授权，请对隔离测试文件 `/samples/reverse/hash_sample.txt` 进行哈希样本分析。请规划 `reverse -> analyze -> report` 链路，优先使用 john 处理测试哈希，并在报告中明确该用例只允许处理教学样本，不接触真实账户或真实口令数据。 | `demo-reverse-hash` | 前端、Planner、ReverseExpert、Execution、AnalyzeExpert、ReportExpert | Planner 应识别为逆向/口令样本分析场景，路由到 `reverse`；参数中保留测试文件路径和合规边界说明。 | `john` | 能识别哈希格式、测试结果和失败原因；报告必须说明仅限授权样本，不输出真实账户或真实口令数据。 | 在前端选择 `REV-004 哈希/口令样本分析`，查看工具输出是否进入 Analyze 和 Report。 | 依赖 john 可用性、测试哈希样本和合规输出约束。 |

## 验收重点

- Planner 能识别逆向分析意图，并生成包含 `reverse` 专家的步骤。
- Execution 能把逆向工具输出写入 `execution_results` 或内部 `execution_result`。
- AnalyzeExpert 能根据逆向输出研判危险函数、安全属性缺失、动态行为或哈希分析结果。
- ReportExpert 能生成 Markdown 报告，包含任务概述、工具动作、关键证据、风险判断、处置建议和合规说明。
- 前端不伪造成成功；后端未接入 reverse 时，应展示真实失败信息或后端返回的错误。

## 后续对接人

- Planner 意图识别与步骤规划：姜楠。
- reverse_expert 节点和工作流集成：柯婧怡。
- Execution 命令拼接和输出捕获：宋家硕。
- 沙箱工具可用性和输出解析器：胡文芳。
- 端到端测试用例和前端展示验证：黄宇轩。
