"""
TTS 模块测试

测试前需要配置环境变量：
- 无需 API key，edge-tts 免费

运行方式：
    uv run python tests/test_tts.py
"""

import os
import sys
from pathlib import Path

# 确保可以导入 core 模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tts import TTSClient, create_tts_client


def test_tts_basic():
    """测试 TTS 基础功能"""
    tts = TTSClient(voice="xiaoxiao")
    text = "你好，我是 Soul Chat，很高兴认识你！"

    audio_file = tts.generate_speech(text)

    assert audio_file, "生成的音频文件路径不应为空"
    assert Path(audio_file).exists(), f"音频文件不存在: {audio_file}"
    assert Path(audio_file).stat().st_size > 0, "音频文件不应为空"

    print(f"OK TTS 基础测试通过，生成文件: {audio_file}")


def test_tts_different_voices():
    """测试不同语音"""
    voices = ["xiaoxiao", "xiaoyi", "yunxi", "yunyang"]

    for voice in voices:
        tts = TTSClient(voice=voice)
        audio_file = tts.generate_speech("测试语音")

        assert Path(audio_file).exists(), f"语音 {voice} 生成失败"
        print(f"OK 语音 {voice} 测试通过")


def test_tts_rate_pitch():
    """测试语速和语调调节"""
    tts = TTSClient(voice="xiaoxiao", rate="+10%", pitch="+5Hz", volume="+0%")
    audio_file = tts.generate_speech("测试语速和语调")

    assert Path(audio_file).exists(), "带语速语调参数的测试失败"
    print("OK TTS 语速语调测试通过")


def test_tts_cache():
    """测试缓存功能"""
    text = "测试缓存功能"
    tts = TTSClient(voice="xiaoxiao")

    # 第一次生成
    file1 = tts.generate_speech(text, use_cache=True)
    size1 = Path(file1).stat().st_size

    # 第二次生成相同文本（应使用缓存）
    file2 = tts.generate_speech(text, use_cache=True)
    size2 = Path(file2).stat().st_size

    assert file1 == file2, "相同文本应返回相同缓存文件"
    assert size1 == size2, "缓存文件大小应一致"
    print("OK TTS 缓存测试通过")


def test_tts_no_cache():
    """测试不使用缓存"""
    tts = TTSClient(voice="xiaoxiao")
    text = "测试不缓存"

    file1 = tts.generate_speech(text, use_cache=False)
    file2 = tts.generate_speech(text, use_cache=False)

    # 不使用缓存时，每次应生成不同文件
    assert file1 != file2, "不使用缓存时应生成不同文件"
    print("OK TTS 不使用缓存测试通过")


def test_factory():
    """测试工厂函数"""
    client = create_tts_client(voice="xiaoyi")
    assert client.voice == "zh-CN-XiaoyiNeural"
    print("OK 工厂函数测试通过")


def test_get_available_voices():
    """测试获取可用语音列表"""
    tts = TTSClient()
    voices = tts.get_available_voices()

    assert "xiaoxiao" in voices
    assert "xiaoyi" in voices
    assert len(voices) >= 4
    print(f"OK 可用语音列表: {list(voices.keys())}")


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 50)
    print("TTS 模块测试")
    print("=" * 50)

    test_factory()
    test_get_available_voices()
    test_tts_basic()
    test_tts_different_voices()
    test_tts_rate_pitch()
    test_tts_cache()
    test_tts_no_cache()

    print("=" * 50)
    print("所有 TTS 测试通过！")
    print("=" * 50)