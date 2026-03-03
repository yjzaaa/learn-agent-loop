# AgentCore 知识图谱设计文档

## 1. 设计目标

将 `agents/agent_full.py` 重构为 `backend/agentcore`，实现以**知识图谱形式**运行和观察 Agent 的核心逻辑。

### 核心洞察
> "运行状态即图谱，执行流程即遍历。"

---

## 2. 前端 UI 设计参考 (GitNexus Web)

前端 UI 设计参考 **gitnexus-web** 的设计风格，采用深色主题、科技感和数据可视化的设计语言。

### 2.1 设计系统

#### 颜色系统

| 颜色名称 | 值 | 用途 |
|---------|-----|------|
| **Backgrounds** |||
| `--color-void` | `#06060a` | 主背景色 |
| `--color-deep` | `#0a0a10` | 次级背景、头部/底部 |
| `--color-surface` | `#101018` | 卡片、面板背景 |
| `--color-elevated` | `#16161f` | 按钮、输入框背景 |
| `--color-hover` | `#1c1c28` | 悬停状态 |
| **Borders** |||
| `--color-border-subtle` | `#1e1e2a` | 细边框、分隔线 |
| `--color-border-default` | `#2a2a3a` | 默认边框 |
| **Text** |||
| `--color-text-primary` | `#e4e4ed` | 主要文字 |
| `--color-text-secondary` | `#8888a0` | 次要文字 |
| `--color-text-muted` | `#5a5a70` | 禁用/提示文字 |
| **Accent** |||
| `--color-accent` | `#7c3aed` | 主强调色（紫罗兰） |
| `--color-accent-dim` | `#5b21b6` | 深强调色 |
| **Node Colors** |||
| `--color-node-file` | `#3b82f6` | 文件节点（蓝） |
| `--color-node-folder` | `#6366f1` | 文件夹节点（靛蓝） |
| `--color-node-class` | `#f59e0b` | 类节点（琥珀） |
| `--color-node-function` | `#10b981` | 函数节点（翠绿） |
| `--color-node-interface` | `#ec4899` | 接口节点（粉） |
| `--color-node-method` | `#14b8a6` | 方法节点（青） |

#### 字体系统

```css
--font-sans: 'Outfit', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

| 样式 | 大小 | 字重 | 用途 |
|-----|------|-----|------|
| Logo | 15px | 600 | 品牌标识 |
| 标题 | 14-18px | 600 | 面板标题 |
| 正文 | 14px | 400 | 主要内容 |
| 小字 | 12px | 400 | 次要信息 |
| 标签 | 10-11px | 500 | 标签、状态 |
| 代码 | 12-14px | 400 | 代码块、JSON |

#### 阴影与光效

```css
--shadow-glow: 0 0 20px rgba(124, 58, 237, 0.4);
--shadow-glow-soft: 0 0 40px rgba(124, 58, 237, 0.15);
```

#### 动画效果

| 动画 | 时长 | 用途 |
|-----|------|------|
| `--animate-breathe` | 3s infinite | 呼吸边框效果 |
| `--animate-pulse-glow` | 2s infinite | 脉冲发光 |
| `--animate-slide-in` | 0.3s | 滑入进入 |
| `--animate-slide-up` | 0.3s | 上滑进入 |
| `--animate-fade-in` | 0.3s | 淡入 |

### 2.2 布局结构

参考 GitNexus Web 的三栏布局：

```
┌─────────────────────────────────────────────────────────────────┐
│  Header (Logo | Search | Stats | Actions)                       │
├──────────┬──────────────────────────────────┬───────────────────┤
│          │                                  │                   │
│  Left    │         Graph Canvas             │     Right Panel   │
│  Panel   │      (Knowledge Graph View)      │   (Code | Chat)   │
│ (Tree/   │                                  │                   │
│  List)   │   ┌──────────────────────────┐   │   ┌───────────┐   │
│          │   │   Floating Controls      │   │   │   Tabs    │   │
│          │   │   (Zoom | Layout | AI)   │   │   ├───────────┤   │
│          │   └──────────────────────────┘   │   │  Content  │   │
│          │                                  │   │           │   │
├──────────┴──────────────────────────────────┴───┴───────────┤   │
│  Status Bar (Progress | Stats | Info)                         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 组件设计规范

#### 按钮样式

**主按钮（Primary）**
```tsx
className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-medium 
           bg-gradient-to-r from-accent to-accent-dim text-white 
           shadow-glow hover:shadow-lg hover:-translate-y-0.5 transition-all"
```

**图标按钮（Icon）**
```tsx
className="w-9 h-9 flex items-center justify-center rounded-md 
           bg-elevated border border-border-subtle 
           text-text-secondary hover:bg-hover hover:text-text-primary transition-colors"
```

**状态按钮（Active）**
```tsx
className="w-9 h-9 flex items-center justify-center rounded-md 
           bg-accent/20 border border-accent/30 text-accent 
           hover:bg-accent/30 transition-colors"
```

#### 卡片样式

**工具调用卡片（ToolCallCard）**
```tsx
// 不同状态的颜色
const statusStyles = {
  running: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
  },
  completed: {
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    text: 'text-emerald-400',
  },
  error: {
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/30',
    text: 'text-rose-400',
  },
};

// 结构
<div className={`rounded-lg border ${borderColor} ${bgColor} overflow-hidden`}>
  {/* Header - 可点击展开/收起 */}
  <div className="flex items-center gap-2 px-3 py-2 hover:bg-white/5 cursor-pointer">
    <ChevronIcon />
    <span className="flex-1 text-sm font-medium">Tool Name</span>
    <StatusIndicator />
  </div>
  {/* Expanded Content */}
  <div className="border-t border-border-subtle/50">
    <pre className="text-xs bg-surface/50 rounded p-2 font-mono">...</pre>
  </div>
</div>
```

#### 输入框样式

**搜索输入框**
```tsx
<div className="flex items-center gap-2.5 px-3.5 py-2 
                bg-surface border border-border-subtle rounded-lg 
                focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/20">
  <Search className="w-4 h-4 text-text-muted" />
  <input className="flex-1 bg-transparent border-none outline-none 
                   text-sm text-text-primary placeholder:text-text-muted" />
  <kbd className="px-1.5 py-0.5 bg-elevated border border-border-subtle 
                 rounded text-[10px] text-text-muted font-mono">⌘K</kbd>
</div>
```

### 2.4 知识图谱可视化

#### 节点样式

| 节点类型 | 颜色 | 形状 | 大小 |
|---------|------|------|------|
| AgentSession | `#7c3aed` | 圆形 | 大 |
| ExecutionStep | `#6366f1` | 方形 | 中 |
| ToolCall | `#10b981` | 菱形 | 小 |
| Message | `#3b82f6` | 圆形 | 小 |
| Task | `#f59e0b` | 六边形 | 中 |
| Todo | `#14b8a6` | 矩形 | 小 |

#### 边样式

| 关系类型 | 颜色 | 样式 | 动画 |
|---------|------|------|------|
| HAS_STEP | `#5a5a70` | 实线 | 无 |
| NEXT_STEP | `#7c3aed` | 实线 | 流动 |
| CALLS_TOOL | `#10b981` | 虚线 | 脉冲 |
| PRODUCES | `#3b82f6` | 实线 | 无 |
| DEPENDS_ON | `#f59e0b` | 实线 | 无 |

#### 交互效果

**节点悬停**
- 放大 1.1 倍
- 显示工具提示（节点名称）
- 高亮相邻边

**节点选中**
- 添加发光阴影 `shadow-glow`
- 顶部显示信息栏
- 右侧面板显示详情

**执行动画**
- 当前执行步骤：脉冲发光
- 工具调用中：流动边动画
- 完成状态：绿色高亮

### 2.5 响应式设计

| 断点 | 宽度 | 布局调整 |
|-----|------|---------|
| Desktop XL | ≥1440px | 三栏布局，完整显示 |
| Desktop | ≥1280px | 三栏布局 |
| Tablet | ≥768px | 双栏布局，右侧面板可收起 |
| Mobile | <768px | 单栏布局，抽屉式面板 |

---

## 3. 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AgentCore Knowledge Graph                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Session    │◄──►│  Execution   │◄──►│    Tool      │                   │
│  │    Node      │    │  Process     │    │    Node      │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Message    │◄──►│   State      │◄──►│  Artifact    │                   │
│  │    Node      │    │   Node       │    │    Node      │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │     Task     │◄──►│    Team      │◄──►│   Skill      │                   │
│  │    Node      │    │   Node       │    │    Node      │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Kuzu Graph Database                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 节点类型 (Node Types)

| 节点类型 | 描述 | 对应原功能 |
|---------|------|-----------|
| `AgentSession` | Agent 会话实例 | BaseAgent 实例 |
| `ExecutionStep` | 执行步骤（LLM调用或工具执行） | run() 循环迭代 |
| `ToolCall` | 工具调用记录 | _execute_tools() |
| `Message` | 消息节点（user/assistant/system/tool） | messages[] |
| `AgentState` | Agent 状态快照 | Mixin 状态 |
| `Task` | 任务节点 | TaskMixin |
| `Todo` | 待办事项 | TodoMixin |
| `Skill` | 技能节点 | SkillMixin |
| `Teammate` | 团队成员 | TeamMixin |
| `BackgroundJob` | 后台任务 | BackgroundMixin |
| `SubagentRun` | 子代理运行 | SubagentMixin |
| `Artifact` | 生成的文件/数据 | 文件操作结果 |
| `Compression` | 压缩记录 | CompressionMixin |

### 3.3 关系类型 (Relationship Types)

| 关系类型 | 源节点 | 目标节点 | 描述 |
|---------|-------|---------|------|
| `HAS_STEP` | AgentSession | ExecutionStep | 会话包含执行步骤 |
| `NEXT_STEP` | ExecutionStep | ExecutionStep | 执行顺序 |
| `CALLS_TOOL` | ExecutionStep | ToolCall | 调用工具 |
| `PRODUCES` | ToolCall | Message | 产生消息 |
| `DEPENDS_ON` | Task | Task | 任务依赖 |
| `HAS_TODO` | AgentSession | Todo | 会话有待办 |
| `USES_SKILL` | ExecutionStep | Skill | 使用技能 |
| `HAS_TEAMMEMBER` | AgentSession | Teammate | 有团队成员 |
| `SENDS_MESSAGE` | Teammate | Teammate | 发送消息 |
| `TRIGGERS_COMPRESSION` | ExecutionStep | Compression | 触发压缩 |
| `SPAWNS_SUBAGENT` | ExecutionStep | SubagentRun | 产生子代理 |
| `CREATES_ARTIFACT` | ToolCall | Artifact | 创建产物 |

---

## 4. 数据模型

### 4.1 AgentSession 节点

```cypher
CREATE NODE TABLE AgentSession (
    id STRING PRIMARY KEY,           // 会话唯一ID
    name STRING,                     // 会话名称
    workdir STRING,                  // 工作目录
    model STRING,                    // 使用模型
    systemPrompt STRING,             // 系统提示词
    status STRING,                   // active | paused | completed | error
    startedAt TIMESTAMP,             // 开始时间
    endedAt TIMESTAMP,               // 结束时间
    maxTokens INT64,                 // 最大token数
    totalSteps INT64,                // 总执行步数
    totalToolCalls INT64,            // 总工具调用数
    metadata STRING                  // JSON 元数据
)
```

### 4.2 ExecutionStep 节点

```cypher
CREATE NODE TABLE ExecutionStep (
    id STRING PRIMARY KEY,           // 步骤ID (session_id:step_num)
    stepNumber INT64,                // 步骤序号
    type STRING,                     // llm_call | tool_execution | hook
    status STRING,                   // running | completed | error
    startedAt TIMESTAMP,
    endedAt TIMESTAMP,
    durationMs INT64,                // 执行耗时
    tokenCount INT64,                // token 数量
    finishReason STRING,             // stop | tool_calls | length | error
    metadata STRING                  // JSON 元数据
)
```

### 4.3 ToolCall 节点

```cypher
CREATE NODE TABLE ToolCall (
    id STRING PRIMARY KEY,           // 工具调用ID
    name STRING,                     // 工具名称
    arguments STRING,                // JSON 参数
    output STRING,                   // 输出结果
    outputPreview STRING,            // 输出预览(前200字符)
    status STRING,                   // success | error | blocked
    errorMessage STRING,             // 错误信息
    startedAt TIMESTAMP,
    endedAt TIMESTAMP,
    durationMs INT64
)
```

### 4.4 Message 节点

```cypher
CREATE NODE TABLE Message (
    id STRING PRIMARY KEY,           // 消息ID
    role STRING,                     // system | user | assistant | tool
    content STRING,                  // 消息内容
    contentPreview STRING,           // 内容预览
    toolCalls STRING,                // JSON 工具调用
    tokenCount INT64,                // 预估token数
    createdAt TIMESTAMP,
    compressionRef STRING            // 压缩引用
)
```

### 4.5 AgentState 节点

```cypher
CREATE NODE TABLE AgentState (
    id STRING PRIMARY KEY,
    stateType STRING,                // todo | task | team | background
    data STRING,                     // JSON 状态数据
    updatedAt TIMESTAMP
)
```

### 4.6 Task 节点

```cypher
CREATE NODE TABLE Task (
    id STRING PRIMARY KEY,
    taskId INT64,                    // 任务数字ID
    subject STRING,                  // 主题
    description STRING,              // 描述
    status STRING,                   // pending | in_progress | completed
    owner STRING,                    // 负责人
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    completedAt TIMESTAMP
)
```

### 4.7 Todo 节点

```cypher
CREATE NODE TABLE Todo (
    id STRING PRIMARY KEY,
    itemId STRING,                   // 事项ID
    text STRING,                     // 内容
    status STRING,                   // pending | in_progress | completed
    updatedAt TIMESTAMP
)
```

### 4.8 Skill 节点

```cypher
CREATE NODE TABLE Skill (
    id STRING PRIMARY KEY,
    name STRING,                     // 技能名称
    description STRING,              // 描述
    tags STRING,                     // 标签
    body STRING,                     // 技能内容
    filePath STRING                  // 文件路径
)
```

### 4.9 Teammate 节点

```cypher
CREATE NODE TABLE Teammate (
    id STRING PRIMARY KEY,
    name STRING,                     // 名称
    role STRING,                     // 角色
    status STRING,                   // idle | working | shutdown
    prompt STRING,                   // 提示词
    threadId STRING                  // 线程ID
)
```

### 4.10 BackgroundJob 节点

```cypher
CREATE NODE TABLE BackgroundJob (
    id STRING PRIMARY KEY,
    taskId STRING,                   // 任务ID
    command STRING,                  // 命令
    status STRING,                   // running | completed | error | timeout
    result STRING,                   // 结果
    startedAt TIMESTAMP,
    endedAt TIMESTAMP
)
```

### 4.11 SubagentRun 节点

```cypher
CREATE NODE TABLE SubagentRun (
    id STRING PRIMARY KEY,
    prompt STRING,                   // 提示词
    agentType STRING,                // Explore | general-purpose
    maxRounds INT64,                 // 最大轮数
    actualRounds INT64,              // 实际轮数
    status STRING,                   // running | completed | error
    summary STRING,                  // 执行摘要
    startedAt TIMESTAMP,
    endedAt TIMESTAMP
)
```

### 4.12 Artifact 节点

```cypher
CREATE NODE TABLE Artifact (
    id STRING PRIMARY KEY,
    type STRING,                     // file | data | output
    name STRING,                     // 名称
    filePath STRING,                 // 文件路径
    contentPreview STRING,           // 内容预览
    sizeBytes INT64,                 // 大小
    createdAt TIMESTAMP
)
```

### 4.13 Compression 节点

```cypher
CREATE NODE TABLE Compression (
    id STRING PRIMARY KEY,
    type STRING,                     // micro | auto | manual
    transcriptPath STRING,           // 转录文件路径
    summary STRING,                  // 摘要内容
    originalTokens INT64,            // 原始token数
    compressedTokens INT64,          // 压缩后token数
    createdAt TIMESTAMP
)
```

### 4.14 关系表

```cypher
CREATE REL TABLE HAS_STEP (
    FROM AgentSession TO ExecutionStep,
    MANY_MANY
)

CREATE REL TABLE NEXT_STEP (
    FROM ExecutionStep TO ExecutionStep,
    ONE_ONE
)

CREATE REL TABLE CALLS_TOOL (
    FROM ExecutionStep TO ToolCall,
    MANY_MANY,
    callOrder INT64                  // 调用顺序
)

CREATE REL TABLE PRODUCES (
    FROM ToolCall TO Message,
    MANY_MANY
)

CREATE REL TABLE HAS_MESSAGE (
    FROM ExecutionStep TO Message,
    MANY_MANY
)

CREATE REL TABLE IN_STATE (
    FROM AgentSession TO AgentState,
    MANY_MANY,
    stateType STRING
)

CREATE REL TABLE DEPENDS_ON (
    FROM Task TO Task,
    MANY_MANY
)

CREATE REL TABLE HAS_TASK (
    FROM AgentSession TO Task,
    MANY_MANY
)

CREATE REL TABLE HAS_TODO (
    FROM AgentSession TO Todo,
    MANY_MANY,
    orderIdx INT64
)

CREATE REL TABLE USES_SKILL (
    FROM ExecutionStep TO Skill,
    MANY_MANY
)

CREATE REL TABLE HAS_TEAMMEMBER (
    FROM AgentSession TO Teammate,
    MANY_MANY
)

CREATE REL TABLE SENDS_MESSAGE (
    FROM Teammate TO Teammate,
    MANY_MANY,
    msgType STRING,
    content STRING,
    sentAt TIMESTAMP
)

CREATE REL TABLE TRIGGERS_COMPRESSION (
    FROM ExecutionStep TO Compression,
    MANY_MANY
)

CREATE REL TABLE SPAWNS_SUBAGENT (
    FROM ExecutionStep TO SubagentRun,
    MANY_MANY
)

CREATE REL TABLE CREATES_ARTIFACT (
    FROM ToolCall TO Artifact,
    MANY_MANY
)
```

---

## 5. 核心执行流程

### 5.1 Agent 运行时的图谱构建

```
用户输入
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  1. 创建 ExecutionStep (type="llm_call")                    │
│     - 记录开始时间、token数                                   │
│     - 创建 HAS_STEP 关系                                     │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  2. 调用 LLM                                                 │
│     - 等待响应                                               │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  3. 创建 Message (role="assistant")                         │
│     - 存储响应内容                                           │
│     - 创建 HAS_MESSAGE 关系                                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  4. 更新 ExecutionStep                                       │
│     - 完成时间、finish_reason                               │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  5. 检查 finish_reason                                       │
│     - 非 "tool_calls" → 流程结束                             │
│     - "tool_calls" → 继续工具执行                            │
└─────────────────────────────────────────────────────────────┘
    │
    ▼ (有工具调用)
┌─────────────────────────────────────────────────────────────┐
│  6. 创建 ExecutionStep (type="tool_execution")              │
│     - 创建 NEXT_STEP 关系链接上一步                          │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  7. 为每个工具调用创建 ToolCall 节点                          │
│     - 记录工具名称、参数、输出                                 │
│     - 创建 CALLS_TOOL 关系                                   │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  8. 创建 Message (role="tool")                              │
│     - 存储工具结果                                           │
│     - 创建 PRODUCES 关系                                     │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  9. 执行钩子 (pre_loop/post_loop)                           │
│     - 检查 Todo、Background、Team 等状态                     │
│     - 更新相应的 State 节点                                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  10. 检查压缩条件                                            │
│     - token > 阈值 → 创建 Compression 节点                   │
│     - 创建 TRIGGERS_COMPRESSION 关系                         │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
    └───────────────────────┐
                            │
                            ▼
                    回到步骤 1 (循环)
```

### 5.2 Mixin 状态追踪

每个 Mixin 在钩子中更新对应的 State 节点：

| Mixin | 状态追踪 | 图谱操作 |
|-------|---------|---------|
| `TodoMixin` | 待办列表 | 创建/更新 Todo 节点 |
| `TaskMixin` | 任务图 | 创建 Task 节点和 DEPENDS_ON 关系 |
| `SkillMixin` | 技能加载 | 创建 Skill 节点，USES_SKILL 关系 |
| `BackgroundMixin` | 后台任务 | 创建 BackgroundJob 节点 |
| `TeamMixin` | 团队成员 | 创建 Teammate 节点和 SENDS_MESSAGE 关系 |
| `SubagentMixin` | 子代理 | 创建 SubagentRun 节点 |
| `CompressionMixin` | 压缩记录 | 创建 Compression 节点 |

---

## 6. 查询接口设计

### 6.1 获取会话执行流程

```cypher
// 获取完整执行链
MATCH (s:AgentSession {id: $sessionId})-[:HAS_STEP]->(step:ExecutionStep)
OPTIONAL MATCH (step)-[:CALLS_TOOL]->(tool:ToolCall)
OPTIONAL MATCH (step)-[:HAS_MESSAGE]->(msg:Message)
OPTIONAL MATCH (step)-[:NEXT_STEP]->(next:ExecutionStep)
RETURN step, tool, msg, next
ORDER BY step.stepNumber
```

### 6.2 获取工具调用统计

```cypher
// 统计各工具使用频率
MATCH (s:AgentSession {id: $sessionId})-[:HAS_STEP]->(:ExecutionStep)-[:CALLS_TOOL]->(tool:ToolCall)
RETURN tool.name as tool_name, 
       count(*) as call_count,
       avg(tool.durationMs) as avg_duration,
       sum(CASE WHEN tool.status = 'error' THEN 1 ELSE 0 END) as error_count
ORDER BY call_count DESC
```

### 6.3 获取任务依赖图

```cypher
// 获取任务依赖关系
MATCH (t:Task)<-[:HAS_TASK]-(s:AgentSession {id: $sessionId})
OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Task)
RETURN t.id, t.subject, t.status, collect(dep.id) as dependencies
```

### 6.4 获取执行时间线

```cypher
// 获取执行时间线
MATCH (s:AgentSession {id: $sessionId})-[:HAS_STEP]->(step:ExecutionStep)
RETURN step.stepNumber,
       step.type,
       step.startedAt,
       step.endedAt,
       step.durationMs,
       step.tokenCount
ORDER BY step.stepNumber
```

### 6.5 获取活跃后台任务

```cypher
// 获取活跃的后台任务
MATCH (s:AgentSession {id: $sessionId})-[:HAS_STEP]->(step:ExecutionStep)-[:CALLS_TOOL]->(tool:ToolCall)
WHERE tool.name = 'background_run'
MATCH (tool)-[:PRODUCES]->(msg:Message)
WHERE msg.content CONTAINS 'task'
RETURN tool.id, tool.arguments, tool.startedAt
```

---

## 7. API 设计

### 7.1 REST API 端点

```
POST   /api/v1/sessions              # 创建会话
GET    /api/v1/sessions              # 列会话
GET    /api/v1/sessions/{id}         # 获取会话详情
POST   /api/v1/sessions/{id}/run     # 运行 Agent
POST   /api/v1/sessions/{id}/pause   # 暂停会话
DELETE /api/v1/sessions/{id}         # 删除会话

GET    /api/v1/sessions/{id}/steps              # 获取执行步骤
GET    /api/v1/sessions/{id}/graph              # 获取执行图谱
GET    /api/v1/sessions/{id}/timeline           # 获取时间线
GET    /api/v1/sessions/{id}/tools/stats        # 工具统计

GET    /api/v1/sessions/{id}/tasks              # 任务列表
POST   /api/v1/sessions/{id}/tasks              # 创建任务
PUT    /api/v1/sessions/{id}/tasks/{taskId}     # 更新任务

GET    /api/v1/sessions/{id}/todos              # 待办列表

GET    /api/v1/sessions/{id}/teammates          # 团队成员

GET    /api/v1/sessions/{id}/artifacts          # 产物列表
```

### 7.2 WebSocket 实时推送

```javascript
// 连接 WebSocket
ws = new WebSocket('ws://localhost:8000/ws/sessions/{sessionId}')

// 接收实时事件
{
  "type": "step_start",
  "data": {
    "stepId": "sess_001:step_5",
    "stepNumber": 5,
    "type": "llm_call",
    "startedAt": "2026-03-03T14:00:00Z"
  }
}

{
  "type": "tool_call",
  "data": {
    "toolId": "tool_123",
    "name": "bash",
    "arguments": {"command": "ls -la"},
    "status": "running"
  }
}

{
  "type": "step_end",
  "data": {
    "stepId": "sess_001:step_5",
    "finishReason": "tool_calls",
    "durationMs": 2500,
    "tokenCount": 1500
  }
}

{
  "type": "state_change",
  "data": {
    "stateType": "todo",
    "todos": [...]
  }
}
```

---

## 8. 前端组件设计

### 8.1 页面结构

参考 GitNexus Web 的三栏布局：

```
┌─────────────────────────────────────────────────────────────────┐
│  Header (Logo | Session Selector | Search | Stats | Actions)   │
├──────────┬──────────────────────────────────┬───────────────────┤
│          │                                  │                   │
│  Left    │         Graph Canvas             │     Right Panel   │
│  Panel   │    (Agent Execution Graph)       │  (Details|Chat)   │
│          │                                  │                   │
│  - Steps │   ┌──────────────────────────┐   │   ┌───────────┐   │
│  - Tasks │   │   Floating Controls      │   │   │   Tabs    │   │
│  - Tools │   │   (Zoom | Layout | AI)   │   │   ├───────────┤   │
│          │   └──────────────────────────┘   │   │  Content  │   │
│          │                                  │   │           │   │
├──────────┴──────────────────────────────────┴───┴───────────┤   │
│  Status Bar (Progress | Token Usage | Step Count)             │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 核心组件

#### AgentGraphCanvas - 执行图谱可视化

```tsx
interface AgentGraphCanvasProps {
  sessionId: string;
  onNodeSelect: (node: GraphNode) => void;
  highlightedNodes: Set<string>;
  animatedNodes: Map<string, AnimationState>;
}

// 使用 Sigma.js 进行图谱渲染
// 支持力导向布局
// 节点悬停/选中高亮
// 实时执行动画
```

#### ToolCallPanel - 工具调用详情

```tsx
interface ToolCallPanelProps {
  toolCalls: ToolCallInfo[];
  onToolSelect: (toolId: string) => void;
  expandedByDefault?: boolean;
}

// 可展开/收起的工具调用卡片
// 显示参数和结果
// 状态指示（运行中/完成/错误）
```

#### ExecutionTimeline - 执行时间线

```tsx
interface ExecutionTimelineProps {
  steps: ExecutionStep[];
  currentStep: number;
  onStepClick: (stepNumber: number) => void;
}

// 垂直时间线布局
// 步骤状态指示
// 点击跳转
```

#### SessionOverview - 会话概览

```tsx
interface SessionOverviewProps {
  session: AgentSession;
  stats: SessionStats;
}

// 会话基本信息
// 统计卡片（步数、工具调用、Token）
// 状态指示器
```

### 8.3 状态管理

使用 Zustand 进行状态管理：

```typescript
interface AgentCoreState {
  // 会话状态
  sessions: AgentSession[];
  currentSession: AgentSession | null;
  
  // 图谱数据
  graph: KnowledgeGraph | null;
  selectedNode: GraphNode | null;
  highlightedNodes: Set<string>;
  
  // 执行状态
  isRunning: boolean;
  currentStep: number;
  
  // UI 状态
  leftPanelOpen: boolean;
  rightPanelOpen: boolean;
  rightPanelTab: 'details' | 'chat' | 'tools';
  
  // 操作
  createSession: (config: SessionConfig) => Promise<void>;
  runAgent: (sessionId: string, query: string) => Promise<void>;
  selectNode: (nodeId: string) => void;
  togglePanel: (panel: 'left' | 'right') => void;
}
```

---

## 9. 实现架构

### 9.1 模块结构

```
backend/app/agentcore/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── base_agent.py          # 基础 Agent 类（图谱感知）
│   ├── mixins.py              # Mixin 类（图谱集成）
│   └── client.py              # LLM 客户端
├── graph/
│   ├── __init__.py
│   ├── database.py            # Kuzu 数据库连接
│   ├── models.py              # Pydantic 模型
│   ├── repository.py          # 图谱操作仓库
│   └── queries.py             # 查询构建器
├── execution/
│   ├── __init__.py
│   ├── engine.py              # 执行引擎
│   ├── observer.py            # 执行观察器
│   └── events.py              # 事件系统
├── api/
│   ├── __init__.py
│   ├── router.py              # API 路由
│   └── schemas.py             # API 模式
└── ws/
    ├── __init__.py
    └── handler.py             # WebSocket 处理器
```

### 9.2 核心类设计

#### GraphAwareAgent (继承自 BaseAgent)

```python
class GraphAwareAgent(BaseAgent):
    """图谱感知的 Agent 基类"""
    
    def __init__(self, session_id: str, graph_repo: GraphRepository, **kwargs):
        super().__init__(**kwargs)
        self.session_id = session_id
        self.graph_repo = graph_repo
        self._current_step: Optional[str] = None
        
    def run(self, messages: Optional[list] = None) -> list:
        """运行 Agent，同时构建知识图谱"""
        messages = messages or []
        
        while True:
            # 1. 创建执行步骤节点
            step = self.graph_repo.create_execution_step(
                session_id=self.session_id,
                step_type="llm_call",
                step_number=self._get_next_step_number()
            )
            self._current_step = step.id
            
            # 2. 执行 LLM 调用
            response = self._call_llm(messages)
            
            # 3. 更新步骤节点
            self.graph_repo.update_execution_step(
                step_id=step.id,
                finish_reason=response.finish_reason,
                token_count=response.usage.total_tokens if response.usage else 0
            )
            
            # 4. 创建消息节点
            msg = self.graph_repo.create_message(
                step_id=step.id,
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls
            )
            
            # 5. 检查是否结束
            if response.finish_reason != "tool_calls":
                break
                
            # 6. 执行工具并记录
            self._execute_tools_with_graph(response.tool_calls, step.id)
            
        return messages
```

#### GraphRepository

```python
class GraphRepository:
    """知识图谱操作仓库"""
    
    def __init__(self, db: KuzuDatabase):
        self.db = db
        
    def create_execution_step(self, session_id: str, step_type: str, 
                              step_number: int) -> ExecutionStep:
        """创建执行步骤节点"""
        step_id = f"{session_id}:step_{step_number}"
        query = """
        CREATE (s:ExecutionStep {
            id: $step_id,
            stepNumber: $step_number,
            type: $step_type,
            status: 'running',
            startedAt: timestamp()
        })
        RETURN s
        """
        # 执行查询...
        
    def create_tool_call(self, step_id: str, name: str, 
                         arguments: dict, output: str) -> ToolCall:
        """创建工具调用节点"""
        tool_id = f"{step_id}:tool_{uuid.uuid4().hex[:8]}"
        # 创建节点和关系...
        
    def get_execution_graph(self, session_id: str) -> ExecutionGraph:
        """获取完整执行图谱"""
        query = """
        MATCH (s:AgentSession {id: $session_id})-[:HAS_STEP]->(step:ExecutionStep)
        OPTIONAL MATCH (step)-[:CALLS_TOOL]->(tool:ToolCall)
        OPTIONAL MATCH (step)-[:NEXT_STEP]->(next:ExecutionStep)
        RETURN step, tool, next
        ORDER BY step.stepNumber
        """
        # 执行查询并构建图谱...
```

---

## 10. 观察与调试功能

### 10.1 实时执行观察

```python
class ExecutionObserver:
    """执行观察器 - 用于调试和监控"""
    
    def __init__(self, graph_repo: GraphRepository):
        self.graph_repo = graph_repo
        self._listeners: List[Callable] = []
        
    def on_step_start(self, step: ExecutionStep):
        """步骤开始回调"""
        for listener in self._listeners:
            listener({"type": "step_start", "data": step})
            
    def on_tool_call(self, tool_call: ToolCall):
        """工具调用回调"""
        for listener in self._listeners:
            listener({"type": "tool_call", "data": tool_call})
            
    def on_state_change(self, state_type: str, state_data: dict):
        """状态变更回调"""
        for listener in self._listeners:
            listener({"type": "state_change", "data": {
                "stateType": state_type,
                "data": state_data
            }})
```

### 10.2 执行回放

```python
class ExecutionReplayer:
    """执行回放器 - 重现 Agent 执行过程"""
    
    def __init__(self, graph_repo: GraphRepository):
        self.graph_repo = graph_repo
        
    def replay(self, session_id: str, speed: float = 1.0):
        """回放执行过程"""
        steps = self.graph_repo.get_execution_steps(session_id)
        
        for step in steps:
            # 按原始时间间隔播放
            time.sleep(step.duration_ms / 1000 / speed)
            
            # 显示步骤详情
            self._display_step(step)
            
            # 显示工具调用
            for tool in step.tool_calls:
                self._display_tool_call(tool)
```

---

## 11. 与原功能的映射

| 原功能 | 知识图谱实现 | 节点/关系 |
|-------|------------|----------|
| `BaseAgent.run()` | `GraphAwareAgent.run()` | AgentSession → ExecutionStep |
| `_execute_tools()` | `_execute_tools_with_graph()` | ExecutionStep → ToolCall → Message |
| `TodoMixin` | Todo 节点追踪 | AgentSession → Todo |
| `TaskMixin` | Task 节点 + 依赖关系 | AgentSession → Task → DEPENDS_ON → Task |
| `SkillMixin` | Skill 节点引用 | ExecutionStep → Skill |
| `BackgroundMixin` | BackgroundJob 节点 | AgentSession → BackgroundJob |
| `TeamMixin` | Teammate 节点 + 消息关系 | AgentSession → Teammate → SENDS_MESSAGE → Teammate |
| `SubagentMixin` | SubagentRun 节点 | ExecutionStep → SubagentRun |
| `CompressionMixin` | Compression 节点 | ExecutionStep → Compression |
| 工具历史 `_tool_history` | ToolCall 节点查询 | MATCH (s)-[:HAS_STEP]->(:ExecutionStep)-[:CALLS_TOOL]->(t) |
| 消息历史 `messages[]` | Message 节点链 | MATCH (s)-[:HAS_STEP]->(:ExecutionStep)-[:HAS_MESSAGE]->(m) |

---

## 12. 部署与使用

### 12.1 启动服务

```bash
# 启动后端服务（包含 AgentCore）
cd backend
uvicorn app.main:app --reload

# 访问 API 文档
open http://localhost:8000/docs
```

### 12.2 创建会话并运行

```bash
# 创建会话
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "test-session", "workdir": "/tmp/work"}'

# 运行 Agent
curl -X POST http://localhost:8000/api/v1/sessions/{id}/run \
  -H "Content-Type: application/json" \
  -d '{"query": "List all files in current directory"}'

# 获取执行图谱
curl http://localhost:8000/api/v1/sessions/{id}/graph
```

### 12.3 可视化查看

```bash
# 导出图谱为可视化格式
curl http://localhost:8000/api/v1/sessions/{id}/graph/export?format=cytoscape

# 生成执行报告
curl http://localhost:8000/api/v1/sessions/{id}/report
```

---

## 附录：核心设计决策

### A1. 为什么使用 Kuzu？

1. **本地优先**：无需外部服务器，嵌入在应用中
2. **Cypher 查询**：标准图查询语言，易于使用
3. **性能优秀**：针对分析型查询优化
4. **Python 友好**：有官方 Python 绑定

### A2. 节点粒度设计

- **ExecutionStep**：每个 LLM 调用或工具执行批次一个节点
- **ToolCall**：每个工具调用一个节点（支持并行调用）
- **Message**：每个消息一个节点（便于内容检索）

### A3. 状态分离

- **运行时状态**：内存中（原 Mixin 属性）
- **持久化状态**：图谱中（用于观察和分析）
- **两者同步**：通过钩子方法在关键节点同步

### A4. UI 设计参考 GitNexus Web 的原因

1. **一致性**：与现有 GitNexus 工具保持统一视觉语言
2. **专业性**：深色科技风格适合开发者工具
3. **可扩展性**：组件化设计便于扩展新功能
4. **性能**：Sigma.js 支持大规模图谱渲染

### A5. 扩展性

- 新 Mixin 只需添加对应的 State 节点类型
- 新工具自动创建 ToolCall 节点
- 查询接口可通过 Cypher 灵活扩展
- 前端组件遵循设计系统规范
