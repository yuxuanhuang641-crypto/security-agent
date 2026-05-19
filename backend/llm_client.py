import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 加载 .env 文件中的环境变量
load_dotenv()

# 获取 API Key
api_key = os.getenv("TONGYI_API_KEY")

if not api_key:
    raise ValueError("未找到 TONGYI_API_KEY，请检查 .env 文件是否配置正确！")

# 实例化大模型客户端（使用兼容 OpenAI 接口的方式调用通义千问）
# 这里的模型名 qwen3.5-plus 可以根据你们团队的实际申请情况调整
llm = ChatOpenAI(
    model="qwen-plus",  # 或者 qwen3.5-plus
    openai_api_key=api_key,
    openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.7, # 稍微带点随机性
)

# 下面是测试代码：只有当你直接运行这个文件时才会执行
if __name__ == "__main__":
    print("正在连接大模型，请稍候...")
    try:
        # 模拟给大模型发一条消息
        test_message = [HumanMessage(content="你好，请用一句话证明你在线。")]
        response = llm.invoke(test_message)
        print("✅ 连接成功！大模型回复：")
        print(response.content)
    except Exception as e:
        print(f"❌ 连接失败，错误信息：{e}")