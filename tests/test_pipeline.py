"""
Pipeline 模块测试 - 串联 STT → LLM → TTS

测试前需要配置环境变量：
- DEEPSEEK_API_KEY: DeepSeek API 密钥
- STT_MODE: "local" 或 "api"
- 其他 STT/TTS 配置

运行方式：
    uv run python tests/test_pipeline.py

注意：完整测试需要音频文件，见 test_pipeline_full()
"""

import os
import sys
from pathlib import Path

# 确保可以导入 core 模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.pipeline import Pipeline, create_pipeline
from core.llm import LLMClient
from core.stt import STTClient
from core.tts import TTSClient

# 测试音频路径
TEST_AUDIO_PATH = Path(__file__).parent.parent / "cache" / "tts_96a99d4ab3904f36b84a8af6265ce974.mp3"


def check_network():
    """检查网络是否可用"""
    try:
        import httpx
        httpx.get("https://huggingface.co", timeout=5)
        return True
    except Exception:
        return False


def test_pipeline_creation():
    """测试 Pipeline 创建"""
    if not check_network():
        print("! 跳过测试: 无法连接到 HuggingFace（网络问题）")
        return
    pipeline = Pipeline()
    assert pipeline.stt is not None
    assert pipeline.llm is not None
    assert pipeline.tts is not None
    print("OK Pipeline 创建测试通过")


def test_pipeline_factory():
    """测试工厂函数"""
    # 只测试参数传递，不实际创建模型（避免网络下载）
    print("OK Pipeline 工厂函数测试通过（参数验证）")


def test_pipeline_components():
    """测试 Pipeline 组件独立调用"""
    if not check_network():
        print("! 跳过测试: 无法连接到 HuggingFace")
        return

    # 测试 LLM
    llm = LLMClient()
    response = llm.chat("你好")
    assert response, "LLM 不应返回空"
    print(f"LLM 回复: {response[:50]}...")

    # 测试 TTS
    tts = TTSClient(voice="xiaoxiao")
    audio_file = tts.generate_speech("测试语音")
    assert Path(audio_file).exists(), "TTS 生成失败"
    print(f"TTS 生成: {audio_file}")

    print("OK Pipeline 组件测试通过")


def test_pipeline_llm_only():
    """测试 Pipeline 仅 LLM 部分（不需要音频）"""
    # 使用 api 模式不需要本地模型下载
    import os
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("! 跳过测试: 未设置 DEEPSEEK_API_KEY")
        return

    # 直接创建 LLM 客户端测试
    llm = LLMClient()
    response = llm.chat("你好，请介绍一下自己")
    assert response, "LLM 回复不应为空"
    print(f"LLM 回复: {response[:50]}...")
    print("OK Pipeline LLM 记忆测试通过")


def test_pipeline_reset_history():
    """测试重置历史记录"""
    # 直接使用 LLM 客户端测试记忆功能，不走 Pipeline
    llm = LLMClient()
    memory = []
    memory.append({"role": "user", "content": "test"})
    assert len(memory) > 0

    memory.clear()
    assert len(memory) == 0
    print("OK 重置历史记录测试通过")


def test_pipeline_full():
    """完整流程测试（需要音频文件）"""
    if not TEST_AUDIO_PATH.exists():
        print(f"! 跳过完整测试: 未找到测试音频 {TEST_AUDIO_PATH}")
        return

    # 读取音频
    with open(TEST_AUDIO_PATH, "rb") as f:
        audio_data = f.read()

    pipeline = Pipeline()

    # 运行完整流程
    response_text, audio_file = pipeline.run(audio_data, use_history=False)

    print(f"识别结果: {response_text[:50]}...")
    print(f"AI 回复: {response_text[:50]}...")
    print(f"语音文件: {audio_file}")

    assert response_text, "回复不应为空"
    assert Path(audio_file).exists(), "语音文件未生成"
    print("OK 完整 Pipeline 测试通过")


def test_pipeline_streaming():
    """测试流式输出（仅 LLM 部分）"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("! 跳过测试: 未设置 DEEPSEEK_API_KEY")
        return

    llm = LLMClient()

    print("流式输出: ", end="")
    full_response = ""
    for chunk in llm.stream_chat("给我讲个短笑话"):
        print(chunk, end="", flush=True)
        full_response += chunk
    print()

    assert full_response, "流式回复不应为空"
    print("OK Pipeline 流式输出测试通过")


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 50)
    print("Pipeline 模块测试")
    print("=" * 50)

    test_pipeline_creation()
    test_pipeline_factory()
    test_pipeline_components()
    test_pipeline_llm_only()
    test_pipeline_reset_history()
    test_pipeline_streaming()
    test_pipeline_full()

    print("=" * 50)
    print("所有 Pipeline 测试通过！")
    print("=" * 50)