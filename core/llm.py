from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()


class LLMClient:
    """DeepSeek LLM 客户端"""

    def __init__(self, model: str = "deepseek-chat"):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        self.model = model
        self._system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """加载系统提示词"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return "你是一个温暖的AI伴侣，善于倾听和陪伴。"

    def chat(self, user_message: str, history: list = None) -> str:
        """
        调用 LLM 生成回复

        Args:
            user_message: 用户当前消息
            history: 历史消息列表，每项为 {"role": "user"/"assistant", "content": "..."}

        Returns:
            LLM 回复文本
        """
        messages = [{"role": "system", "content": self._system_prompt}]

        # 添加历史消息
        if history:
            messages.extend(history)

        # 添加当前消息
        messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=500
        )

        return response.choices[0].message.content

    def stream_chat(self, user_message: str, history: list = None):
        """
        流式调用 LLM 生成回复

        Args:
            user_message: 用户当前消息
            history: 历史消息列表

        Yields:
            回复文本片段
        """
        messages = [{"role": "system", "content": self._system_prompt}]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=500,
            stream=True
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


def create_llm_client(model: str = "deepseek-chat") -> LLMClient:
    """创建 LLM 客户端的工厂函数"""
    return LLMClient(model=model)