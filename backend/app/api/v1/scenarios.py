"""
场景 API 路由

提供学习场景的查询功能
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Query

from app.core.logger import get_logger, info, warning
from app.models.schemas import (
    Scenario, ScenarioListResponse, ScenarioDetailResponse
)
from app.services.data_service import data_service

router = APIRouter(prefix="/scenarios", tags=["学习场景"])
logger = get_logger(__name__)


@router.get(
    "",
    response_model=ScenarioListResponse,
    summary="获取场景列表",
    description="获取所有学习场景列表"
)
async def list_scenarios(
    version_id: Optional[str] = Query(None, description="按版本ID筛选")
):
    """
    获取场景列表
    
    - **version_id**: 可选，按版本 ID 筛选
    """
    info("Listing scenarios", extra={"version_id": version_id})
    
    scenarios = data_service.get_scenarios(version_id)
    
    return ScenarioListResponse(
        scenarios=scenarios,
        total=len(scenarios),
        message=f"Found {len(scenarios)} scenarios"
    )


@router.get(
    "/{scenario_id}",
    response_model=ScenarioDetailResponse,
    summary="获取场景详情",
    description="根据场景 ID 获取详细信息"
)
async def get_scenario(
    scenario_id: str = Path(..., description="场景 ID")
):
    """获取场景详情"""
    info("Getting scenario", extra={"scenario_id": scenario_id})
    
    # 从 ID 提取版本号
    version_id = scenario_id.replace("_scenario", "")
    scenario = data_service.get_scenario_by_version(version_id)
    
    if not scenario:
        warning(f"Scenario not found: {scenario_id}")
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    
    return ScenarioDetailResponse(
        data=scenario,
        message=f"Scenario {scenario_id} retrieved successfully"
    )


@router.get(
    "/by-version/{version_id}",
    response_model=ScenarioDetailResponse,
    summary="按版本获取场景",
    description="根据版本 ID 获取对应的学习场景"
)
async def get_scenario_by_version(
    version_id: str = Path(..., description="版本 ID", pattern=r"^s\d{2}$")
):
    """
    根据版本 ID 获取场景
    
    - **version_id**: 版本 ID，如 s01, s02
    """
    info("Getting scenario by version", extra={"version_id": version_id})
    
    scenario = data_service.get_scenario_by_version(version_id)
    
    if not scenario:
        raise HTTPException(
            status_code=404, 
            detail=f"No scenario found for version {version_id}"
        )
    
    return ScenarioDetailResponse(
        data=scenario,
        message=f"Scenario for {version_id} retrieved successfully"
    )


@router.get(
    "/{scenario_id}/steps/{step_number}",
    response_model=dict,
    summary="获取步骤详情",
    description="获取场景中指定步骤的详情"
)
async def get_step_detail(
    scenario_id: str = Path(..., description="场景 ID"),
    step_number: int = Path(..., description="步骤序号", ge=1)
):
    """获取步骤详情"""
    info("Getting step detail", extra={"scenario_id": scenario_id, "step": step_number})
    
    version_id = scenario_id.replace("_scenario", "")
    scenario = data_service.get_scenario_by_version(version_id)
    
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    
    if step_number > len(scenario.steps):
        raise HTTPException(
            status_code=404, 
            detail=f"Step {step_number} not found in scenario {scenario_id}"
        )
    
    step = scenario.steps[step_number - 1]
    
    return {
        "status": "success",
        "data": step,
        "message": f"Step {step_number} retrieved successfully"
    }
