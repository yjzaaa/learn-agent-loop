"""
可视化 API 路由

提供可视化数据的查询功能
"""

from fastapi import APIRouter, HTTPException, Path

from app.core.logger import get_logger, info, warning
from app.models.schemas import VisualizationResponse
from app.services.data_service import data_service

router = APIRouter(prefix="/visualizations", tags=["可视化"])
logger = get_logger(__name__)


@router.get(
    "/{version_id}",
    response_model=VisualizationResponse,
    summary="获取可视化数据",
    description="根据版本 ID 获取对应的可视化数据"
)
async def get_visualization(
    version_id: str = Path(..., description="版本 ID", pattern=r"^s\d{2}$")
):
    """
    获取可视化数据
    
    - **version_id**: 版本 ID，如 s01, s02
    """
    info("Getting visualization", extra={"version_id": version_id})
    
    viz_data = data_service.get_visualization(version_id)
    
    if not viz_data:
        warning(f"Visualization not found: {version_id}")
        raise HTTPException(
            status_code=404, 
            detail=f"No visualization found for version {version_id}"
        )
    
    return VisualizationResponse(
        data=viz_data,
        message=f"Visualization for {version_id} retrieved successfully"
    )


@router.get(
    "/{version_id}/state/{step}",
    response_model=dict,
    summary="获取指定状态",
    description="获取可视化在指定步骤的状态"
)
async def get_visualization_state(
    version_id: str = Path(..., description="版本 ID"),
    step: int = Path(..., description="步骤序号", ge=0)
):
    """获取指定步骤的可视化状态"""
    info("Getting visualization state", extra={"version_id": version_id, "step": step})
    
    viz_data = data_service.get_visualization(version_id)
    
    if not viz_data:
        raise HTTPException(
            status_code=404, 
            detail=f"No visualization found for version {version_id}"
        )
    
    if step >= len(viz_data.states):
        raise HTTPException(
            status_code=404, 
            detail=f"Step {step} not found in visualization {version_id}"
        )
    
    state = viz_data.states[step]
    
    return {
        "status": "success",
        "data": {
            "step": step,
            "state": state,
            "total_steps": len(viz_data.states),
        },
        "message": f"State at step {step} retrieved successfully"
    }


@router.get(
    "/{version_id}/nodes",
    response_model=dict,
    summary="获取节点列表",
    description="获取可视化的所有节点"
)
async def get_visualization_nodes(
    version_id: str = Path(..., description="版本 ID")
):
    """获取可视化节点列表"""
    info("Getting visualization nodes", extra={"version_id": version_id})
    
    viz_data = data_service.get_visualization(version_id)
    
    if not viz_data:
        raise HTTPException(
            status_code=404, 
            detail=f"No visualization found for version {version_id}"
        )
    
    return {
        "status": "success",
        "data": viz_data.nodes,
        "total": len(viz_data.nodes),
        "message": f"Nodes for {version_id} retrieved successfully"
    }


@router.get(
    "/{version_id}/edges",
    response_model=dict,
    summary="获取边列表",
    description="获取可视化的所有边"
)
async def get_visualization_edges(
    version_id: str = Path(..., description="版本 ID")
):
    """获取可视化边列表"""
    info("Getting visualization edges", extra={"version_id": version_id})
    
    viz_data = data_service.get_visualization(version_id)
    
    if not viz_data:
        raise HTTPException(
            status_code=404, 
            detail=f"No visualization found for version {version_id}"
        )
    
    return {
        "status": "success",
        "data": viz_data.edges,
        "total": len(viz_data.edges),
        "message": f"Edges for {version_id} retrieved successfully"
    }
