"""
后端 API - FastAPI + WebSocket
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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

# 每个连接独立的记忆
connections: dict[str, WindowMemory] = {}

# 缓存目录
CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# 音频目录
AUDIO_DIR = CACHE_DIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)


# ==================== FastAPI 应用 ====================

app = FastAPI(title="Soul Chat API")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== WebSocket 处理 ====================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket 聊天端点"""
    connection_id = str(uuid.uuid4())
    memory = WindowMemory(window_size=20)
    connections[connection_id] = memory

    await websocket.accept()

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            msg_type = data.get("type")
            content = data.get("content")
            enable_tts = data.get("enable_tts", True)

            if msg_type == "text":
                await handle_text_message(websocket, content, memory, enable_tts)
            elif msg_type == "audio":
                await handle_audio_message(websocket, content, memory, enable_tts)
            elif msg_type == "clear":
                memory.clear()
                await websocket.send_json({"type": "done", "content": "历史已清空"})
            else:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        print(f"[WS] Client {connection_id} disconnected")
    except Exception as e:
        print(f"[WS] Error: {e}")
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except:
            pass
    finally:
        del connections[connection_id]


async def handle_text_message(websocket: WebSocket, text: str, memory: WindowMemory, enable_tts: bool):
    """处理文本消息"""
    if not text or text.strip() == "":
        await websocket.send_json({"type": "error", "content": "消息不能为空"})
        return

    # 流式调用 LLM
    history = memory.get_history()

    full_response = ""
    for chunk in llm_client.stream_chat(text, history):
        full_response += chunk
        await websocket.send_json({"type": "chunk", "content": chunk})

    # 保存到记忆
    memory.add("user", text)
    memory.add("assistant", full_response)

    # 发送完成信号
    await websocket.send_json({"type": "done", "content": full_response})

    # 生成 TTS（如果启用）
    if enable_tts and full_response:
        try:
            audio_file = tts_client.generate_speech(full_response)
            # 返回音频文件路径（相对路径）
            audio_url = f"/api/audio/{Path(audio_file).name}"
            await websocket.send_json({"type": "tts", "content": audio_url})
        except Exception as e:
            print(f"[TTS] Error: {e}")


async def handle_audio_message(websocket: WebSocket, audio_base64: str, memory: WindowMemory, enable_tts: bool):
    """处理音频消息（base64 编码）"""
    try:
        import base64
        import io

        # 解码 base64
        audio_bytes = base64.b64decode(audio_base64)

        # 读取为 numpy 数组
        audio_array, sr = sf.read(io.BytesIO(audio_bytes))

        # 转换格式
        if audio_array.dtype != np.float32:
            audio_array = audio_array.astype(np.float32)
        if len(audio_array.shape) > 1:
            audio_array = audio_array[:, 0]

        # STT 识别
        text = stt_client.transcribe(audio_array, sr)

        if not text or text.strip() == "":
            await websocket.send_json({"type": "error", "content": "未能识别语音"})
            return

        # 告诉客户端识别到的文字
        await websocket.send_json({"type": "recognized", "content": text})

        # 流式调用 LLM
        history = memory.get_history()

        full_response = ""
        for chunk in llm_client.stream_chat(text, history):
            full_response += chunk
            await websocket.send_json({"type": "chunk", "content": chunk})

        # 保存到记忆
        memory.add("user", text)
        memory.add("assistant", full_response)

        # 发送完成信号
        await websocket.send_json({"type": "done", "content": full_response})

        # 生成 TTS（如果启用）
        if enable_tts and full_response:
            try:
                audio_file = tts_client.generate_speech(full_response)
                audio_url = f"/api/audio/{Path(audio_file).name}"
                await websocket.send_json({"type": "tts", "content": audio_url})
            except Exception as e:
                print(f"[TTS] Error: {e}")

    except Exception as e:
        print(f"[Audio] Error: {e}")
        await websocket.send_json({"type": "error", "content": f"处理音频失败: {str(e)}"})


# ==================== REST API ====================

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


@app.post("/api/audio/stt")
async def audio_to_text(file: UploadFile = File(...)):
    """语音转文字 API"""
    try:
        audio_bytes = await file.read()

        # 读取为 numpy 数组
        audio_array, sr = sf.read(io.BytesIO(audio_bytes))

        if audio_array.dtype != np.float32:
            audio_array = audio_array.astype(np.float32)
        if len(audio_array.shape) > 1:
            audio_array = audio_array[:, 0]

        text = stt_client.transcribe(audio_array, sr)

        return {"text": text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import io


@app.post("/api/audio/tts")
async def text_to_audio(text: str):
    """文字转语音 API"""
    try:
        audio_file = tts_client.generate_speech(text)
        filename = Path(audio_file).name
        return {"audio_url": f"/api/audio/{filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """获取音频文件"""
    audio_path = CACHE_DIR / filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(audio_path, media_type="audio/mpeg")


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )