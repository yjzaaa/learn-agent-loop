# 前后端联调文档

本文档说明如何配置和运行 Learn Claude Code 的前后端联调。

## 架构概述

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (Next.js)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Server     │  │  Client     │  │  API Client (lib/api.ts)│  │
│  │  Components │  │  Components │  └───────────┬─────────────┘  │
│  └──────┬──────┘  └──────┬──────┘              │                │
│         │                 │                    │                │
│         └─────────────────┴────────────────────┘                │
│                           │                                     │
│              直接使用 API 或 Server API                          │
└───────────────────────────┼─────────────────────────────────────┘
                            │ HTTP
┌───────────────────────────┼─────────────────────────────────────┐
│                           ▼                                     │
│              后端 (FastAPI + Loguru)                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  API Routes (app/api/v1/)                                │   │
│  │  ├── versions.py    # 版本管理                           │   │
│  │  ├── scenarios.py   # 学习场景                           │   │
│  │  ├── visualizations.py # 可视化数据                       │   │
│  │  ├── docs.py        # 文档                               │   │
│  │  └── system.py      # 系统/健康检查                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Data Service (app/services/data_service.py)             │   │
│  │  └── 读取 web/src/data 目录下的 JSON 文件                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 快速启动

### 1. 启动后端服务

```bash
cd backend

# 创建虚拟环境（如果还没有）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 运行。

访问 http://localhost:8000/docs 查看自动生成的 API 文档。

### 2. 启动前端服务

```bash
cd web

# 安装依赖（如果还没有）
npm install

# 配置环境变量
cp .env.local.example .env.local

# 启动开发服务器
npm run dev
```

前端服务将在 http://localhost:3000 运行。

### 3. 验证联调

1. 访问 http://localhost:3000 - 前端页面应正常加载
2. 访问 http://localhost:3000/en/timeline - 时间线页面应从后端 API 获取数据
3. 访问 http://localhost:3000/en/s01 - 版本详情页应显示后端数据
4. 查看后端日志 - 应能看到请求日志

## 配置说明

### 后端配置 (backend/.env)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | `8000` | 后端服务端口 |
| `CORS_ORIGINS` | `http://localhost:3000` | 允许的前端域名 |
| `DATA_DIR` | `../web/src/data` | 前端数据目录路径 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 前端配置 (web/.env.local)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | 后端 API 地址 |

## 数据流说明

### Server Components (服务端组件)

服务端组件直接使用 `lib/server-api.ts` 中的函数调用后端 API：

```typescript
// app/[locale]/(learn)/[version]/page.tsx
import { getVersionServer } from "@/lib/server-api";

export default async function VersionPage({ params }) {
  const versionData = await getVersionServer(params.version);
  // ...
}
```

**特点：**
- 在服务端执行，不暴露 API 调用逻辑到客户端
- 更好的 SEO 和首屏加载性能
- 支持异步数据获取

### Client Components (客户端组件)

客户端组件使用 `lib/api-service.ts` 中的函数调用后端 API：

```typescript
// 客户端组件
"use client";
import { getVersion } from "@/lib/api-service";

export default function MyComponent() {
  useEffect(() => {
    getVersion("s01").then(data => {
      console.log(data);
    });
  }, []);
}
```

**特点：**
- 在浏览器中执行
- 适用于交互式组件
- 可以响应用户操作

## API 端点列表

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/versions` | 获取版本列表 |
| GET | `/api/v1/versions/{id}` | 获取版本详情 |
| GET | `/api/v1/versions/{id}/source` | 获取版本源代码 |
| GET | `/api/v1/versions/{id}/diff` | 获取版本差异 |
| GET | `/api/v1/scenarios/by-version/{id}` | 获取场景 |
| GET | `/api/v1/visualizations/{id}` | 获取可视化数据 |
| GET | `/api/v1/docs` | 获取文档列表 |
| GET | `/api/v1/system/health` | 健康检查 |

## 故障排查

### 跨域错误 (CORS)

**症状：** 浏览器控制台显示 CORS 错误

**解决：**
1. 检查后端 `.env` 中的 `CORS_ORIGINS` 是否包含前端地址
2. 确保后端服务已重启

### 数据未更新

**症状：** 前端显示的数据不是最新的

**解决：**
1. 后端数据有缓存，重启后端服务刷新缓存
2. 检查 `DATA_DIR` 路径是否正确

### API 连接失败

**症状：** 前端无法获取数据

**解决：**
1. 确认后端服务是否运行：`curl http://localhost:8000/api/v1/system/health`
2. 检查前端 `.env.local` 中的 `NEXT_PUBLIC_API_URL` 是否正确
3. 检查防火墙设置

### 数据格式不匹配

**症状：** API 返回 500 错误或数据为空

**解决：**
1. 检查后端日志查看具体错误
2. 确认 `web/src/data/generated/versions.json` 和 `docs.json` 格式正确
3. 检查 `DATA_DIR` 路径是否正确指向数据目录

## 开发建议

1. **日志查看**
   - 后端日志：`backend/logs/app.log`
   - 前端日志：浏览器开发者工具 Console

2. **API 测试**
   - 使用 Swagger UI：http://localhost:8000/docs
   - 使用 curl 或 Postman 测试 API

3. **热重载**
   - 后端：修改代码后自动重载（`--reload` 模式）
   - 前端：Next.js 自动热重载

4. **生产部署**
   - 后端：设置 `ENVIRONMENT=production`，`LOG_JSON=true`
   - 前端：使用 `npm run build` 构建静态文件
