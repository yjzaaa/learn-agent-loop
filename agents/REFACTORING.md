# 面向对象重构说明

## 概述

本项目从原始的函数式代码重构为面向对象的架构，通过提取公共基类和混入类(Mixin)来实现代码复用和模块化。

## 重构前的问题

原始代码存在大量重复：
- 每个文件都重复定义 `safe_path`, `run_bash`, `run_read` 等基础函数
- Agent 循环逻辑在每个文件中重复
- 工具注册方式不一致
- 难以组合多个功能

## 重构后的架构

```
agents/
├── core/                           # 核心框架
│   ├── __init__.py                # 导出公共接口
│   ├── client.py                  # LLM 客户端配置
│   ├── base_agent.py              # Agent 基类
│   └── mixins.py                  # 功能混入类
├── agent_s01.py ~ agent_s09.py    # 各阶段 Agent 实现
├── agent_full.py                  # 完整功能 Agent
└── s01_agent_loop.py ~ s_full.py  # 原始文件（保留）
```

## 核心组件

### 1. BaseAgent (基类)

提供所有 Agent 共用的基础功能：
- 客户端配置（client, model, workdir）
- 工具注册和执行机制
- Agent 循环核心逻辑
- 消息历史管理
- 钩子方法（pre_loop_hook, post_loop_hook）

```python
class MyAgent(BaseAgent):
    def _init_tools(self):
        self.register_tool("my_tool", handler, "Description", {...}, ["required"])
    
    def pre_loop_hook(self, messages):
        # 每次 LLM 调用前执行
        pass
```

### 2. Mixin 类

每个 Mixin 提供特定功能：

| Mixin | 功能 | 工具 |
|-------|------|------|
| `ToolsMixin` | 基础文件操作 | bash, read_file, write_file, edit_file |
| `TodoMixin` | 待办事项管理 | todo |
| `TaskMixin` | 持久化任务系统 | task_create, task_update, task_list, task_get |
| `SkillMixin` | 技能加载 | load_skill |
| `CompressionMixin` | 上下文压缩 | compact |
| `BackgroundMixin` | 后台任务 | background_run, check_background |
| `SubagentMixin` | 子代理 | task |
| `TeamMixin` | 团队协作 | spawn_teammate, list_teammates, send_message, read_inbox, broadcast |

### 3. Mixin 组合示例

```python
# S03: 基础工具 + 待办事项
class S03Agent(TodoMixin, ToolsMixin, BaseAgent):
    pass

# S08: 基础工具 + 后台任务
class S08Agent(BackgroundMixin, ToolsMixin, BaseAgent):
    pass

# Full: 所有功能组合
class FullAgent(
    CompressionMixin,
    TeamMixin,
    BackgroundMixin,
    TodoMixin,
    SubagentMixin,
    SkillMixin,
    TaskMixin,
    ToolsMixin,
    BaseAgent,
):
    pass
```

## 使用方式

### 运行重构后的 Agent

```bash
# 运行特定阶段的 Agent
cd agents
python agent_s03.py

# 运行完整 Agent
python agent_full.py
```

### 在代码中使用

```python
from agent_full import FullAgent

agent = FullAgent()

# 非交互式使用
messages = [{"role": "user", "content": "List all files"}]
result = agent.run(messages)

# 交互式使用
agent.interactive_mode("my_agent >> ")
```

## 代码统计对比

### 原始代码（部分文件）

| 文件 | 行数 | 重复代码估算 |
|------|------|-------------|
| s01_agent_loop.py | 123 | - |
| s02_tool_use.py | 209 | ~60% |
| s03_todo_write.py | 303 | ~50% |
| s04_subagent.py | 186 | ~50% |
| s07_task_system.py | 244 | ~50% |
| **总计** | **~1000+** | **~50-60%** |

### 重构后代码

| 文件 | 行数 | 说明 |
|------|------|------|
| core/base_agent.py | ~280 | 基类（一次编写） |
| core/mixins.py | ~1000 | 所有 Mixin（一次编写） |
| core/client.py | ~40 | 客户端配置 |
| agent_s01.py ~ agent_s09.py | ~50-100 每个 | 只需设置系统提示词 |
| agent_full.py | ~100 | 组合所有功能 |

**优势**：
- 新增功能只需添加 Mixin，无需复制代码
- 修改通用逻辑只需修改一处
- 清晰的依赖关系（通过 Mixin 顺序）

## 扩展指南

### 添加新的 Mixin

```python
class MyFeatureMixin(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化你的功能
    
    def _init_tools(self) -> None:
        super()._init_tools()
        self.register_tool(
            name="my_tool",
            handler=self.handle_my_tool,
            description="My tool description",
            parameters={"arg": {"type": "string"}},
            required=["arg"]
        )
    
    def handle_my_tool(self, arg: str) -> str:
        return f"Result: {arg}"
```

### 创建自定义 Agent

```python
class MyAgent(MyFeatureMixin, ToolsMixin, BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system_prompt = "You are a custom agent..."
```

## 注意事项

1. **Mixin 顺序很重要**：Python 的 MRO（方法解析顺序）从左到右
2. **始终调用 super()**：确保所有 Mixin 的初始化都被执行
3. **_init_tools 方法**：在 __init__ 完成后调用，可以安全地使用 self 属性
4. **钩子方法**：pre_loop_hook 和 post_loop_hook 会自动调用所有 Mixin 的实现
