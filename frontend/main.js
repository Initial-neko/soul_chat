// ==================== 常量 ====================

const WS_URL = `ws://${window.location.host}/ws/chat`;
const API_BASE = '';  // Vite 代理


// ==================== 状态 ====================

let ws = null;
let isConnected = false;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let currentAiMessage = null;
let enableTts = true;


// ==================== DOM 元素 ====================

const chatArea = document.getElementById('chatArea');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');
const micBtn = document.getElementById('micBtn');
const ttsToggle = document.getElementById('ttsToggle');
const clearBtn = document.getElementById('clearBtn');
const audioPlayer = document.getElementById('audioPlayer');
const audioElement = document.getElementById('audioElement');
const status = document.getElementById('status');


// ==================== WebSocket ====================

function connect() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    console.log('[WS] Connected');
    isConnected = true;
    updateStatus('已连接', 'connected');
  };

  ws.onclose = () => {
    console.log('[WS] Disconnected');
    isConnected = false;
    updateStatus('连接已断开，正在重连...', 'disconnected');
    // 自动重连
    setTimeout(connect, 3000);
  };

  ws.onerror = (error) => {
    console.error('[WS] Error:', error);
    updateStatus('连接错误', 'error');
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleMessage(data);
  };
}

function sendMessage(type, content, enableTts = true) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    updateStatus('连接未建立', 'error');
    return;
  }

  ws.send(JSON.stringify({
    type,
    content,
    enable_tts: enableTts
  }));
}

function handleMessage(data) {
  switch (data.type) {
    case 'chunk':
      // 流式输出片段
      appendToAiMessage(data.content);
      break;

    case 'done':
      // 输出完成
      finishAiMessage(data.content);
      updateStatus('处理完成', 'connected');
      break;

    case 'tts':
      // TTS 音频
      playAudio(data.content);
      break;

    case 'recognized':
      // 语音识别结果
      addMessage(data.content, 'user');
      startAiMessage();
      updateStatus('正在生成回复...', 'connected');
      break;

    case 'error':
      // 错误
      updateStatus(`错误: ${data.content}`, 'error');
      finishAiMessage('');
      break;
  }
}


// ==================== 消息处理 ====================

function addMessage(content, role) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;

  const label = document.createElement('div');
  label.className = 'message-label';
  label.textContent = role === 'user' ? '你' : 'Soul';

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  contentDiv.textContent = content;

  messageDiv.appendChild(label);
  messageDiv.appendChild(contentDiv);

  // 移除欢迎消息
  const welcome = chatArea.querySelector('.welcome-message');
  if (welcome) welcome.remove();

  chatArea.appendChild(messageDiv);
  chatArea.scrollTop = chatArea.scrollHeight;
}

function startAiMessage() {
  currentAiMessage = '';
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message assistant';
  messageDiv.id = 'ai-message';

  const label = document.createElement('div');
  label.className = 'message-label';
  label.textContent = 'Soul';

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content typing';
  contentDiv.textContent = '';

  messageDiv.appendChild(label);
  messageDiv.appendChild(contentDiv);

  chatArea.appendChild(messageDiv);
  chatArea.scrollTop = chatArea.scrollHeight;
}

function appendToAiMessage(text) {
  currentAiMessage += text;
  const aiMessage = document.getElementById('ai-message');
  if (aiMessage) {
    const contentDiv = aiMessage.querySelector('.message-content');
    contentDiv.textContent = currentAiMessage;
    chatArea.scrollTop = chatArea.scrollHeight;
  }
}

function finishAiMessage(fullText) {
  const aiMessage = document.getElementById('ai-message');
  if (aiMessage) {
    aiMessage.classList.remove('typing');
    const contentDiv = aiMessage.querySelector('.message-content');
    contentDiv.textContent = fullText || currentAiMessage;
    contentDiv.classList.remove('typing');
  }
  currentAiMessage = null;
  chatArea.scrollTop = chatArea.scrollHeight;
}

function clearMessages() {
  chatArea.innerHTML = `
    <div class="welcome-message">
      <p>你好呀！我是 Soul Chat，很高兴认识你~</p>
      <p>可以直接打字聊天，或者点击麦克风录音发送语音哦！</p>
    </div>
  `;
  sendMessage('clear', '');
}


// ==================== 音频播放 ====================

function playAudio(audioUrl) {
  if (!enableTts) return;

  const fullUrl = window.location.origin + audioUrl;
  audioElement.src = fullUrl;
  audioPlayer.style.display = 'block';
  audioElement.play().catch(err => {
    console.log('[Audio] Play failed:', err);
  });
}


// ==================== 状态 ====================

function updateStatus(text, type) {
  status.textContent = text;
  status.className = `status ${type}`;
}


// ==================== 事件监听 ====================

// 发送文本
sendBtn.addEventListener('click', () => {
  const text = textInput.value.trim();
  if (!text) return;

  addMessage(text, 'user');
  textInput.value = '';
  startAiMessage();
  updateStatus('正在生成回复...', 'connected');

  sendMessage('text', text, enableTts);
});

textInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    sendBtn.click();
  }
});

// 录音
micBtn.addEventListener('click', async () => {
  if (!isRecording) {
    // 开始录音
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];

      mediaRecorder.ondataavailable = (e) => {
        audioChunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const arrayBuffer = await audioBlob.arrayBuffer();
        const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));

        startAiMessage();
        updateStatus('正在识别语音...', 'connected');
        sendMessage('audio', base64, enableTts);

        // 停止所有 tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      isRecording = true;
      micBtn.classList.add('recording');
      micBtn.querySelector('.mic-text').textContent = '录音中...';

    } catch (err) {
      console.error('[Mic] Error:', err);
      updateStatus('无法访问麦克风', 'error');
    }
  } else {
    // 停止录音
    mediaRecorder.stop();
    isRecording = false;
    micBtn.classList.remove('recording');
    micBtn.querySelector('.mic-text').textContent = '录音';
  }
});

// TTS 开关
ttsToggle.addEventListener('change', () => {
  enableTts = ttsToggle.checked;
});

// 清空对话
clearBtn.addEventListener('click', () => {
  clearMessages();
  updateStatus('对话已清空', 'connected');
});


// ==================== 初始化 ====================

connect();