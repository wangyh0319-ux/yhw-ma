# AI Music Analyzer

分析音频的 BPM、调性、响度等指标，并用 AI 判断风格与情绪。

当前进度：**模块 7 — 分析报告**（完整报告页：摘要、指标、AI、频谱，以及加载/错误状态）。

## 你需要同时开两个窗口

这个项目有两部分：

1. **后端**（Python）：算音频、提供接口，地址 `http://127.0.0.1:8000`
2. **前端**（网页）：你看到的界面，地址 `http://localhost:5173`

## 第一次安装

在终端里进入项目文件夹：

```bash
cd ~/ai-music-analyzer
```

### 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 前端

```bash
cd frontend
npm install
```

## 每次开发时怎么运行

**窗口 1 — 后端：**

```bash
cd ~/ai-music-analyzer/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

浏览器打开：http://127.0.0.1:8000/health  
应该看到：`{"ok":true,"service":"ai-music-analyzer"}`

分析接口：网页上选文件后点 Analyze，会调用 `POST /api/analyze/run`。

MP3 需要本机安装 `ffmpeg`；WAV 可以直接分析。

### 可选：打开 AI 标签

复制 `backend/.env.example` 为 `backend/.env`，填入你的 OpenAI API 密钥，然后重启后端。

没有密钥时，客观数字仍然会出来，只是没有 Genre / Mood / Energy。

**窗口 2 — 前端：**

```bash
cd ~/ai-music-analyzer/frontend
npm run dev
```

浏览器打开终端里提示的地址（一般是 http://localhost:5173 ）。
