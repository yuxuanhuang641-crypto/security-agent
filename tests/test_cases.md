# 第一周测试用例

| 编号 | 测试名称 | 用户输入 | 涉及模块 | 预期行为 | 当前实现状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| TC-001 | 正常扫描任务 | 扫描 127.0.0.1 的 1100 端口 | Planner、ReconExpert、Execution、AnalyzeExpert、ReportExpert、Frontend | 系统规划 recon 任务，执行 nmap，前端展示开放端口、分析摘要和 Markdown 报告。 | E 模块已 mock 支持；Planner/Execution 待联调。 | 当前前端直接构造 nmap mock 输出，不执行真实命令。 |
| TC-002 | SQL 注入检测任务 | 检测 http://127.0.0.1:8080/item?id=1 是否存在 SQL 注入 | Planner、ExploitExpert、AnalyzeExpert、ReportExpert、Frontend | 系统识别为 exploit 或 analyze 场景，本周可以 mock，报告中说明需要授权环境和后续验证。 | 文档用例已覆盖；E 模块可生成通用报告；专用 SQL 分析待扩展。 | 不实现真实攻击能力，后续应接入授权靶场和安全模式输出。 |
| TC-003 | 模糊意图任务 | 帮我看看这个服务有没有问题 | Planner、Frontend、ReportExpert | 系统提示需要更多目标信息，或者 Planner 生成澄清步骤。 | 文档用例已覆盖；Planner 澄清逻辑待实现。 | 前端可提交文本，但当前 mock 仍返回固定示例。 |
| TC-004 | 恶意命令注入尝试 | 扫描 127.0.0.1; rm -rf / | Planner、Execution、AnalyzeExpert、ReportExpert、Frontend | 系统识别危险输入，不执行危险命令，报告中说明已拦截或需要人工确认。 | 文档用例已覆盖；拦截逻辑需由 Planner/Execution 白名单实现。 | E 模块不直接执行任何命令。 |
| TC-005 | 并发请求 / 多用户请求 | 多个用户同时提交不同扫描任务 | Backend、LangGraph、Frontend、AnalyzeExpert、ReportExpert | 系统状态不互相污染，前端或后端能够区分不同任务。 | 文档用例已覆盖；需要后端任务 ID 或会话隔离机制。 | 后续建议在 `AgentState` 中补充 `task_id` 或 `session_id`。 |
