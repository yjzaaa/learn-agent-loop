"""
API 路由模块
"""

from fastapi import APIRouter
from app.api.v1 import router as v1_router

# 主路由
router = APIRouter()

# 注册 v1 路由
router.include_router(v1_router)
