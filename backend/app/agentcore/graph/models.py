"""
Graph Data Models

Pydantic models for knowledge graph nodes and relationships
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """会话状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class StepType(str, Enum):
    """执行步骤类型"""
    LLM_CALL = "llm_call"
    TOOL_EXECUTION = "tool_execution"
    HOOK = "hook"


class StepStatus(str, Enum):
    """执行步骤状态"""
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class ToolStatus(str, Enum):
    """工具调用状态"""
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    BLOCKED = "blocked"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TodoStatus(str, Enum):
    """待办状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TeammateStatus(str, Enum):
    """团队成员状态"""
    IDLE = "idle"
    WORKING = "working"
    SHUTDOWN = "shutdown"


class BackgroundJobStatus(str, Enum):
    """后台任务状态"""
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"


class CompressionType(str, Enum):
    """压缩类型"""
    MICRO = "micro"
    AUTO = "auto"
    MANUAL = "manual"


class AgentSession(BaseModel):
    """Agent 会话节点"""
    id: str = Field(..., description="会话唯一ID")
    name: str = Field(..., description="会话名称")
    workdir: str = Field(..., description="工作目录")
    model: str = Field(..., description="使用模型")
    system_prompt: str = Field(..., description="系统提示词")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    max_tokens: int = Field(default=8000)
    total_steps: int = Field(default=0)
    total_tool_calls: int = Field(default=0)
    metadata: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ExecutionStep(BaseModel):
    """执行步骤节点"""
    id: str = Field(..., description="步骤ID (session_id:step_num)")
    step_number: int = Field(..., description="步骤序号")
    type: StepType = Field(..., description="步骤类型")
    status: StepStatus = Field(default=StepStatus.RUNNING)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    token_count: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ToolCall(BaseModel):
    """工具调用节点"""
    id: str = Field(..., description="工具调用ID")
    name: str = Field(..., description="工具名称")
    arguments: str = Field(..., description="JSON 参数")
    output: Optional[str] = None
    output_preview: Optional[str] = None
    status: ToolStatus = Field(default=ToolStatus.RUNNING)
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Message(BaseModel):
    """消息节点"""
    id: str = Field(..., description="消息ID")
    role: str = Field(..., description="角色: system/user/assistant/tool")
    content: str = Field(..., description="消息内容")
    content_preview: Optional[str] = None
    tool_calls: Optional[str] = None  # JSON
    token_count: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    compression_ref: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Task(BaseModel):
    """任务节点"""
    id: str = Field(..., description="任务ID")
    task_id: int = Field(..., description="任务数字ID")
    subject: str = Field(..., description="主题")
    description: Optional[str] = None
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    owner: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Todo(BaseModel):
    """待办节点"""
    id: str = Field(..., description="待办ID")
    item_id: str = Field(..., description="事项ID")
    text: str = Field(..., description="内容")
    status: TodoStatus = Field(default=TodoStatus.PENDING)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Skill(BaseModel):
    """技能节点"""
    id: str = Field(..., description="技能ID")
    name: str = Field(..., description="技能名称")
    description: Optional[str] = None
    tags: Optional[str] = None
    body: Optional[str] = None
    file_path: Optional[str] = None


class Teammate(BaseModel):
    """团队成员节点"""
    id: str = Field(..., description="成员ID")
    name: str = Field(..., description="名称")
    role: str = Field(..., description="角色")
    status: TeammateStatus = Field(default=TeammateStatus.IDLE)
    prompt: Optional[str] = None
    thread_id: Optional[str] = None


class BackgroundJob(BaseModel):
    """后台任务节点"""
    id: str = Field(..., description="任务ID")
    task_id: str = Field(..., description="任务标识")
    command: str = Field(..., description="命令")
    status: BackgroundJobStatus = Field(default=BackgroundJobStatus.RUNNING)
    result: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SubagentRun(BaseModel):
    """子代理运行节点"""
    id: str = Field(..., description="运行ID")
    prompt: str = Field(..., description="提示词")
    agent_type: str = Field(default="Explore")
    max_rounds: int = Field(default=30)
    actual_rounds: int = Field(default=0)
    status: str = Field(default="running")
    summary: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Artifact(BaseModel):
    """产物节点"""
    id: str = Field(..., description="产物ID")
    type: str = Field(..., description="类型: file/data/output")
    name: str = Field(..., description="名称")
    file_path: Optional[str] = None
    content_preview: Optional[str] = None
    size_bytes: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Compression(BaseModel):
    """压缩记录节点"""
    id: str = Field(..., description="压缩ID")
    type: CompressionType = Field(..., description="压缩类型")
    transcript_path: Optional[str] = None
    summary: Optional[str] = None
    original_tokens: Optional[int] = None
    compressed_tokens: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GraphNode(BaseModel):
    """通用图谱节点"""
    id: str
    label: str
    properties: Dict[str, Any]


class GraphEdge(BaseModel):
    """通用图谱边"""
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any]


class ExecutionGraph(BaseModel):
    """执行图谱"""
    session: AgentSession
    steps: List[ExecutionStep]
    tool_calls: List[ToolCall]
    messages: List[Message]
    tasks: List[Task]
    todos: List[Todo]
    edges: List[GraphEdge]
