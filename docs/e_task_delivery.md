# E 模块交付说明

## 1. 模块定位

E 模块负责安全智能体链路中的分析、报告、前端展示和测试验收辅助，主要承接执行节点之后的结果整理工作。

- 分析专家：接收工具执行结果，对结果进行结构化分析，提取关键信息、风险等级、证据和建议。
- 报告专家：根据用户输入、执行命令、执行结果、分析摘要生成 Markdown 格式安全分析报告。
- 前端：提供极简任务输入和结果展示界面。
- 测试：提供至少 5 个测试用例，辅助全链路验收。
- 文档：记录接口约定、字段含义和联调方式。

## 2. 当前实现范围

本周目标是最小可用版本，不追求完整安全分析能力，也不实现真实攻击能力。

当前分析专家可以根据模拟或后端返回的执行结果做基础规则分析，例如识别 `open`、`filtered`、`closed`、执行失败和空输出等情况。

当前报告专家可以生成结构化 Markdown 报告，包含任务概述、执行动作、执行结果摘要、分析结论、证据链、处置建议和合规说明。

当前前端已经改为 v2 接口测试前端，可以向后端 `POST /task` 发送请求，并展示请求体、接口状态、计划、执行结果、最终报告和错误信息。

当前测试用例用于指导联调和验收，不一定全部自动化。

## 3. 文件清单

| 文件 | 用途 |
| --- | --- |
| `AGENTS.md` | 仓库级 AI 开发规范，说明项目背景、开发边界、代码规范和文档规范。 |
| `agents/analyze_expert.py` | 分析专家最小可用节点，基于模拟/规则生成 `analysis_result`。 |
| `agents/report_expert.py` | 报告专家最小可用节点，根据 `state` 生成 Markdown `final_report`。 |
| `frontend/app.py` | Streamlit v2 接口测试前端，调用后端 `POST /task` 并展示返回结果；已加入逆向分析 REV 联调用例入口。 |
| `requirements.txt` | 当前前端演示所需依赖。 |
| `.gitignore` | 忽略 Python 缓存、虚拟环境和本地编辑器目录，并转为 UTF-8 以便 Git 正常识别。 |
| `docs/e_task_delivery.md` | E 模块交付说明，便于队友联调和后续比赛报告整理。 |
| `docs/api_contract.md` | E 模块与后端、LangGraph 状态流的接口字段约定。 |
| `docs/planner_integration.md` | 规划智能体对接说明，解释 AI 安全审计版 Planner 的输入、输出和 E 侧展示方式。 |
| `knowledge_base/ai_safety_knowledge_base.json` | AI 安全审计知识库模板，包含 `score` 影响分、OWASP/ATLAS 映射、目标接口、优先级标签和 OpenClaw 专项模板。 |
| `docs/knowledge_base_coverage_matrix.md` | 知识库覆盖矩阵，用于查看每个模板覆盖的安全框架、接口、影响分和优先级。 |
| `tests/knowledge_base_test_cases.md` | 知识库模板对应的人工验证用例，并记录 `score` 影响分字段验证方式。 |
| `tests/test_knowledge_base_schema.py` | 知识库结构校验脚本，验证字段完整性、模板 ID 唯一性、影响分字段、覆盖矩阵字段、多轮配置和清理要求。 |
| `tests/test_multi_turn_templates.py` | 多轮模板专项测试，验证多轮数量、轮次顺序、跨会话重置和证据要求。 |
| `docs/daily_progress.md` | 每日进展记录模板，并记录 Day 1 初始化内容。 |
| `tests/test_cases.md` | 联调测试用例文档，包含 v2 基础用例、AI 安全审计用例和逆向分析场景用例。 |
| `tests/reverse_e2e_test_cases.md` | 逆向分析场景端到端测试用例，覆盖基础分析、深度分析、动态跟踪和哈希样本分析。 |
| `docs/reverse_integration.md` | 逆向分析场景对接说明，记录 E 侧对 Planner、ReverseExpert、Execution、Analyze 和 Report 的联调期望。 |
| `README.md` | 项目简介、第一周目标、目录结构、E 模块说明和前端运行方式。 |

## 4. 与其他同学模块的对接方式

- 前端当前已经按 v2 后端的 `POST /task` 接口联调。
- 若后端接入 AI 安全审计版规划智能体，前端可直接展示 `plan.workflow`、`plan.steps` 和 `template_id`。
- 如果需要离线演示，可重新补充模拟数据模式，但默认不伪造后端成功结果。
- 分析专家和报告专家的函数可以作为 LangGraph 节点被注册。
- 输入输出都通过 `state` 字典传递。
- C 同学 FastAPI 后端当前返回 `status`、`plan`、`execution_results` 和 `final_report`，前端按字段展示。
- LangGraph 中建议在执行节点之后调用 `analyze_expert_node(state)`，再调用 `report_expert_node(state)`。
- 如果后端后续支持 SSE 或 WebSocket，前端可以从一次性结果展示升级为执行时间线展示。

## 5. 后续可扩展方向

- 接入真实执行节点输出。
- 接入大模型生成更自然的分析。
- 支持 Web 漏洞分析报告、应急响应报告、代码审计报告等不同模板。
- 增加导出 Markdown / PDF 的功能。
- 增加前端的执行时间线展示。
- 增加按工具类型区分的结果解析器，例如 `nmap`、`sqlmap` 安全模式输出、日志分析器和代码扫描器。
- 增加自动化单元测试，验证不同 `execution_result` 输入下的风险等级和报告内容。
