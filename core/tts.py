"""TTS (Text-to-Speech) 模块 - 文字转语音"""

import asyncio
import os
import uuid
from pathlib import Path

import edge_tts
from dotenv import load_dotenv

load_dotenv()

# 默认缓存目录
CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


class TTSClient:
    """文字转语音客户端，使用 Microsoft Edge TTS"""

    # 可用的中文语音列表
    VOICES = {
        # 女声
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",
        "xiaoyi": "zh-CN-XiaoyiNeural",
        # 男声
        "yunxi": "zh-CN-YunxiNeural",
        "yunyang": "zh-CN-YunyangNeural",
        # 粤语
        "xiaoxiao_yue": "zh-HK-XiaoxiaoNeural",
    }

    def __init__(
        self,
        voice: str = None,
        rate: str = "+0%",  # 语速调整: +50% 到 -50%
        pitch: str = "+0Hz",  # 语调���整
        volume: str = "+0%",  # 音量调整
    ):
        """
        初始化 TTS 客户端

        Args:
            voice: 语音名称，可选值: xiaoxiao, xiaoyi, yunxi, yunyang, xiaoxiao_yue
                   或直接使用 edge-tts 的语音名称如 zh-CN-XiaoxiaoNeural
            rate: 语速调整，格式如 "+10%" 或 "-10%"
            pitch: 语调调整，格式如 "+10Hz" 或 "-10Hz"
            volume: 音量调整，格式如 "+10%" 或 "-10%"
        """
        voice = voice or os.getenv("TTS_VOICE", "xiaoxiao")

        # 如果是简短名称，转换为完整语音名称
        if voice in self.VOICES:
            self.voice = self.VOICES[voice]
        else:
            self.voice = voice

        self.rate = rate
        self.pitch = pitch
        self.volume = volume

    async def _generate_async(self, text: str, output_file: str) -> str:
        """
        异步生成语音文件

        Args:
            text: 要转换的文本
            output_file: 输出文件路径

        Returns:
            生成的文件路径
        """
        # 创建communicate对象，设置语音、语速、语调、音量
        communicate = edge_tts.Communicate(
            text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch,
            volume=self.volume,
        )

        # 保存为音频文件
        await communicate.save(output_file)
        return output_file

    def generate_speech(
        self,
        text: str,
        output_file: str = None,
        use_cache: bool = True,
    ) -> str:
        """
        生成语音文件（同步版本）

        Args:
            text: 要转换的文本
            output_file: 输出文件路径，默认自动生成
            use_cache: 是否使用缓存（相同文本返回缓存文件）

        Returns:
            生成的文件路径
        """
        if not text:
            raise ValueError("Text cannot be empty")

        # 生成缓存键（使用文本的hash）
        if use_cache:
            cache_key = str(hash(text))[:16]
            default_file = str(CACHE_DIR / f"tts_{cache_key}.mp3")
        else:
            default_file = str(CACHE_DIR / f"tts_{uuid.uuid4().hex}.mp3")

        output_file = output_file or default_file

        # 如果文件已存在，直接返回
        if use_cache and Path(output_file).exists():
            return output_file

        # 异步执行
        asyncio.run(self._generate_async(text, output_file))
        return output_file

    async def _generate_streaming_async(self, text: str):
        """
        异步流式生成语音（用于实时播放）

        Args:
            text: 要转换的文本

        Yields:
            音频数据块
        """
        communicate = edge_tts.Communicate(
            text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch,
            volume=self.volume,
        )

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    def generate_streaming(self, text: str):
        """
        流式生成语音（用于实时播放）

        Args:
            text: 要转换的文本

        Yields:
            音频数据块
        """
        async def run():
            async for chunk in self._generate_streaming_async(text):
                yield chunk

        # 返回异步生成器
        return run()

    def get_available_voices(self) -> dict:
        """获取可用的语音列表"""
        return self.VOICES.copy()


def create_tts_client(
    voice: str = None,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
) -> TTSClient:
    """创建 TTS 客户端的工厂函数"""
    return TTSClient(voice=voice, rate=rate, pitch=pitch, volume=volume)