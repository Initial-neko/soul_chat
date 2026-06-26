"""简单的 WebSocket 测试"""
import socket
import json
import base64
import threading
import time


def test_websocket():
    # 创建一个简单的 WebSocket 测试
    import urllib.request
    import urllib.error

    # 先测试 HTTP
    print("1. 测试健康检查...")
    req = urllib.request.Request("http://localhost:8000/api/health")
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"   OK: {resp.read().decode()}")
    except Exception as e:
        print(f"   FAIL: {e}")
        return

    # 测试 WebSocket 升级
    print("2. 测试 WebSocket 握手...")
    req = urllib.request.Request(
        "http://localhost:8000/ws/chat",
        headers={
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
            "Sec-WebSocket-Version": "13"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"   状态码: {resp.status}")
            print(f"   OK: WebSocket 握手成功")
    except urllib.error.HTTPError as e:
        print(f"   状态码: {e.code}")
        print(f"   响应: {e.reason}")
        if e.code == 404:
            print("   -> 路由 /ws/chat 未找到！检查后端代码")
        elif e.code == 426:
            print("   -> 需要升级协议")
        else:
            print(f"   -> {e.read().decode()[:200]}")
    except Exception as e:
        print(f"   FAIL: {e}")


if __name__ == "__main__":
    test_websocket()