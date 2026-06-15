# security-agent

中国大学生信息安全大赛作品赛项目。

## 项目简介

本项目目标是实现一个面向授权安全场景的自主安全智能体，支持任务规划、专家路由、工具执行、结果分析、报告生成和前端展示等能力。

系统仅用于授权靶场、本地测试环境、安全运维辅助、应急响应分析、代码审计辅助和教学演示，不用于未授权攻击。

## 第一周目标

第一周目标是搭建最小可用的多智能体工作流骨架：

用户输入任务 -> 规划智能体生成结构化任务计划 -> LangGraph 根据计划路由到对应专家智能体 -> 侦察、验证、分析、报告等专家节点处理 -> 执行节点调用安全工具或沙箱执行 -> 前端展示执行状态、执行结果、分析摘要和最终报告。

## 目录结构

- `agents/`：智能体节点。
- `backend/`：后端接口。
- `frontend/`：前端界面。
- `knowledge_base/`：AI 安全审计知识库模板。
- `docs/knowledge_base_coverage_matrix.md`：知识库覆盖矩阵，记录 OWASP/ATLAS 映射、目标接口、影响分和优先级。
- `prompts/`：提示词模板。
- `sandbox/`：工具执行与沙箱。
- `tests/`：测试用例。
- `docs/`：接口文档、交付说明和进展记录。
- `AGENTS.md`：仓库级 AI 开发规范。

## E 模块说明

当前 E 模块负责分析、报告、前端展示和测试验收辅助：

- `agents/analyze_expert.py`：分析专家最小可用节点，从 `state["execution_result"]` 中读取工具输出，生成结构化 `analysis_result`。
- `agents/report_expert.py`：报告专家最小可用节点，根据用户输入、执行命令、执行结果和分析摘要生成 Markdown `final_report`。
- `frontend/app.py`：Streamlit v2 接口测试前端，向后端 `POST /task` 发送请求，并展示请求体、接口状态、计划、工具执行结果和最终报告。
- `tests/test_cases.md`：第一周联调测试用例。
- `tests/knowledge_base_test_cases.md`：知识库模板验证用例。
- `docs/api_contract.md`：与 FastAPI 后端和 LangGraph 状态流对齐的字段约定。
- `docs/e_task_delivery.md`：E 模块交付说明。

## 前端运行方式

```bash
pip install -r requirements.txt
streamlit run frontend/app.py
```

启动后在浏览器中打开 Streamlit 输出的本地地址即可查看测试界面。默认后端接口为 `http://127.0.0.1:8008/task`。

## 当前注意事项

- 当前前端为 v2 后端接口测试版本，不直接执行本地命令；需要先启动后端服务。
- 当前分析专家和报告专家为最小可用占位实现。
- 后续需要继续和 FastAPI 后端、LangGraph 工作流、执行沙箱输出对接。
- 所有安全测试仅限授权环境、本地靶场、测试数据和教学演示。
- E 模块不直接执行系统命令，也不实现真实攻击能力。
