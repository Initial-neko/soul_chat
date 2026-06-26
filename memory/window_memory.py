class WindowMemory:
    """滑动窗口记忆"""

    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.messages = []

    def add(self, role: str, content: str):
        """
        添加消息到记忆

        Args:
            role: "user" 或 "assistant"
            content: 消息内容
        """
        self.messages.append({"role": role, "content": content})
        self._trim()

    def _trim(self):
        """裁剪超过窗口大小的消息"""
        if len(self.messages) > self.window_size:
            # 保留 system 消息（如果有）和最近的消息
            system_msg = None
            if self.messages and self.messages[0]["role"] == "system":
                system_msg = self.messages[0]
                messages = self.messages[1:]
            else:
                messages = self.messages

            # 保留最近 window_size 条
            self.messages = messages[-self.window_size:]
            if system_msg:
                self.messages.insert(0, system_msg)

    def get_history(self) -> list:
        """获取历史消息（不含 system 提示词）"""
        # 过滤掉 system 消息，因为 LLM 调用时会单独添加
        return [m for m in self.messages if m["role"] != "system"]

    def clear(self):
        """清空记忆"""
        self.messages = []

    def __len__(self):
        return len(self.messages)

    def __repr__(self):
        return f"WindowMemory({len(self.messages)} messages)"