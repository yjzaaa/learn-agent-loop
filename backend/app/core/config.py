"""
应用配置模块

使用 Pydantic Settings 管理配置，支持环境变量和 .env 文件
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # 应用基础配置
    APP_NAME: str = Field(default="Learn Claude Code API", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    DEBUG: bool = Field(default=False, description="调试模式")
    ENVIRONMENT: str = Field(default="development", description="运行环境")
    
    # 服务器配置
    HOST: str = Field(default="0.0.0.0", description="监听地址")
    PORT: int = Field(default=8000, description="监听端口")
    
    # CORS 配置
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="允许的跨域来源"
    )
    CORS_CREDENTIALS: bool = Field(default=True, description="允许跨域携带凭证")
    CORS_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="允许的 HTTP 方法"
    )
    CORS_HEADERS: List[str] = Field(
        default=["*"],
        description="允许的 HTTP 头部"
    )
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_JSON: bool = Field(default=False, description="是否使用 JSON 格式日志")
    
    # 数据配置
    DATA_DIR: str = Field(default="../web/src/data", description="前端数据目录路径")
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="是否启用限流")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="每分钟最大请求数")
    
    # 缓存配置
    CACHE_ENABLED: bool = Field(default=True, description="是否启用缓存")
    CACHE_TTL: int = Field(default=300, description="缓存过期时间（秒）")
    
    @property
    def is_development(self) -> bool:
        """是否开发环境"""
        return self.ENVIRONMENT.lower() in ("development", "dev")
    
    @property
    def is_production(self) -> bool:
        """是否生产环境"""
        return self.ENVIRONMENT.lower() in ("production", "prod")
    
    @property
    def is_testing(self) -> bool:
        """是否测试环境"""
        return self.ENVIRONMENT.lower() in ("testing", "test")


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置实例（单例模式）
    
    Returns:
        Settings 配置实例
    """
    return Settings()


# 导出配置实例
settings = get_settings()
