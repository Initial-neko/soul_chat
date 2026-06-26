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

stt_client = STTClient()
llm_client = LLMClient()
tts_client = TTSClient()
memory = WindowMemory(window_size=20)


# ==================== 核心处理函数 ====================

def process_text(user_text: str, history: list, enable_tts: bool) -> tuple:
    """
    处理文本输入：直接发送给 LLM

    Args:
        user_text: 用户输入的文本
        history: 对话历史
        enable_tts: 是否启用 TTS

    Returns:
        (更新后的历史, TTS音频文件, 状态消息, 音频播放组件)
    """
    if not user_text or user_text.strip() == "":
        return history, None, "请输入内容", None

    try:
        # LLM 生成回复
        history_messages = memory.get_history()
        ai_response = llm_client.chat(user_text, history_messages)

        # 更新记忆
        memory.add("user", user_text)
        memory.add("assistant", ai_response)

        # TTS 生成（如果启用）
        audio_file = None
        if enable_tts:
            audio_file = tts_client.generate_speech(ai_response)

        # 更新 UI
        new_history = history + [(user_text, ai_response)]

        return new_history, audio_file, "处理完成", audio_file

    except Exception as e:
        print(f"[Error] 处理文本时出错: {e}")
        return history, None, f"处理出错: {str(e)}", None


def process_audio(audio_input, history: list, enable_tts: bool) -> tuple:
    """
    处理音频输入：STT → LLM → TTS

    Args:
        audio_input: gr.Audio 返回的 (sample_rate, data) 元组
        history: 对话历史
        enable_tts: 是否启用 TTS

    Returns:
        (更新后的历史, TTS音频文件, 状态消息, 音频播放组件)
    """
    if audio_input is None:
        return history, None, "请先录音后再发送", None

    try:
        sample_rate, audio_data = audio_input

        # 音频格式转换
        if isinstance(audio_data, np.ndarray):
            if len(audio_data.shape) > 1:
                audio_data = audio_data[:, 0]
            audio_data = audio_data.astype(np.float32)

        # STT 语音转文字
        user_text = stt_client.transcribe(audio_data, sample_rate)

        if not user_text or user_text.strip() == "":
            return history, None, "未能识别语音，请重试", None

        # LLM 生成回复
        history_messages = memory.get_history()
        ai_response = llm_client.chat(user_text, history_messages)

        # 更新记忆
        memory.add("user", user_text)
        memory.add("assistant", ai_response)

        # TTS 生成（如果启用）
        audio_file = None
        if enable_tts:
            audio_file = tts_client.generate_speech(ai_response)

        # 更新 UI
        new_history = history + [(user_text, ai_response)]

        return new_history, audio_file, "处理完成", audio_file

    except Exception as e:
        print(f"[Error] 处理音频时出错: {e}")
        return history, None, f"处理出错: {str(e)}", None


def clear_history():
    """清空对话历史"""
    memory.clear()
    return [], None, "对话历史已清空", None


# ==================== Gradio 界面 ====================

def create_demo():
    """创建 Gradio 应用"""

    with gr.Blocks(
        title="Soul Chat - 情感陪伴聊天机器人",
    ) as demo:
        gr.Markdown("""
        # Soul Chat
        ### 情感陪伴聊天机器人

        你可以直接打字聊天，或者点击麦克风录音发送语音。
        """)

        # 状态存储
        history_state = gr.State(value=[])
        tts_enabled = gr.State(value=True)  # TTS 默认开启

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="对话历史",
                    height=500,
                )
            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### 设置")
                    enable_tts = gr.Checkbox(
                        label="启用 TTS 语音回复",
                        value=True,
                    )
                    clear_btn = gr.Button("清空对话历史", variant="secondary")

        with gr.Row():
            # 文本输入
            with gr.Column(scale=3):
                text_input = gr.Textbox(
                    label="输入消息",
                    placeholder="在这里输入文字...",
                    lines=2,
                )
            with gr.Column(scale=1):
                text_submit_btn = gr.Button("发送文字", variant="primary")

        with gr.Row():
            gr.Markdown("---")
            gr.Markdown("**或者使用语音输入：**")

        with gr.Row():
            audio_input = gr.Audio(
                label="点击录音",
                sources=["microphone"],
                type="numpy",
                format="wav",
            )

        with gr.Row():
            audio_submit_btn = gr.Button("发送语音", variant="primary")

        with gr.Row():
            gr.Markdown("---")

        with gr.Row():
            # 音频输出（自动播放）
            audio_output = gr.Audio(
                label="AI 回复语音（自动播放）",
                type="filepath",
                autoplay=True,
            )

        status_text = gr.Textbox(
            label="状态",
            interactive=False,
            lines=1,
        )

        # 事件绑定：文本输入
        text_submit_btn.click(
            fn=process_text,
            inputs=[text_input, history_state, enable_tts],
            outputs=[chatbot, audio_output, status_text, audio_output],
        )
        text_input.submit(
            fn=process_text,
            inputs=[text_input, history_state, enable_tts],
            outputs=[chatbot, audio_output, status_text, audio_output],
        )

        # 事件绑定：语音输入
        audio_submit_btn.click(
            fn=process_audio,
            inputs=[audio_input, history_state, enable_tts],
            outputs=[chatbot, audio_output, status_text, audio_output],
        )

        # 事件绑定：清除历史
        clear_btn.click(
            fn=clear_history,
            inputs=[],
            outputs=[chatbot, audio_output, status_text, audio_output],
        )

    return demo


if __name__ == "__main__":
    demo = create_demo()

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
    )