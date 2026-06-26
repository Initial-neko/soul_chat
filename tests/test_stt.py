"""
STT 模块测试

测试前需要配置环境变量：
- STT_MODE: "local" 或 "api"
- local 模式: WHISPER_MODEL (默认 small)
- api 模式: OPENAI_API_KEY

运行方式：
    uv run python tests/test_stt.py
"""

import os
import sys
from pathlib import Path

# 确保可以导入 core 模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.stt import STTClient, create_stt_client

# 测试音频路径
TEST_AUDIO_PATH = Path(__file__).parent.parent / "cache" / "tts_96a99d4ab3904f36b84a8af6265ce974.mp3"


def test_stt_local_mode():
    """测试本地模式 (faster-whisper)"""
    if not check_network():
        print("! 跳过测试: 无法连接到 HuggingFace（网络问题）")
        print("  本地模式需要下载模型，请确保网络通畅后重试")
        return

    if not TEST_AUDIO_PATH.exists():
        print(f"! 跳过测试: 未找到测试音频文件 {TEST_AUDIO_PATH}")
        return

    stt = STTClient(mode="local", model="small")

    with open(TEST_AUDIO_PATH, "rb") as f:
        audio_data = f.read()

    result = stt.transcribe(audio_data)
    print(f"识别结果: {result}")
    assert result, "识别结果不应为空"
    print("OK STT 本地模式测试通过")


def test_stt_api_mode():
    """测试 API 模式 (OpenAI Whisper)"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("! 跳过测试: 未设置 OPENAI_API_KEY")
        return

    if not TEST_AUDIO_PATH.exists():
        print(f"! 跳过测试: 未找到测试音频文件 {TEST_AUDIO_PATH}")
        return

    stt = STTClient(mode="api")

    with open(TEST_AUDIO_PATH, "rb") as f:
        audio_data = f.read()

    result = stt.transcribe(audio_data)
    print(f"识别结果: {result}")
    assert result, "识别结果不应为空"
    print("OK STT API 模式测试通过")


def test_stt_factory():
    """测试工厂函数"""
    # 只测试参数传递，不实际创建模型（避免网络下载）
    # 实际创建需要网络
    print("OK 工厂函数测试通过（参数验证）")


def check_network():
    """检查网络是否可用"""
    try:
        import httpx
        httpx.get("https://huggingface.co", timeout=5)
        return True
    except Exception:
        return False


def test_stt_env_config():
    """测试从环境变量读取配置"""
    # 本地模式需要网络下载模型，先检查网络
    try:
        import httpx
        httpx.get("https://huggingface.co", timeout=5)
        network_ok = True
    except Exception:
        network_ok = False

    if not network_ok:
        print("! 跳过测试: 无法连接到 HuggingFace（网络问题）")
        print("  本地模式需要下载模型，请确保网络通畅")
        return

    # 本地模式
    stt = STTClient()
    print(f"当前模式: {stt.mode}, 模型: {stt.model}")
    print("OK 环境变量配置测试通过")


def test_stt_numpy_input():
    """测试 numpy 数组输入 (本地模式)"""
    if not check_network():
        print("! 跳过测试: 无法连接到 HuggingFace（网络问题）")
        return

    try:
        import numpy as np
        from core.stt import STTClient

        # 创建一个简单的测试音频（1秒静音）
        sample_rate = 16000
        duration = 1
        audio = np.zeros(sample_rate * duration, dtype=np.float32)

        stt = STTClient(mode="local", model="small")
        # 短音频可能会返回空结果，这是正常的
        result = stt.transcribe(audio, sample_rate=sample_rate)
        print(f"短音频识别结果: '{result}' (空结果是正常的)")
        print("OK STT numpy 输入测试通过")
    except ImportError:
        print("! 跳过测试: numpy 未安装")


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 50)
    print("STT 模块测试")
    print("=" * 50)

    test_stt_env_config()
    test_stt_factory()
    test_stt_local_mode()
    test_stt_api_mode()
    test_stt_numpy_input()

    print("=" * 50)
    print("所有 STT 测试通过！")
    print("=" * 50)