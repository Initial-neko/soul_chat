"""
LLM 模块测试

测试前需要配置环境变量：
- DEEPSEEK_API_KEY: DeepSeek API 密钥

运行方式：
    uv run python -m pytest tests/test_llm.py -v
或：
    uv run python tests/test_llm.py
"""

import os
import sys
from pathlib import Path

# 确保可以导入 core 模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm import LLMClient, create_llm_client
from memory.window_memory import WindowMemory


def test_llm_basic():
    """测试 LLM 基础对话功能"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("⚠️ 跳过测试: 未设置 DEEPSEEK_API_KEY")
        return

    client = LLMClient()
    response = client.chat("你好呀，今天过得怎么样？")
    print(f"🤖 回复: {response}")
    assert response, "回复不应为空"
    print("✓ LLM 基础对话测试通过")


def test_llm_with_history():
    """测试 LLM 带历史记录的对话"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("⚠️ 跳过测试: 未设置 DEEPSEEK_API_KEY")
        return

    client = LLMClient()
    memory = WindowMemory()

    # 第一轮对话
    response1 = client.chat("我今天工作有点累", memory.get_history())
    print(f"🤖 第一轮回复: {response1}")
    memory.add("user", "我今天工作有点累")
    memory.add("assistant", response1)

    # 第二轮对话
    response2 = client.chat("有什么放松的方式吗？", memory.get_history())
    print(f"🤖 第二轮回复: {response2}")
    print(f"📜 历史记录: {memory.get_history()}")
    assert response2, "回复不应为空"
    print("✓ LLM 带历史记录测试通过")


def test_llm_stream():
    """测试 LLM 流式输出"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("⚠️ 跳过测试: 未设置 DEEPSEEK_API_KEY")
        return

    client = LLMClient()
    print("🤖 流式回复: ", end="")

    full_response = ""
    for chunk in client.stream_chat("给我讲个笑话"):
        print(chunk, end="", flush=True)
        full_response += chunk
    print()  # 换行

    assert full_response, "流式回复不应为空"
    print("✓ LLM 流式输出测试通过")


def test_memory():
    """测试记忆模块"""
    memory = WindowMemory(window_size=3)

    memory.add("user", "你好")
    memory.add("assistant", "你好呀")
    memory.add("user", "今天天气真好")
    memory.add("assistant", "是呀，很适合出去走走呢")

    # 添加第5条消息，触发窗口裁剪
    memory.add("user", "我们去公园吧")

    history = memory.get_history()
    print(f"📜 历史记录: {history}")
    assert len(history) == 3, f"窗口大小应为3，实际为 {len(history)}"
    print("✓ 记忆模块测试通过")


def test_factory():
    """测试工厂函数"""
    client = create_llm_client()
    assert client.model == "deepseek-chat"
    print("✓ 工厂函数测试通过")


if __name__ == "__main__":
    print("=" * 50)
    print("LLM 模块测试")
    print("=" * 50)

    test_factory()
    test_memory()
    test_llm_basic()
    test_llm_with_history()
    test_llm_stream()

    print("=" * 50)
    print("所有测试通过！✅")
    print("=" * 50)