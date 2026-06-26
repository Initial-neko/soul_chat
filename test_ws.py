"""WebSocket API 测试"""
import asyncio
import json
import websockets
import sys


async def test_websocket():
    uri = "ws://localhost:8000/ws/chat"

    print("测试: WebSocket 连接...")
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ 连接成功")

            # 发送文本消息
            test_msg = {
                "type": "text",
                "content": "你好",
                "enable_tts": False
            }
            await websocket.send(json.dumps(test_msg))
            print("✓ 发送消息成功")

            # 接收响应
            chunks = []
            try:
                while True:
                    response = await asyncio.wait_for(websocket.recv(), timeout=15)
                    data = json.loads(response)
                    print(f"  收到: type={data.get('type')}, content={data.get('content', '')[:50]}...")

                    if data.get("type") == "done":
                        break
                    chunks.append(data)
            except asyncio.TimeoutError:
                print("  等待响应超时")

            if chunks:
                print(f"✓ 共收到 {len(chunks)} 个响应片段")
                return True
            else:
                print("✗ 未收到响应")
                return False

    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


if __name__ == "__main__":
    # 先检查健康检查
    import urllib.request
    try:
        resp = urllib.request.urlopen("http://localhost:8000/api/health")
        print(f"健康检查: {resp.read().decode()}")
    except Exception as e:
        print(f"后端未启动: {e}")
        sys.exit(1)

    # 运行 WebSocket 测试
    result = asyncio.run(test_websocket())
    sys.exit(0 if result else 1)