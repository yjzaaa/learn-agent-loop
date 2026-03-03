# AgentCore 启动指南

## 环境要求

- Python 3.11+
- Node.js 20+
- 已安装后端依赖（`backend/.venv-new`）
- 已安装前端依赖（`web/node_modules`）

## 快速启动

### 1. 启动后端服务

打开 **PowerShell 窗口 1**，切换到 `.venv-new` 虚拟环境：

```powershell
# 进入后端目录
cd D:\kearn-claude-code\learn-claude-code\backend

# 激活虚拟环境（如果还没激活）
..\.venv-new\Scripts\Activate.ps1

# 启动后端（端口 8080）
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

看到以下输出说明启动成功：
```
Uvicorn running on http://127.0.0.1:8080
```

### 2. 启动前端服务

打开 **PowerShell 窗口 2**：

```powershell
# 进入前端目录
cd D:\kearn-claude-code\learn-claude-code\web

# 启动前端开发服务器
npm run dev
```

看到以下输出说明启动成功：
```
Ready in xxxms
- Local: http://localhost:3000
```

**注意**：如果 3000 端口被占用，会自动使用 3001，以实际输出为准。

### 3. 浏览器访问

打开浏览器访问前端地址：

```
http://localhost:3000/agentcore
```

或（如果 3000 被占用）：

```
http://localhost:3001/agentcore
```

---

## 使用流程

1. 打开 AgentCore 页面
2. 在左侧列表点击 **"Session 1"** 选择会话（必须先选择会话才能输入）
3. 在顶部输入框输入查询（如 `List all files`）
4. 点击 **Run** 按钮运行 Agent
5. 查看中间画布显示执行图谱

---

## 常见问题

### 端口被占用

**8080 端口被占用**：
```powershell
# 查找并关闭占用 8080 的进程
Get-Process -Id (netstat -ano | findstr ":8080" | Select-Object -First 1).Split()[-1] -ErrorAction SilentlyContinue | Stop-Process -Force
```

**3000 端口被占用**：
前端会自动切换到 3001 端口，使用 `http://localhost:3001/agentcore` 访问。

### 后端 API 测试

```powershell
# 测试 API 是否运行
curl http://localhost:8080/api/v1/agentcore/sessions
```

### WebSocket 连接失败

检查 `.env.local` 文件配置：
```
# web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + Kuzu 图数据库 |
| 前端 | Next.js 16 + React 19 + TypeScript |
| 可视化 | Sigma.js |
| 通信 | REST API + WebSocket |

---

## 项目结构

```
learn-claude-code/
├── backend/
│   └── app/agentcore/          # AgentCore 核心模块
│       ├── core/               # Agent 基类和 Mixins
│       ├── graph/              # 图数据库和模型
│       ├── execution/          # 执行引擎
│       └── api/                # API 路由
├── web/
│   └── src/components/agentcore/  # 前端组件
└── docs/
    └── agentcore-knowledge-graph-design.md  # 设计文档
```
