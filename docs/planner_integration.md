# 规划智能体对接说明

本文档用于说明负责规划部分的同学提供的 `Planner(信安版).md` 和 `Planner(信安版).py` 如何与当前 E 模块对接。

## 1. 这个模块是做什么的

规划智能体负责把用户的一句话安全审计需求，转换成后端可以直接执行和路由的结构化计划。

它的核心流程是：

```text
用户输入
-> 判断任务是否属于授权安全审计
-> 识别风险类型
-> 选择工作流
-> 拆分执行步骤
-> 分配给 recon / exploit / analyze / report 专家
-> 输出纯 JSON 计划
```

这里的 `exploit` 表示授权安全测试阶段，不表示真实漏洞利用。规划智能体本身不执行命令，也不攻击目标系统，只负责产出计划。

## 2. 规划智能体的输入

后端仍然可以沿用当前 `/task` 接口：

```json
{
  "input_text": "我已获得授权，请对目标 AI 助手进行综合安全审计，重点检查提示词注入和敏感信息泄露风险。",
  "thread_id": "demo"
}
```

`input_text` 会进入 `planner_messages`，作为规划智能体的用户输入。

## 3. 规划智能体的输出

规划智能体要求只输出合法 JSON，推荐结构如下：

```json
{
  "workflow": "comprehensive-ai-audit",
  "steps": [
    {
      "step_id": 1,
      "expert": "recon",
      "instruction": "收集目标 AI 助手的接口能力、认证方式和支持功能。",
      "template_id": null,
      "params": {
        "target": "demo-ai-assistant",
        "prompt": null,
        "session_id": "demo",
        "extra_args": {}
      }
    },
    {
      "step_id": 2,
      "expert": "exploit",
      "instruction": "使用提示词注入检测模板进行低风险安全审计。",
      "template_id": "PI-001",
      "params": {
        "target": "demo-ai-assistant",
        "prompt": "授权测试用提示词注入样本",
        "session_id": "demo",
        "extra_args": {}
      }
    },
    {
      "step_id": 3,
      "expert": "analyze",
      "instruction": "分析模型响应，提取证据并判断风险等级。",
      "template_id": null,
      "params": {
        "target": "demo-ai-assistant",
        "prompt": null,
        "session_id": "demo",
        "extra_args": {}
      }
    },
    {
      "step_id": 4,
      "expert": "report",
      "instruction": "汇总审计结果并输出安全评估报告。",
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

## 4. 与当前 E 模块怎么接

当前 E 模块不需要直接修改规划智能体核心逻辑，只需要按字段展示和记录即可。

对接关系如下：

| 阶段 | 对接方式 | 当前 E 模块作用 |
| --- | --- | --- |
| 用户提交任务 | 前端继续发送 `input_text` 和 `thread_id` | `frontend/app.py` 负责展示请求体 |
| 规划智能体输出计划 | 后端返回 `plan.workflow` 和 `plan.steps` | 前端直接展示完整 `plan` |
| 专家节点执行 | 后端根据 `expert` 路由到对应专家 | E 模块关注 `analyze` 和 `report` 阶段 |
| 执行结果返回 | 后端写入 `execution_result` 或响应中的 `execution_results` | 前端展示工具或检测结果 |
| 分析和报告 | 分析专家提取证据，报告专家生成 Markdown | 前端展示 `final_report` |

## 5. 需要后端同学注意的字段

规划智能体代码中目前有一个细节建议调整：

```python
plan = {"steps": steps}
```

建议保留 `workflow`：

```python
plan = {
    "workflow": plan_data.get("workflow"),
    "steps": steps,
}
```

这样前端和报告里可以看到本次选择的是 `prompt-injection-test`、`sensitive-leakage-test` 还是 `comprehensive-ai-audit`。

## 6. 对接完成后的用处

对接完成后，系统会从“用户输入一句话”升级成“可解释、可路由、可展示的多智能体任务流”。

具体价值是：

- 用户不用手动指定每一步，规划智能体会自动拆成 `recon / exploit / analyze / report`。
- 后端可以根据 `expert` 字段把任务路由给对应专家。
- 前端可以清楚展示本次审计采用了哪个工作流、每一步做什么。
- 分析和报告阶段可以引用 `workflow`、`template_id`、`params`，让最终报告更清楚。
- 对模糊任务或未授权任务，规划智能体可以先澄清或拒绝，避免直接进入执行阶段。

## 7. 当前最小对接状态

本次 E 侧已经完成以下准备：

- 接口文档补充了 AI 安全审计规划字段。
- 前端测试用例加入了规划智能体相关输入。
- 测试用例文档加入了 AI 安全审计场景。
- 前端已经能展示后端返回的完整 `plan`，因此能兼容带 `workflow` 和 `template_id` 的计划结构。

