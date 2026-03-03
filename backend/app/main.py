"""
FastAPI 主应用入口

Learn Claude Code API 后端服务
使用 Loguru 进行结构化日志记录
"""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logger import (
    setup_logging, get_logger, RequestContext,
    info, error, exception
)
from app.api import router as api_router
from app.agentcore.api import router as agentcore_router

# 初始化日志
setup_logging(
    level=settings.LOG_LEVEL,
    json_logs=settings.LOG_JSON,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    - 启动时：初始化资源、连接数据库等
    - 关闭时：清理资源、关闭连接等
    """
    # 启动
    info(
        "Application starting",
        extra={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
        }
    )
    
    yield
    
    # 关闭
    info("Application shutting down")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Learn Claude Code 后端 API 服务",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


# 请求日志中间件
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    请求日志中间件
    
    记录每个请求的处理时间、状态码等信息
    """
    # 生成请求 ID
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    # 记录开始时间
    start_time = time.time()
    
    # 创建请求上下文
    client_ip = request.client.host if request.client else None
    path = request.url.path
    method = request.method
    
    ctx = RequestContext(
        request_id=request_id,
        client_ip=client_ip,
        path=path,
        method=method,
    )
    
    # 绑定上下文并记录请求开始
    ctx.bind()
    ctx.log_request_start()
    
    try:
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        duration = (time.time() - start_time) * 1000
        
        # 添加请求 ID 到响应头
        response.headers["X-Request-ID"] = request_id
        
        # 记录请求完成
        ctx.log_request_end(
            status_code=response.status_code,
            duration_ms=round(duration, 2)
        )
        
        return response
        
    except Exception as e:
        # 计算处理时间
        duration = (time.time() - start_time) * 1000
        
        # 记录异常
        exception("Request failed with exception")
        
        # 返回错误响应
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Internal server error",
                "request_id": request_id,
            }
        )


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    exception("Unhandled exception", extra={"request_id": request_id})
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Internal server error",
            "request_id": request_id,
        }
    )


# 注册 API 路由
app.include_router(api_router, prefix="/api")
app.include_router(agentcore_router, prefix="/api/v1")


# 根路由
@app.get("/")
async def root():
    """根路径 - 返回 API 信息"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Learn Claude Code 后端 API 服务",
        "docs": "/docs" if settings.DEBUG else None,
        "health": "/api/v1/system/health",
    }


# 启动入口
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None,  # 禁用 uvicorn 默认日志，使用 loguru
    )
