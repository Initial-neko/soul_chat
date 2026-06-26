# 情感陪伴聊天机器人 — Soul Chat

## 项目目标

构建一个以**情绪价值**为核心的语音对话 Demo，打通 STT → LLM → TTS 完整链路，并通过简易 WebUI 可交互。

**当前阶段目标（Demo v0.1）：**
- 用户通过麦克风说话 → STT 转文字
- 文字交给 DeepSeek 生成有温度的回复（含简单记忆）
- 回复通过 TTS 转语音播放
- Gradio WebUI 将上述流程可视化、可交互

---

## 技术栈

| 模块 | 方案 | 说明 |
|------|------|------|
| STT | `faster-whisper` (本地) 或 `OpenAI Whisper API` | 本地免费；API 更简单 |
| LLM | `DeepSeek API` (deepseek-chat) | 直接调用 OpenAI SDK |
| TTS | `edge-tts` | 免费，中文效果好 |
| WebUI | `Gradio` | 原生支持音频输入/输出组件 |
| 记忆 | 内存 `list`（Demo 阶段） | 维护 messages 窗口，后期扩展 |
| 包管理 | `uv` | 项目使用 uv 管理依赖 |

---

## 项目结构

```
soul-chat/
├── CLAUDE.md                  # 本文件
├── pyproject.toml             # uv 依赖配置（使用 uv 管理）
├── .env                       # API Key 等环境变量（不提交 git）
├── .env.example               # 环境变量模板

├── core/                      # 核心逻辑模块
│   ├── __init__.py
│   ├── stt.py                 # STT：语音 → 文字
│   ├── llm.py                 # LLM：文字 → 文字（含人格与记忆）
│   ├── tts.py                 # TTS：文字 → 语音
│   └── pipeline.py            # 串联 STT + LLM + TTS

├── memory/                    # 记忆系统（Demo 阶段为内存实现）
│   ├── __init__.py
│   └── window_memory.py       # 滑动窗口记忆，维护 messages list

├── prompts/                   # Prompt 管理
│   └── system_prompt.txt      # 角色人格设定

├── tests/                     # 测试模块
│   └── test_llm.py

└── app.py                     # Gradio WebUI 入口
```

---

## 快速启动

```bash
# 1. 安装 uv（如果没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 4. 启动 WebUI
uv run python app.py
# 浏览器访问 http://localhost:7860
```

---

## 环境变量（.env）

```
DEEPSEEK_API_KEY=your-api-key-here
STT_MODE=api          # api 或 local
WHISPER_MODEL=base    # local 模式下的模型大小：tiny/base/small
TTS_VOICE=zh-CN-XiaoxiaoNeural   # edge-tts 中文语音
MEMORY_WINDOW=20      # 滑动窗口保留轮数
```

---

## Git 提交规范

### 提交时机

每个开发阶段完成后**立即提交**，不要等到多个功能完成后一起提交。

### 提交信息格式

```
<类型>: <简短描述>

[可选的详细描述]
```

**类型说明：**
- `feat`: 新功能
- `fix`: 修复 bug
- `refactor`: 重构
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 构建/工具/依赖等

**示例：**
```
feat: 完成 LLM 模块和记忆系统

- 实现 DeepSeek API 客户端
- 添加滑动窗口记忆功能
- 包含流式输出支持
```

### 当前开发进度

- [x] 初始化项目结构
- [x] 配置 pyproject.toml 依赖
- [x] 实现 LLM 模块 (DeepSeek)
- [ ] 实现 STT 模块
- [ ] 实现 TTS 模块
- [ ] 实现 pipeline 串联
- [ ] 实现 Gradio WebUI

---

## 开发阶段

### Phase 1 — 链路跑通（当前目标）

- [x] 环境搭建，配置 pyproject.toml 依赖
- [x] 创建 core/llm.py 并测试（DeepSeek）
- [x] 创建 memory/window_memory.py
- [x] 创建 prompts/system_prompt.txt
- [ ] 创建 core/stt.py 并测试
- [ ] 创建 core/tts.py 并测试
- [ ] 创建 core/pipeline.py 串联三模块
- [ ] 创建 app.py Gradio WebUI

### Phase 2 — 体验优化

- [ ] 流式输出（Streaming）减少等待感
- [ ] 记忆系统升级（摘要压缩 + 用户画像持久化）
- [ ] TTS 语气优化（不同情绪用不同语速/音色）
- [ ] 错误处理与异常兜底

### Phase 3 — 功能扩展（待定）

- [ ] 向量数据库接入（长期情景记忆）
- [ ] 轻量工具调用（天气、提醒）
- [ ] 多角色/人格切换

---

## 依赖管理（使用 uv）

```bash
# 添加依赖
uv add openai edge-tts gradio python-dotenv soundfile numpy faster-whisper aiohttp

# 安装项目
uv sync
```

---

## 注意事项

1. **不要使用 pip** — 所有依赖管理使用 `uv` 命令
2. **运行项目使用 `uv run`** — 例如 `uv run python app.py`
3. **测试模块先单测** — 确认每个模块独立工作后再串联
4. **.env 不提交 git** — 确保 .gitignore 包含 .env
5. **每个阶段完成后立即提交 git** — 保持提交粒度适中