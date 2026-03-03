# Learn Claude Code API

FastAPI 后端服务，为 Learn Claude Code 学习平台提供 RESTful API 支持。

## 特性

- **FastAPI** - 高性能异步 Web 框架
- **Loguru** - 结构化日志记录，支持 JSON 格式
- **Pydantic** - 数据验证和序列化
- **自动 API 文档** - 自动生成 Swagger UI 和 ReDoc

## 项目结构

```
backend/
├── app/
│   ├── api/                # API 路由
│   │   ├── v1/             # v1 版本路由
│   │   │   ├── versions.py    # 版本管理 API
│   │   │   ├── scenarios.py   # 场景 API
│   │   │   ├── visualizations.py  # 可视化 API
│   │   │   ├── docs.py        # 文档 API
│   │   │   └── system.py      # 系统 API
│   │   └── __init__.py
│   ├── core/               # 核心模块
│   │   ├── config.py       # 配置管理
│   │   └── logger.py       # 日志配置
│   ├── models/             # 数据模型
│   │   └── schemas.py      # Pydantic 模型
│   ├── services/           # 服务层
│   │   └── data_service.py # 数据服务
│   └── main.py             # 应用入口
├── logs/                   # 日志目录
├── tests/                  # 测试文件
├── .env.example            # 环境变量示例
├── requirements.txt        # 依赖列表
└── README.md               # 项目文档
```

## 快速开始

### 1. 安装依赖

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑 .env 文件，根据需要修改配置
```

### 3. 启动服务

```bash
# 开发模式（带热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. 访问 API

- API 文档: http://localhost:8000/docs
- 替代文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/api/v1/system/health

## API 接口

### 版本管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/versions` | 获取版本列表 |
| GET | `/api/v1/versions/timeline` | 获取版本时间线 |
| GET | `/api/v1/versions/{version_id}` | 获取版本详情 |
| GET | `/api/v1/versions/{version_id}/source` | 获取版本源代码 |
| GET | `/api/v1/versions/{version_id}/diff` | 对比版本差异 |
| POST | `/api/v1/versions/compare` | 对比任意两个版本 |

### 学习场景

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/scenarios` | 获取场景列表 |
| GET | `/api/v1/scenarios/{scenario_id}` | 获取场景详情 |
| GET | `/api/v1/scenarios/by-version/{version_id}` | 按版本获取场景 |

### 可视化

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/visualizations/{version_id}` | 获取可视化数据 |
| GET | `/api/v1/visualizations/{version_id}/state/{step}` | 获取指定状态 |

### 系统

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/system/health` | 健康检查 |
| GET | `/api/v1/system/info` | 系统信息 |
| GET | `/api/v1/system/stats` | 统计数据 |

## 日志系统

使用 Loguru 实现结构化日志记录：

### 日志文件

- `logs/app.log` - 应用日志（文本格式）
- `logs/app.json` - 应用日志（JSON 格式，用于日志收集）
- `logs/error.log` - 错误日志（ERROR 级别以上）

### 使用日志

```python
from app.core.logger import get_logger, info, error, exception

# 获取 logger
logger = get_logger(__name__)

# 记录日志
info("用户登录", extra={"user_id": "123", "ip": "192.168.1.1"})
error("操作失败", extra={"error_code": "E001"})
exception("发生异常")  # 自动包含堆栈
```

### 日志轮转

- **app.log**: 500MB 自动轮转，保留 30 天
- **app.json**: 每天轮转，保留 30 天
- **error.log**: 100MB 自动轮转，保留 30 天

## 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `DEBUG` | `true` | 调试模式 |
| `ENVIRONMENT` | `development` | 运行环境 |
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8000` | 监听端口 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `LOG_JSON` | `false` | JSON 格式日志 |
| `DATA_DIR` | `../web/src/data` | 前端数据目录 |

## 开发

### 代码格式化

```bash
# 使用 black 格式化
black app/

# 使用 ruff 检查
ruff check app/
ruff check --fix app/

# 类型检查
mypy app/
```

### 运行测试

```bash
pytest
```

## 部署

### Docker 部署

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产环境配置

```bash
# 设置环境变量
export DEBUG=false
export ENVIRONMENT=production
export LOG_JSON=true
export LOG_LEVEL=WARNING

# 使用 Gunicorn 运行
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 许可证

MIT
