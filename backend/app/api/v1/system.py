"""
系统 API 路由

提供健康检查、系统信息等功能
"""

import time
from datetime import datetime
from fastapi import APIRouter

from app.core.config import settings
from app.core.logger import get_logger, info
from app.models.schemas import HealthResponse, HealthStatus, ResponseStatus

router = APIRouter(prefix="/system", tags=["系统"])
logger = get_logger(__name__)

# 启动时间
START_TIME = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查 API 服务健康状态"
)
async def health_check():
    """健康检查端点"""
    uptime = time.time() - START_TIME
    
    health_data = HealthStatus(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        uptime=round(uptime, 2),
        environment=settings.ENVIRONMENT,
    )
    
    return HealthResponse(
        data=health_data,
        message="Service is healthy"
    )


@router.get(
    "/info",
    response_model=dict,
    summary="系统信息",
    description="获取 API 系统信息"
)
async def system_info():
    """获取系统信息"""
    info("Getting system info")
    
    return {
        "status": ResponseStatus.SUCCESS,
        "data": {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
        },
        "message": "System info retrieved successfully"
    }


@router.get(
    "/stats",
    response_model=dict,
    summary="统计数据",
    description="获取系统统计数据"
)
async def system_stats():
    """获取系统统计"""
    from app.services.data_service import data_service
    
    info("Getting system stats")
    
    versions = data_service.get_versions()
    scenarios = data_service.get_scenarios()
    docs = data_service.get_docs()
    
    # 按层级统计
    layer_stats = {}
    for v in versions:
        layer = v.layer.value
        layer_stats[layer] = layer_stats.get(layer, 0) + 1
    
    return {
        "status": ResponseStatus.SUCCESS,
        "data": {
            "versions": {
                "total": len(versions),
                "by_layer": layer_stats,
            },
            "scenarios": {
                "total": len(scenarios),
            },
            "docs": {
                "total": len(docs),
            },
            "uptime_seconds": round(time.time() - START_TIME, 2),
        },
        "message": "System stats retrieved successfully"
    }


@router.get(
    "/logs",
    response_model=dict,
    summary="日志级别",
    description="获取和设置日志级别（开发调试用）"
)
async def get_log_level():
    """获取当前日志级别"""
    return {
        "status": ResponseStatus.SUCCESS,
        "data": {
            "level": settings.LOG_LEVEL,
            "json_logs": settings.LOG_JSON,
        },
        "message": "Log level retrieved"
    }
