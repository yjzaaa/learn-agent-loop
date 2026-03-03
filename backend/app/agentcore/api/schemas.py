"""
API Schemas

Pydantic models for API requests and responses
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    name: str = Field(..., description="会话名称")
    workdir: str = Field(default="./workspace", description="工作目录")
    model: Optional[str] = Field(default=None, description="模型名称")


class CreateSessionResponse(BaseModel):
    """创建会话响应"""
    session_id: str
    name: str
    workdir: str
    created_at: datetime


class RunAgentRequest(BaseModel):
    """运行 Agent 请求"""
    query: str = Field(..., description="用户查询")
    workdir: Optional[str] = Field(default=None, description="可选的工作目录覆盖")


class RunAgentResponse(BaseModel):
    """运行 Agent 响应"""
    session_id: str
    status: str
    steps: int
    message: str


class SessionResponse(BaseModel):
    """会话详情响应"""
    id: str
    name: str
    workdir: str
    model: str
    status: str
    started_at: str
    ended_at: Optional[str]
    total_steps: int
    total_tool_calls: int


class TimelineItem(BaseModel):
    """时间线项目"""
    step_number: int
    type: str
    status: str
    started_at: str
    duration_ms: Optional[int]
    token_count: Optional[int]
    finish_reason: Optional[str]
    tool_count: int


class SessionTimelineResponse(BaseModel):
    """会话时间线响应"""
    session_id: str
    timeline: List[TimelineItem]


class ToolStatItem(BaseModel):
    """工具统计项目"""
    tool_name: str
    call_count: int
    avg_duration: float
    error_count: int


class ToolStatsResponse(BaseModel):
    """工具统计响应"""
    session_id: str
    stats: List[ToolStatItem]


class GraphNode(BaseModel):
    """图谱节点"""
    id: str
    label: str
    properties: Dict[str, Any]


class GraphEdge(BaseModel):
    """图谱边"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any]


class ExecutionGraphResponse(BaseModel):
    """执行图谱响应"""
    session_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
