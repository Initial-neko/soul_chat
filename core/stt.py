"""STT (Speech-to-Text) 模块 - 语音转文字"""

import io
import os
from pathlib import Path

import numpy as np
import soundfile as sf
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from openai import OpenAI

load_dotenv()


class STTClient:
    """语音转文字客户端，支持本地和 API 两种模式"""

    def __init__(
        self,
        mode: str = None,
        model: str = None,
        api_key: str = None,
    ):
        """
        初始化 STT 客户端

        Args:
            mode: 模式，"local" 使用 faster-whisper，"api" 使用 OpenAI Whisper API
            model: 模型名称
                  - local 模式：tiny/base/small/medium/large
                  - api 模式：whisper-1
            api_key: OpenAI API key (api 模式需要)
        """
        self.mode = mode or os.getenv("STT_MODE", "local")
        self.model = model or os.getenv("WHISPER_MODEL", "small")
        self.language = "zh"  # 默认中文

        if self.mode == "local":
            self._init_local()
        elif self.mode == "api":
            self._init_api(api_key)
        else:
            raise ValueError(f"Unknown STT mode: {self.mode}. Use 'local' or 'api'")

    def _init_local(self):
        """初始化本地 faster-whisper 模型"""
        # 强制使用 CPU（避免 CUDA 兼容性问题）
        self.whisper = WhisperModel(
            model_size_or_path=self.model,
            device="cpu",  # 强制使用 CPU
            compute_type="int8",
        )
        print(f"[STT] 本地模式已加载，模型: {self.model}")

    def _init_api(self, api_key: str = None):
        """初始化 OpenAI Whisper API 客户端"""
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "whisper-1"
        print(f"[STT] API 模式已加载，模型: {self.model}")

    def transcribe(self, audio_data: bytes | np.ndarray, sample_rate: int = 16000) -> str:
        """
        将语音转为文字

        Args:
            audio_data: 音频数据
                       - bytes: 原始音频字节 (WAV 格式)
                       - np.ndarray: 音频数组
            sample_rate: 采样率 (仅 bytes 模式需要)

        Returns:
            识别的文字
        """
        if self.mode == "local":
            return self._transcribe_local(audio_data, sample_rate)
        else:
            return self._transcribe_api(audio_data)

    def _transcribe_local(self, audio_data: bytes | np.ndarray, sample_rate: int = 16000) -> str:
        """使用本地 faster-whisper 转写"""
        # 如果是 bytes，先转为 numpy 数组
        if isinstance(audio_data, bytes):
            audio_array, sr = sf.read(io.BytesIO(audio_data))
            # 转换为 float32 并归一化
            if audio_array.dtype != np.float32:
                audio_array = audio_array.astype(np.float32)
            # 如果是立体声，取第一个通道
            if len(audio_array.shape) > 1:
                audio_array = audio_array[:, 0]
        else:
            audio_array = audio_data

        # 转写
        segments, info = self.whisper.transcribe(
            audio_array,
            language=self.language,
            beam_size=5,
            condition_on_previous_text=False,
        )

        # 合并所有片段
        text = "".join(segment.text for segment in segments)
        return text.strip()

    def _transcribe_api(self, audio_data: bytes) -> str:
        """使用 OpenAI Whisper API 转写"""
        # 将字节转为文件对象
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.wav"

        response = self.client.audio.transcriptions.create(
            model=self.model,
            file=audio_file,
            language="zh",  # 中文
            response_format="text",
        )

        return response.strip()


def create_stt_client(
    mode: str = None,
    model: str = None,
    api_key: str = None,
) -> STTClient:
    """创建 STT 客户端的工厂函数"""
    return STTClient(mode=mode, model=model, api_key=api_key)