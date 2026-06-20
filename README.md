# HMP WS Service (DDD)

HMP WS Service 高性能异步长连接与大文件传输中心，是一套基于 **FastAPI + SQLAlchemy + RabbitMQ** 的高性能实时通信与文件服务。项目采用领域驱动设计（DDD）的分层架构，实现了安全的 WebSocket 长连接生命周期管理、RabbitMQ 扇出模式的多实例实时消息广播、MySQL 站内信系统以及基于二进制帧零拷贝与并发滑动窗口的流式大文件分片上传。

---

## 🚀 核心功能

1. **WebSocket 长连接网关**
   - **多标签页共存**：完美支持同一客户端 ID 下的多浏览器标签页/多连接管理，下线精确移除。
   - **自动重连机制**：前端具备指数退避自动重连，服务端具备鲁棒垃圾回收。
   - **安全令牌校验**：支持基于 Bearer Header 或 Query 参数的安全 Token 校验边界。
2. **分布式站内信广播系统**
   - **多实例分发**：支持 **RabbitMQ Fanout Exchange** 扇出广播。在集群/多实例水平扩展部署时，保证每个节点都能消费到消息并推送给其本地的在线用户。
   - **非阻塞落库**：采用多线程隔离机制（`asyncio.to_thread`），高并发下数据库操作不阻塞 asyncio 主事件循环。
3. **滑动窗口并发大文件分片上传**
   - **二进制流式传输**：采用纯二进制 Websocket 帧配合零拷贝技术，保障内存与 CPU 的极致低负荷。
   - **并发滑动窗口**：基于客户端并发发送控制（滑动窗口机制），兼顾测速、ETA 预估与上传取消防护。
   - **路径穿越防御**：严格校验 `upload_id` 规范，对临时目录删除进行绝对物理路径防越权穿越保护。

---

## 🛠️ 技术栈

- **核心框架**：[FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **ORM / 数据库**：[SQLAlchemy 2.0](https://www.sqlalchemy.org/) + [PyMySQL](https://github.com/PyMySQL/PyMySQL) (MySQL 5.7+)
- **版本迁移管理**：[Alembic](https://alembic.sqlalchemy.org/)
- **消息队列**：[aio-pika](https://github.com/mosbrupture/aio-pika) (RabbitMQ 异步驱动)
- **校验边界**：[Pydantic v2](https://docs.pydantic.dev/)
- **测试保障**：[pytest](https://docs.pytest.org/) + [httpx](https://www.python-httpx.org/)

---

## 📂 项目目录结构

项目严格遵循 DDD (领域驱动设计) 分层规范进行划分，代码高内聚、低耦合：

```text
hmp_ws_service/
  ├── alembic/                  # Alembic 数据库版本演进迁移目录
  ├── app/                      # DDD 业务代码目录
  │    ├── domain/              # 领域层：领域对象（SiteMessage 实体）与仓储契约接口
  │    ├── application/         # 应用层：负责业务流转与编排（Message/Upload 服务层）
  │    ├── infrastructure/      # 基础设施层：数据源、MQ适配器、本地存储及鉴权
  │    └── interfaces/          # 接口层：HTTP API 路由、Web 页面及 WebSocket 端点与 Handler
  ├── static/                   # 独立出来的静态文件托管（CSS/JS/图标库）
  ├── templates/                # HMP 控制台调试 HTML 模板
  ├── tests/                    # 单元测试模块 (包含上传安全、Token鉴权和站内信测试)
  ├── requirements.txt          # 运行、开发与测试统一依赖清单
  ├── main.py                   # 服务主运行入口
  ├── alembic.ini               # Alembic 配置文件
  └── run.bat                   # Windows 下一键启动批处理脚本
```

---

## ⚙️ 环境配置

在根目录下创建 `.env` 配置文件（或在操作系统环境变量中声明）：

```ini
# 监听端口
PORT=18088

# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=hmp_websocket

# RabbitMQ 配置
RABBITMQ_HOST=127.0.0.1
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# 安全令牌配置（若留空则不拦截，便于本地调试）
API_TOKEN=secure-secret-token
```

---

## 🏃 启动与运行

### 1. 安装项目依赖
建议在 Python 虚拟环境中，运行以下命令一键安装所有运行与开发依赖：
```bash
pip install -r requirements.txt
```

### 2. 数据库迁移与初始化
如果您的数据库之前已包含 `site_message` 表，Alembic 系统已为您配置了最新基线。只需在项目根目录下执行以下指令完成迁移更新：
```bash
alembic upgrade head
```

### 3. 运行服务
您可以通过以下命令直接拉起服务：
```bash
python main.py
```
*在 Windows 环境下，您也可以直接双击根目录下的 `run.bat` 进行一键快速启动。*

启动成功后，您可以通过以下地址访问服务：
- **HMP WS Service 全功能控制台**：[http://127.0.0.1:18088/](http://127.0.0.1:18088/) （用于 WebSocket 通信自测、模拟站内信分发及大文件并发上传验证）
- **Swagger 接口文档**：[http://127.0.0.1:18088/docs](http://127.0.0.1:18088/docs)

---

## 🧪 运行单元测试

项目中已包含完备的单元测试，已经通过 Mock 对 MySQL 及 RabbitMQ 连接进行解耦隔离，您可以直接在本地无污染运行：

```bash
pytest
```

测试覆盖了：
- **路径与上传安全**：校验上传会话 ID 的合法性正则与文件名穿越防护行为。
- **Token 鉴权机制**：验证在提供/不提供 `API_TOKEN` 时的 API 拦截行为与 Query Token 校验。
- **站内信 API 约束**：检验站内信发送接口的字段校验、空字段检测与长度溢出拦截。

---

## 🔄 数据库开发迁移规范 (Alembic)

项目已经初始化了 Alembic 架构支持，在日常迭代中：

1. **更新数据库模型**：当您在 [models.py](file:///d:/Project_2023/hmp_ws_service/app/infrastructure/database/models.py) 中更新了表结构（如修改了字段、增加了索引等）。
2. **自动生成迁移脚本**：在根目录下执行：
   ```bash
   alembic revision --autogenerate -m "变更说明文案"
   ```
   它会在 `alembic/versions/` 目录中生成带有时间戳的 `.py` 版本脚本。请确认脚本内自动生成的 DDL 逻辑（`upgrade` 和 `downgrade`）完全无误。
3. **应用迁移**：
   ```bash
   alembic upgrade head
   ```
