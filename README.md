# HMP WS Service — 欢乐斗地主

本项目是一个基于前后端彻底分离架构的“欢乐斗地主”网络对战系统。

## 项目结构

```text
hmp_ws_service/
├── backend/      # 后端服务 (FastAPI + DDD 架构 + MySQL + Redis + RabbitMQ)
└── frontend/     # 前端客户端 (Vue 3 + Vite + Pinia + Vue Router 4)
```

## 快速开始

### 后端启动

1. 进入后端目录：
   ```bash
   cd backend
   ```
2. 激活 Python 虚拟环境（如 conda 环境 `hmp_ai`）：
   ```bash
   conda activate hmp_ai
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 配置 `.env` 环境变量（确保本地的 MySQL, Redis 和 RabbitMQ 服务已正常运行且配置正确）。
5. 启动服务：
   ```bash
   python main.py
   ```
   服务将默认运行在 `http://127.0.0.1:18088`。

### 前端启动

1. 进入前端目录：
   ```bash
   cd frontend
   ```
2. 安装依赖：
   ```bash
   npm install
   ```
3. 启动开发服务器：
   ```bash
   npm run dev
   ```
   前端服务将默认运行在 `http://localhost:5173`。

## 运行测试

进入后端目录，运行以下命令验证后端功能：

```bash
cd backend
python -m pytest tests/ -v
```
