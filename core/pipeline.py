"""Pipeline 模块 - 串联 STT → LLM → TTS"""

import os
from pathlib import Path

from dotenv import load_dotenv

from .llm import LLMClient
from .stt import STTClient
from .tts import TTSClient

load_dotenv()


class Pipeline:
    """语音对话 Pipeline，串联 STT → LLM → TTS"""

    def __init__(
        self,
        stt_client: STTClient = None,
        llm_client: LLMClient = None,
        tts_client: TTSClient = None,
    ):
        """
        初始化 Pipeline

        Args:
            stt_client: STT 客户端，默认创建本地模式
            llm_client: LLM 客户端，默认创建 DeepSeek
            tts_client: TTS 客户端，默认使用 edge-tts
        """
        self.stt = stt_client or STTClient()
        self.llm = llm_client or LLMClient()
        self.tts = tts_client or TTSClient()

        # 缓存目录
        self.cache_dir = Path(__file__).parent.parent / "cache"
        self.cache_dir.mkdir(exist_ok=True)

    def run(self, audio_data: bytes, use_history: bool = True) -> tuple[str, str]:
        """
        运行完整流程：音频 → 文字 → LLM 回复 → 语音

        Args:
            audio_data: 音频数据 (bytes)
            use_history: 是否使用对话历史

        Returns:
            (文字回复, 语音文件路径)
        """
        # Step 1: STT - 语音转文字
        user_text = self.stt.transcribe(audio_data)
        print(f"[Pipeline] 用户说: {user_text}")

        # Step 2: LLM 生成回复
        if use_history:
            response_text = self.llm.chat(user_text, self.llm_memory)
            # 更新记忆
            self.llm_memory.append({"role": "user", "content": user_text})
            self.llm_memory.append({"role": "assistant", "content": response_text})
        else:
            response_text = self.llm.chat(user_text)

        print(f"[Pipeline] AI 回复: {response_text}")

        # Step 3: TTS - 文字转语音
        audio_file = self.tts.generate_speech(response_text)
        print(f"[Pipeline] 语音已生成: {audio_file}")

        return response_text, audio_file

    def run_streaming(self, audio_data: bytes):
        """
        运行完整流程（流式 LLM，可选）

        Args:
            audio_data: 音频数据 (bytes)

        Yields:
            LLM 回复片段（用于实时显示）
        """
        # Step 1: STT
        user_text = self.stt.transcribe(audio_data)
        print(f"[Pipeline] 用户说: {user_text}")

        # Step 2: LLM 流式输出
        response_chunks = []
        for chunk in self.llm.stream_chat(user_text):
            response_chunks.append(chunk)
            yield chunk

        response_text = "".join(response_chunks)
        print(f"[Pipeline] AI 回复: {response_text}")

        # Step 3: TTS
        audio_file = self.tts.generate_speech(response_text)
        print(f"[Pipeline] 语音已生成: {audio_file}")

    def reset_history(self):
        """重置对话历史"""
        self.llm_memory = []

    @property
    def memory(self):
        """获取当前记忆（用于外部访问）"""
        if not hasattr(self, "llm_memory"):
            self.llm_memory = []
        return self.llm_memory


def create_pipeline(
    stt_mode: str = None,
    llm_model: str = None,
    tts_voice: str = None,
) -> Pipeline:
    """
    创建 Pipeline 的工厂函数

    Args:
        stt_mode: STT 模式，"local" 或 "api"
        llm_model: LLM 模型名称
        tts_voice: TTS 语音名称
    """
    stt = STTClient(mode=stt_mode) if stt_mode else STTClient()
    llm = LLMClient(model=llm_model) if llm_model else LLMClient()
    tts = TTSClient(voice=tts_voice) if tts_voice else TTSClient()

    return Pipeline(stt_client=stt, llm_client=llm, tts_client=tts)