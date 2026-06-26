"""
Gradio WebUI 入口 - 情感陪伴聊天机器人
"""

import os

import gradio as gr
import numpy as np
from dotenv import load_dotenv

from core.llm import LLMClient
from core.stt import STTClient
from core.tts import TTSClient
from memory.window_memory import WindowMemory

load_dotenv()

# ==================== 全局单例 ====================
# 避免重复加载模型

stt_client = STTClient()
llm_client = LLMClient()
tts_client = TTSClient()
memory = WindowMemory(window_size=20)


# ==================== 核心处理函数 ====================

def process_audio(audio_input, history: list) -> tuple:
    """
    处理音频输入：STT → LLM → TTS

    Args:
        audio_input: gr.Audio 返回的 (sample_rate, data) 元组
        history: 对话历史

    Returns:
        (更新后的历史, 音频文件路径, 状态消息)
    """
    if audio_input is None:
        return history, None, "请先录音后再发送"

    try:
        sample_rate, audio_data = audio_input

        # Step 1: 音频格式转换
        if isinstance(audio_data, np.ndarray):
            if len(audio_data.shape) > 1:
                audio_data = audio_data[:, 0]  # 取左声道
            audio_data = audio_data.astype(np.float32)

        # Step 2: STT 语音转文字
        user_text = stt_client.transcribe(audio_data, sample_rate)

        if not user_text or user_text.strip() == "":
            return history, None, "未能识别语音，请重试"

        # Step 3: LLM 生成回复
        history_messages = memory.get_history()
        ai_response = llm_client.chat(user_text, history_messages)

        # 更新记忆
        memory.add("user", user_text)
        memory.add("assistant", ai_response)

        # Step 4: TTS 文字转语音
        audio_file = tts_client.generate_speech(ai_response)

        # Step 5: 更新 UI
        new_history = history + [(user_text, ai_response)]

        return new_history, audio_file, "处理完成"

    except Exception as e:
        print(f"[Error] 处理音频时出错: {e}")
        return history, None, f"处理出错: {str(e)}"


def clear_history():
    """清空对话历史"""
    memory.clear()
    return [], None, "对话历史已清空"


# ==================== Gradio 界面 ====================

def create_demo():
    """创建 Gradio 应用"""

    with gr.Blocks(
        title="Soul Chat - 情感陪伴聊天机器人",
        theme=gr.themes.Soft(),
    ) as demo:
        # 标题
        gr.Markdown("""
        # Soul Chat
        ### 情感陪伴聊天机器人

        点击麦克风录音，然后点击发送按钮与我对话吧！
        """)

        # 状态存储
        history_state = gr.State(value=[])

        with gr.Row():
            with gr.Column(scale=3):
                # 对话显示区
                chatbot = gr.Chatbot(
                    label="对话历史",
                    height=400,
                    bubble_full_width=False,
                )

            with gr.Column(scale=1):
                # 状态显示
                status_text = gr.Textbox(
                    label="状态",
                    interactive=False,
                    lines=2,
                )

        with gr.Row():
            # 音频输入（麦克风）
            audio_input = gr.Audio(
                label="点击录音",
                sources=["microphone"],
                type="numpy",
                format="wav",
            )

        with gr.Row():
            # 发送按钮
            submit_btn = gr.Button("发送", variant="primary", size="lg")

        with gr.Row():
            # 音频输出（播放 AI 回复）
            audio_output = gr.Audio(
                label="AI 回复语音",
                type="filepath",
            )

        with gr.Row():
            # 清空按钮
            clear_btn = gr.Button("清空对话历史", variant="secondary")

        # 事件绑定
        submit_btn.click(
            fn=process_audio,
            inputs=[audio_input, history_state],
            outputs=[chatbot, audio_output, status_text],
        )

        clear_btn.click(
            fn=clear_history,
            inputs=[],
            outputs=[chatbot, audio_output, status_text],
        )

    return demo


if __name__ == "__main__":
    demo = create_demo()

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )