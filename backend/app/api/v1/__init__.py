"""
API v1 路由聚合

聚合所有 v1 版本的 API 路由
"""

from fastapi import APIRouter

from app.api.v1 import versions, scenarios, visualizations, docs, system

# 创建 v1 路由
router = APIRouter(prefix="/v1")

# 注册子路由
router.include_router(versions.router)
router.include_router(scenarios.router)
router.include_router(visualizations.router)
router.include_router(docs.router)
router.include_router(system.router)
