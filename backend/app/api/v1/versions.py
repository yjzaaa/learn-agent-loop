"""
版本管理 API 路由

提供 Agent 版本的查询和对比功能
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path

from app.core.logger import get_logger, info, warning
from app.models.schemas import (
    AgentVersion, VersionListResponse, VersionDetailResponse,
    VersionCompareResponse, ResponseStatus
)
from app.services.data_service import data_service

router = APIRouter(prefix="/versions", tags=["版本管理"])
logger = get_logger(__name__)


@router.get(
    "",
    response_model=VersionListResponse,
    summary="获取版本列表",
    description="获取所有 Agent 版本的列表，支持按层级筛选"
)
async def list_versions(
    layer: Optional[str] = Query(None, description="按层级筛选"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取版本列表
    
    - **layer**: 可选，按层级筛选 (L1-Coordination, L2-Orchestration, L3-Execution)
    - **limit**: 返回数量限制，默认 100
    - **offset**: 偏移量，用于分页
    """
    info("Listing versions", extra={"layer": layer, "limit": limit, "offset": offset})
    
    versions = data_service.get_versions()
    
    # 按层级筛选
    if layer:
        versions = [v for v in versions if v.layer.value == layer]
    
    total = len(versions)
    
    # 分页
    versions = versions[offset:offset + limit]
    
    return VersionListResponse(
        versions=versions,
        total=total,
        message=f"Found {total} versions"
    )


@router.get(
    "/timeline",
    response_model=VersionListResponse,
    summary="获取版本时间线",
    description="按时间顺序获取所有版本，用于时间线展示"
)
async def get_timeline():
    """获取版本时间线"""
    info("Getting version timeline")
    
    versions = data_service.get_versions()
    
    return VersionListResponse(
        versions=versions,
        total=len(versions),
        message="Timeline retrieved successfully"
    )


@router.get(
    "/{version_id}",
    response_model=VersionDetailResponse,
    summary="获取版本详情",
    description="根据版本 ID 获取详细信息"
)
async def get_version(
    version_id: str = Path(..., description="版本 ID，如 s01, s02", pattern=r"^s\d{2}$")
):
    """
    获取版本详情
    
    - **version_id**: 版本 ID，格式为 s01, s02, ..., s12
    """
    info("Getting version details", extra={"version_id": version_id})
    
    version = data_service.get_version_by_id(version_id)
    
    if not version:
        warning(f"Version not found: {version_id}")
        raise HTTPException(status_code=404, detail=f"Version {version_id} not found")
    
    return VersionDetailResponse(
        data=version,
        message=f"Version {version_id} retrieved successfully"
    )


@router.get(
    "/{version_id}/source",
    response_model=dict,
    summary="获取版本源代码",
    description="获取指定版本的完整源代码"
)
async def get_version_source(
    version_id: str = Path(..., description="版本 ID")
):
    """获取版本源代码"""
    info("Getting version source code", extra={"version_id": version_id})
    
    version = data_service.get_version_by_id(version_id)
    
    if not version:
        raise HTTPException(status_code=404, detail=f"Version {version_id} not found")
    
    return {
        "status": ResponseStatus.SUCCESS,
        "data": {
            "version_id": version_id,
            "filename": version.filename,
            "source": version.source,
            "loc": version.loc,
        },
        "message": "Source code retrieved successfully"
    }


@router.get(
    "/{version_id}/diff",
    response_model=VersionCompareResponse,
    summary="对比版本",
    description="对比当前版本与上一版本的差异"
)
async def get_version_diff(
    version_id: str = Path(..., description="目标版本 ID")
):
    """
    获取版本与上一版本的对比
    
    - **version_id**: 目标版本 ID
    """
    info("Getting version diff", extra={"version_id": version_id})
    
    version = data_service.get_version_by_id(version_id)
    
    if not version:
        raise HTTPException(status_code=404, detail=f"Version {version_id} not found")
    
    if not version.prev_version:
        return VersionCompareResponse(
            data=None,
            message=f"Version {version_id} is the first version, no previous version to compare"
        )
    
    diff = data_service.compare_versions(version.prev_version, version_id)
    
    if not diff:
        raise HTTPException(status_code=500, detail="Failed to generate diff")
    
    return VersionCompareResponse(
        data=diff,
        message=f"Diff between {version.prev_version} and {version_id}"
    )


@router.post(
    "/compare",
    response_model=VersionCompareResponse,
    summary="对比任意两个版本",
    description="对比任意两个指定版本的差异"
)
async def compare_two_versions(
    from_version: str = Query(..., description="源版本 ID"),
    to_version: str = Query(..., description="目标版本 ID")
):
    """
    对比两个版本
    
    - **from_version**: 源版本 ID
    - **to_version**: 目标版本 ID
    """
    info("Comparing versions", extra={"from": from_version, "to": to_version})
    
    # 验证版本存在
    from_v = data_service.get_version_by_id(from_version)
    to_v = data_service.get_version_by_id(to_version)
    
    if not from_v:
        raise HTTPException(status_code=404, detail=f"Version {from_version} not found")
    if not to_v:
        raise HTTPException(status_code=404, detail=f"Version {to_version} not found")
    
    diff = data_service.compare_versions(from_version, to_version)
    
    return VersionCompareResponse(
        data=diff,
        message=f"Comparison between {from_version} and {to_version}"
    )


@router.get(
    "/{version_id}/related",
    response_model=dict,
    summary="获取相关版本",
    description="获取当前版本的前后版本信息"
)
async def get_related_versions(
    version_id: str = Path(..., description="版本 ID")
):
    """获取相关版本（前序和后续）"""
    info("Getting related versions", extra={"version_id": version_id})
    
    version = data_service.get_version_by_id(version_id)
    
    if not version:
        raise HTTPException(status_code=404, detail=f"Version {version_id} not found")
    
    prev_version = None
    next_version = None
    
    if version.prev_version:
        prev_version = data_service.get_version_by_id(version.prev_version)
    if version.next_version:
        next_version = data_service.get_version_by_id(version.next_version)
    
    return {
        "status": ResponseStatus.SUCCESS,
        "data": {
            "current": version,
            "previous": prev_version,
            "next": next_version,
        },
        "message": "Related versions retrieved successfully"
    }
