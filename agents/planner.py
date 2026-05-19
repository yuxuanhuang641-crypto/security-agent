import json
from pathlib import Path
from typing import TypedDict, List, Dict, Any, Annotated
from operator import add
from langchain_core.messages import AnyMessage, AIMessage, SystemMessage, HumanMessage

# 导入我们在第一步里封装好的大模型客户端
from llm_client import llm


# 一、定义全局状态（State）
# 这部分数据结构需要和负责编排的 C 同学对齐
class AgentState(TypedDict):
    planner_messages: Annotated[list[AnyMessage], add]  # 规划智能体的消息队列 [cite: 16]
    recon_messages: Annotated[list[AnyMessage], add]  # 侦察专家的消息队列 [cite: 16]
    plan: list  # 存放拆解后的结构化计划列表 [cite: 16, 29]
    current_step: int  # 当前执行到第几步 [cite: 16, 29]


# 二、编写 Planner 节点函数
def Planner(state: AgentState) -> Dict[str, Any]:
    print("\n>>> 🧠 [Planner] 收到用户请求，正在规划安全任务...")

    # 1. 读取我们在第二步写好的提示词文档 [cite: 28]
    script_dir = Path(__file__).parent
    prompt_path = script_dir / "prompts" / "planner.md"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        print("❌ 错误：未找到 prompts/planner.md 文件，请检查路径是否正确！")
        return {}

    # 2. 组装消息发送给大模型 [cite: 31]
    messages = [
        SystemMessage(content=system_prompt),
        *state["planner_messages"]
    ]

    # 3. 调用大模型获取响应 [cite: 31]
    response = llm.invoke(messages)
    raw_content = response.content.strip()

    print(f"[Planner] 大模型原始返回内容:\n{raw_content}")

    try:
        # 4. 尝试解析大模型返回的 JSON 文本 [cite: 29]
        plan_data = json.loads(raw_content)
        sub_tasks = plan_data.get("sub_tasks", [])

        # 5. 准备要更新到全局 State 中的数据 [cite: 29]
        state_update = {
            "plan": sub_tasks,  # 将任务计划存入 state["plan"] [cite: 29]
            "current_step": 0,  # 设置当前步骤索引 current_step = 0 [cite: 29]
            "planner_messages": [AIMessage(content=raw_content)]
        }

        # 6. 提取第一步的指令，派发给对应的专家消息队列
        if sub_tasks:
            first_task = sub_tasks[0]
            expert_type = first_task.get("expert")
            instruction = first_task.get("instruction")

            # 本周核心：如果是 recon（侦察），就塞进侦察专家的消息队列中 [cite: 4, 30]
            if expert_type == "recon":
                state_update["recon_messages"] = [AIMessage(content=instruction)]  #
                print(f"✅ 成功将第一步指令派发给侦察专家 [recon_messages]: {instruction}")

            # 如果以后扩展了其他专家，可以在这里继续写 elif

        return state_update

    except json.JSONDecodeError:
        print("❌ 错误：大模型返回的不是合法的 JSON 格式，请检查提示词约束！")
        return {
            "planner_messages": [AIMessage(content="规划失败，大模型输出格式错误")]
        }


# 三、本地独立自测（不需要启动复杂的图，直接测试节点函数）
if __name__ == "__main__":
    # 模拟一个前端传进来的初始状态 [cite: 7]
    mock_initial_state = {
        "planner_messages": [HumanMessage(content="扫描 127.0.0.1 的 1100 端口")],  # [cite: 7]
        "recon_messages": [],
        "plan": [],
        "current_step": 0
    }

    # 直接运行我们的 Planner 节点，看看它的产出
    result = Planner(mock_initial_state)

    print("\n>>> 📊 [测试结果] Planner 节点执行完毕，返回的状态更新包为:")
    print(json.dumps(result, ensure_ascii=False, indent=2))