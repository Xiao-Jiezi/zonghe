# 专业综合实践 - AI Agent 中台系统

一个基于 FastAPI + React 的智能 Agent 中台系统，集成多种 AI 能力模块，包括自动编程、深度研究、文档重组和语音语义分析。

## 📋 项目概览

本项目是一个专业的 AI Agent 中台系统，提供以下核心功能：

- **🤖 自动编程控制台**：基于通义千问（Qwen）大模型的代码生成器，支持多语言识别
- **🔍 深度研究枢纽**：智能研究报告生成与深度分析
- **📝 文档特征提取与重组**：对杂乱文本进行自然语言总结和逻辑排版
- **🧠 语音语义分析枢纽**：打破场景限制的通用语义理解与意图分析

## 🏗️ 技术栈

### 前端
- **框架**: React 19
- **构建工具**: Vite 8
- **样式**: Tailwind CSS 3
- **图标**: Lucide React

### 后端
- **框架**: FastAPI
- **语言**: Python 3.10+
- **HTTP 客户端**: httpx
- **数据验证**: Pydantic
- **PDF 处理**: PyPDF2

### AI 服务
- **大模型**: 通义千问（Qwen Plus）API
- **视觉多模态**: 通义千问（Qwen VL Plus）API
- **语音识别**: 通义千问（SenseVoice）API

## 🚀 快速开始

### 环境要求
- Node.js >= 20.x
- Python >= 3.10
- npm >= 10.x

### 安装与运行

**1. 安装后端依赖**
```bash
cd agent-hub-backend
pip install fastapi uvicorn httpx pydantic PyPDF2 python-docx
```

**2. 安装前端依赖**
```bash
cd agent-hub-frontend
npm install
```

**3. 启动后端服务**
```bash
cd agent-hub-backend
uvicorn main:app --reload --port 8000
```

**4. 启动前端服务**
```bash
cd agent-hub-frontend
npm run dev
```

### 访问地址
- **前端应用**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 📁 项目结构

```
agent-hub/
├── agent-hub-backend/          # 后端服务
│   ├── main.py                 # FastAPI 入口文件
│   └── __pycache__/            # Python 缓存文件
└── agent-hub-frontend/         # 前端应用
    ├── public/                 # 静态资源
    ├── src/
    │   ├── assets/             # 资源文件
    │   ├── App.jsx             # 主应用组件
    │   ├── main.jsx            # 入口文件
    │   ├── App.css             # 应用样式
    │   └── index.css           # 全局样式
    ├── .env                    # 开发环境变量
    ├── .env.production         # 生产环境变量
    ├── vite.config.js          # Vite 配置
    ├── tailwind.config.js      # Tailwind 配置
    ├── postcss.config.js       # PostCSS 配置
    └── package.json            # 前端依赖配置
```

## 🔧 配置说明

### 环境变量 (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
```

### Vite 代理配置
前端已配置 API 代理，所有 `/api` 请求自动转发到后端服务。

## 📡 API 接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/coder` | POST | 自动编程代码生成 |
| `/api/research` | POST | 深度研究报告生成 |
| `/api/ocr` | POST (multipart/form-data) | 文档图像上传与自然语言重组 |
| `/api/speech` | POST (multipart/form-data) | 真实音频流上传与语义分析 |

## 🎯 功能模块

### 1. 自动编程控制台
- 自然语言描述开发需求
- 智能代码生成与多语言识别
- 实时代码预览与一键复制
- 动态文件扩展名识别
- 40% vs 60% 黄金比例布局

### 2. 深度研究枢纽
- 复杂命题深度探索
- 结构化研究报告生成
- 优雅 Markdown 排版输出
- 全网深度挖掘能力

### 3. 视觉 OCR 处理
- **真实文件解析**：支持 PDF、Word、图片、文本文件的真实内容提取
- **PDF 文本提取**：使用 PyPDF2 从真实 PDF 中提取文本内容
- **Word 文档解析**：使用 python-docx 从 Word 文档提取文字
- **多模态视觉分析**：使用通义千问 Qwen VL Plus 分析图片内容
- **图像预览**：实时预览上传的文件
- **AI 深度重组**：将提取的内容重新组织为优雅的自然语言

### 4. 语音语义分析
- **真实麦克风录制**：使用浏览器 MediaRecorder API 捕获实时音频流
- **语音转写识别**：使用通义千问 SenseVoice 进行真实语音转写
- **音频文件上传**：支持本地上传音频文件分析
- **深层语义分析**：包含语音转写原文、核心主旨、细节梳理、意图分析

## 📝 开发命令

```bash
# 前端开发模式
npm run dev

# 前端构建生产版本
npm run build

# 代码检查
npm run lint

# 预览构建结果
npm run preview
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
