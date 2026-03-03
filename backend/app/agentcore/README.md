# AgentCore - Knowledge Graph Based Agent System

基于知识图谱的 Agent 核心系统

## 概述

AgentCore 将传统 Agent 的执行过程转化为知识图谱，实现：

- **执行可视化**: 实时观察 Agent 的执行流程
- **可追溯性**: 完整的执行历史记录
- **可分析性**: 基于图谱的查询和分析
- **可扩展性**: 模块化 Mixin 架构

## 核心概念

### 运行状态即图谱

```
AgentSession → ExecutionStep → ToolCall → Message
     ↓              ↓              ↓
   Task         Todo        Compression
```

### 节点类型

| 节点 | 描述 |
|-----|------|
| `AgentSession` | Agent 会话实例 |
| `ExecutionStep` | 执行步骤（LLM调用/工具执行） |
| `ToolCall` | 工具调用记录 |
| `Message` | 消息节点 |
| `Task` | 任务节点 |
| `Todo` | 待办事项 |

### 关系类型

| 关系 | 描述 |
|-----|------|
| `HAS_STEP` | 会话包含步骤 |
| `NEXT_STEP` | 执行顺序 |
| `CALLS_TOOL` | 调用工具 |
| `PRODUCES` | 产生消息 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
export ANTHROPIC_API_KEY="your-api-key"
export MODEL_ID="claude-sonnet-4-6"
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. 访问 API 文档

打开 http://localhost:8000/docs

## API 端点

### 会话管理

```bash
# 创建会话
POST /api/v1/agentcore/sessions
{
  "name": "My Session",
  "workdir": "./workspace"
}

# 列出会话
GET /api/v1/agentcore/sessions

# 获取会话详情
GET /api/v1/agentcore/sessions/{session_id}
```

### Agent 执行

```bash
# 运行 Agent
POST /api/v1/agentcore/sessions/{session_id}/run
{
  "query": "List all files in current directory"
}
```

### 数据查询

```bash
# 获取执行时间线
GET /api/v1/agentcore/sessions/{session_id}/timeline

# 获取执行图谱
GET /api/v1/agentcore/sessions/{session_id}/graph

# 获取工具统计
GET /api/v1/agentcore/sessions/{session_id}/tools/stats
```

### WebSocket

```javascript
const ws = new WebSocket(
  'ws://localhost:8000/api/v1/agentcore/ws/sessions/{session_id}'
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data.data);
};
```

## 代码示例

### 基础使用

```python
from app.agentcore import ExecutionEngine

# 创建执行引擎
engine = ExecutionEngine()

# 创建会话
session_id = engine.create_session(
    name="Test Session",
    workdir="./workspace"
)

# 运行 Agent
result = engine.run_agent(
    session_id=session_id,
    query="List all files"
)

# 获取执行图谱
graph = engine.get_execution_graph(session_id)
```

### 自定义 Agent

```python
from app.agentcore import GraphAwareAgent, ToolsMixin, TodoMixin

class MyAgent(ToolsMixin, TodoMixin, GraphAwareAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system_prompt = "You are a helpful assistant"

# 使用
agent = MyAgent(session_id="sess_123")
messages = agent.run([{"role": "user", "content": "Hello"}])
```

### 图谱查询

```python
from app.agentcore.graph import GraphRepository

repo = GraphRepository()

# 获取执行时间线
timeline = repo.get_step_timeline("sess_123")

# 获取工具统计
stats = repo.get_tool_stats("sess_123")
```

## 前端界面

访问 http://localhost:3000/agentcore 查看可视化界面

功能：
- 会话管理
- 实时执行追踪
- 工具调用查看
- 执行时间线

## 架构

```
┌─────────────────────────────────────────────┐
│                 Frontend                     │
│  React + TypeScript + Tailwind CSS          │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│                 FastAPI                      │
│  REST API + WebSocket                       │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│              ExecutionEngine                 │
│  GraphAwareAgent + Mixins                   │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│            GraphRepository                   │
│  Kuzu Graph Database                        │
└─────────────────────────────────────────────┘
```

## 测试

```bash
# 运行 API 测试
python test_agentcore.py
```

## 开发

### 添加新的 Mixin

```python
class MyMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _init_tools(self):
        super()._init_tools()
        self.register_tool(
            name="my_tool",
            handler=self.my_handler,
            description="My tool",
            parameters={}
        )
```

### 添加新的节点类型

1. 在 `graph/models.py` 定义模型
2. 在 `graph/database.py` 创建表
3. 在 `graph/repository.py` 添加操作方法

## 许可证

MIT
