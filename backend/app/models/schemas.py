"""
Pydantic 模型定义

定义 API 请求和响应的数据模型
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# ==================== 通用响应模型 ====================

class ResponseStatus(str, Enum):
    """响应状态枚举"""
    SUCCESS = "success"
    ERROR = "error"


class BaseResponse(BaseModel):
    """基础响应模型"""
    status: ResponseStatus = Field(default=ResponseStatus.SUCCESS, description="响应状态")
    message: str = Field(default="", description="响应消息")
    request_id: Optional[str] = Field(default=None, description="请求ID")


class PaginatedResponse(BaseResponse):
    """分页响应模型"""
    total: int = Field(default=0, description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页大小")
    pages: int = Field(default=1, description="总页数")
    has_next: bool = Field(default=False, description="是否有下一页")
    has_prev: bool = Field(default=False, description="是否有上一页")


# ==================== Agent 版本模型 ====================

class AgentLayer(str, Enum):
    """Agent 层级枚举"""
    L1_COORDINATION = "L1-Coordination"
    L2_ORCHESTRATION = "L2-Orchestration"
    L3_EXECUTION = "L3-Execution"


class ClassInfo(BaseModel):
    """类信息"""
    name: str = Field(..., description="类名")
    startLine: int = Field(..., description="起始行号")
    endLine: int = Field(..., description="结束行号")


class FunctionInfo(BaseModel):
    """函数信息"""
    name: str = Field(..., description="函数名")
    signature: str = Field(..., description="函数签名")
    startLine: int = Field(..., description="起始行号")


class AgentVersion(BaseModel):
    """Agent 版本模型"""
    id: str = Field(..., description="版本ID，如 s01, s02")
    title: str = Field(..., description="版本标题")
    subtitle: str = Field(..., description="版本副标题")
    description: str = Field(default="", description="版本描述")
    layer: str = Field(default="tools", description="所属层级")
    prev_version: Optional[str] = Field(default=None, description="上一版本ID")
    next_version: Optional[str] = Field(default=None, description="下一版本ID")
    
    # 代码统计
    loc: int = Field(default=0, description="代码行数")
    filename: str = Field(default="", description="代码文件名")
    source: str = Field(default="", description="源代码内容")
    
    # 组件
    tools: List[str] = Field(default_factory=list, description="使用的工具")
    classes: List[Union[str, ClassInfo]] = Field(default_factory=list, description="定义的类")
    functions: List[Union[str, FunctionInfo]] = Field(default_factory=list, description="定义的函数")
    
    # 额外字段（从前端 JSON 导入）
    newTools: List[str] = Field(default_factory=list, description="新增工具")
    coreAddition: str = Field(default="", description="核心新增功能")
    keyInsight: str = Field(default="", description="关键洞察")
    
    class Config:
        from_attributes = True


class VersionDiff(BaseModel):
    """版本差异模型"""
    from_version: str = Field(..., description="源版本ID")
    to_version: str = Field(..., description="目标版本ID")
    loc_delta: int = Field(..., description="代码行数变化")
    new_tools: List[str] = Field(default_factory=list, description="新增工具")
    new_classes: List[str] = Field(default_factory=list, description="新增类")
    new_functions: List[str] = Field(default_factory=list, description="新增函数")
    diff_content: Optional[str] = Field(default=None, description="差异内容")


class VersionListResponse(BaseResponse):
    """版本列表响应"""
    versions: List[AgentVersion] = Field(default_factory=list, description="版本列表")
    total: int = Field(default=0, description="总数量")


class VersionDetailResponse(BaseResponse):
    """版本详情响应"""
    data: Optional[AgentVersion] = Field(default=None, description="版本详情")


class VersionCompareResponse(BaseResponse):
    """版本对比响应"""
    data: Optional[VersionDiff] = Field(default=None, description="版本差异")


# ==================== 场景模型 ====================

class ScenarioStep(BaseModel):
    """场景步骤模型"""
    step: int = Field(..., description="步骤序号")
    title: str = Field(..., description="步骤标题")
    description: str = Field(..., description="步骤描述")
    code: Optional[str] = Field(default=None, description="代码示例")
    note: Optional[str] = Field(default=None, description="备注")


class Scenario(BaseModel):
    """场景模型"""
    id: str = Field(..., description="场景ID")
    version_id: str = Field(..., description="所属版本ID")
    title: str = Field(..., description="场景标题")
    description: str = Field(..., description="场景描述")
    steps: List[ScenarioStep] = Field(default_factory=list, description="步骤列表")
    
    class Config:
        from_attributes = True


class ScenarioListResponse(BaseResponse):
    """场景列表响应"""
    scenarios: List[Scenario] = Field(default_factory=list, description="场景列表")
    total: int = Field(default=0, description="总数量")


class ScenarioDetailResponse(BaseResponse):
    """场景详情响应"""
    data: Optional[Scenario] = Field(default=None, description="场景详情")


# ==================== 可视化模型 ====================

class VisualizationNode(BaseModel):
    """可视化节点模型"""
    id: str = Field(..., description="节点ID")
    type: str = Field(..., description="节点类型")
    label: str = Field(..., description="节点标签")
    x: float = Field(..., description="X坐标")
    y: float = Field(..., description="Y坐标")
    data: Optional[Dict[str, Any]] = Field(default=None, description="节点数据")


class VisualizationEdge(BaseModel):
    """可视化边模型"""
    id: str = Field(..., description="边ID")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    label: Optional[str] = Field(default=None, description="边标签")
    animated: bool = Field(default=False, description="是否动画")


class VisualizationState(BaseModel):
    """可视化状态模型"""
    step: int = Field(..., description="步骤序号")
    title: str = Field(..., description="状态标题")
    description: str = Field(..., description="状态描述")
    active_nodes: List[str] = Field(default_factory=list, description="激活的节点")
    highlighted_edges: List[str] = Field(default_factory=list, description="高亮的边")


class VisualizationData(BaseModel):
    """可视化数据模型"""
    id: str = Field(..., description="可视化ID")
    version_id: str = Field(..., description="所属版本ID")
    title: str = Field(..., description="可视化标题")
    description: str = Field(..., description="可视化描述")
    nodes: List[VisualizationNode] = Field(default_factory=list, description="节点列表")
    edges: List[VisualizationEdge] = Field(default_factory=list, description="边列表")
    states: List[VisualizationState] = Field(default_factory=list, description="状态列表")
    
    class Config:
        from_attributes = True


class VisualizationResponse(BaseResponse):
    """可视化数据响应"""
    data: Optional[VisualizationData] = Field(default=None, description="可视化数据")


# ==================== 执行流程模型 ====================

class ExecutionFlowStep(BaseModel):
    """执行流程步骤模型"""
    step: int = Field(..., description="步骤序号")
    title: str = Field(..., description="步骤标题")
    description: str = Field(..., description="步骤描述")
    actor: str = Field(..., description="执行者")
    action: str = Field(..., description="动作")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细信息")


class ExecutionFlow(BaseModel):
    """执行流程模型"""
    id: str = Field(..., description="流程ID")
    version_id: str = Field(..., description="所属版本ID")
    title: str = Field(..., description="流程标题")
    description: str = Field(..., description="流程描述")
    steps: List[ExecutionFlowStep] = Field(default_factory=list, description="步骤列表")
    
    class Config:
        from_attributes = True


class ExecutionFlowResponse(BaseResponse):
    """执行流程响应"""
    data: Optional[ExecutionFlow] = Field(default=None, description="执行流程数据")


# ==================== 文档模型 ====================

class DocItem(BaseModel):
    """文档条目模型"""
    id: str = Field(..., description="文档ID")
    version_id: str = Field(..., description="所属版本ID")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    category: str = Field(default="general", description="文档分类")
    order: int = Field(default=0, description="排序顺序")
    
    class Config:
        from_attributes = True


class DocListResponse(BaseResponse):
    """文档列表响应"""
    docs: List[DocItem] = Field(default_factory=list, description="文档列表")
    total: int = Field(default=0, description="总数量")


class DocDetailResponse(BaseResponse):
    """文档详情响应"""
    data: Optional[DocItem] = Field(default=None, description="文档详情")


# ==================== 健康检查模型 ====================

class HealthStatus(BaseModel):
    """健康状态模型"""
    status: str = Field(..., description="状态")
    version: str = Field(..., description="版本")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")
    uptime: float = Field(default=0.0, description="运行时间（秒）")
    environment: str = Field(..., description="环境")


class HealthResponse(BaseResponse):
    """健康检查响应"""
    data: HealthStatus = Field(..., description="健康状态数据")


# ==================== 错误模型 ====================

class ErrorDetail(BaseModel):
    """错误详情模型"""
    field: Optional[str] = Field(default=None, description="错误字段")
    message: str = Field(..., description="错误消息")
    code: Optional[str] = Field(default=None, description="错误代码")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    status: ResponseStatus = ResponseStatus.ERROR
    errors: List[ErrorDetail] = Field(default_factory=list, description="错误列表")
    traceback: Optional[str] = Field(default=None, description="堆栈跟踪（仅调试模式）")
