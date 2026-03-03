"""
Loguru 日志配置模块

提供结构化日志记录，支持：
- 控制台彩色输出（开发环境）
- JSON 格式文件日志（生产环境）
- 自动日志轮转和压缩
- 请求上下文绑定
"""

import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger
from datetime import datetime

# 日志目录
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


class JSONFormatter:
    """JSON 格式日志处理器"""
    
    def __call__(self, record: Dict[str, Any]) -> str:
        log_data = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
            "thread": record["thread"],
            "process": record["process"],
        }
        
        # 添加 extra 字段
        if record["extra"]:
            log_data.update(record["extra"])
        
        # 添加异常信息
        if record["exception"]:
            log_data["exception"] = record["exception"]
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logging(
    level: str = "INFO",
    json_logs: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """
    配置 Loguru 日志系统
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: 是否使用 JSON 格式（生产环境推荐）
        log_file: 日志文件路径，None 则使用默认路径
    """
    # 移除默认处理器
    logger.remove()
    
    # 控制台处理器
    if json_logs:
        # JSON 格式（生产环境）
        logger.add(
            sys.stdout,
            level=level,
            serialize=True,
            format="{message}",
        )
    else:
        # 彩色格式（开发环境）
        logger.add(
            sys.stdout,
            level=level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    
    # 文件处理器 - 应用日志
    app_log_file = log_file or LOG_DIR / "app.log"
    logger.add(
        app_log_file,
        level=level,
        rotation="500 MB",
        retention="30 days",
        compression="gz",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        enqueue=True,  # 异步写入，提高性能
    )
    
    # 文件处理器 - JSON 格式（用于日志收集系统）
    json_log_file = LOG_DIR / "app.json"
    logger.add(
        json_log_file,
        level=level,
        rotation="1 day",
        retention="30 days",
        compression="gz",
        encoding="utf-8",
        format="{message}",
        serialize=True,  # 输出 JSON
        enqueue=True,
    )
    
    # 错误日志单独存储
    error_log_file = LOG_DIR / "error.log"
    logger.add(
        error_log_file,
        level="ERROR",
        rotation="100 MB",
        retention="30 days",
        compression="gz",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        enqueue=True,
    )
    
    logger.info(
        "Logging system initialized",
        extra={
            "level": level,
            "json_logs": json_logs,
            "app_log": str(app_log_file),
            "error_log": str(error_log_file),
        }
    )


def get_logger(name: Optional[str] = None):
    """
    获取配置好的 logger 实例
    
    Args:
        name: 模块名称，用于上下文绑定
    
    Returns:
        配置好的 logger
    """
    if name:
        return logger.bind(module=name)
    return logger


class RequestContext:
    """请求上下文管理器，用于绑定请求相关的日志信息"""
    
    def __init__(
        self,
        request_id: str,
        client_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
    ):
        self.request_id = request_id
        self.client_ip = client_ip
        self.user_id = user_id
        self.path = path
        self.method = method
        self.start_time = datetime.utcnow()
        self._logger = None
    
    def bind(self) -> Any:
        """绑定上下文到 logger"""
        self._logger = logger.bind(
            request_id=self.request_id,
            client_ip=self.client_ip,
            user_id=self.user_id,
            path=self.path,
            method=self.method,
        )
        return self._logger
    
    def log_request_start(self) -> None:
        """记录请求开始"""
        if self._logger:
            self._logger.info(
                "Request started",
                extra={
                    "event": "request_start",
                    "request_id": self.request_id,
                    "client_ip": self.client_ip,
                    "path": self.path,
                    "method": self.method,
                }
            )
    
    def log_request_end(
        self,
        status_code: int,
        duration_ms: float,
        extra: Optional[Dict] = None
    ) -> None:
        """记录请求结束"""
        if self._logger:
            log_data = {
                "event": "request_end",
                "request_id": self.request_id,
                "status_code": status_code,
                "duration_ms": duration_ms,
            }
            if extra:
                log_data.update(extra)
            
            # 根据状态码选择日志级别
            if status_code >= 500:
                self._logger.error("Request failed", extra=log_data)
            elif status_code >= 400:
                self._logger.warning("Request warning", extra=log_data)
            else:
                self._logger.info("Request completed", extra=log_data)
    
    def __enter__(self):
        self.bind()
        self.log_request_start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            if self._logger:
                self._logger.exception("Request exception")
        return False


# 便捷函数
def debug(msg: str, **kwargs):
    """调试日志"""
    logger.debug(msg, **kwargs)


def info(msg: str, **kwargs):
    """信息日志"""
    logger.info(msg, **kwargs)


def warning(msg: str, **kwargs):
    """警告日志"""
    logger.warning(msg, **kwargs)


def error(msg: str, **kwargs):
    """错误日志"""
    logger.error(msg, **kwargs)


def critical(msg: str, **kwargs):
    """严重错误日志"""
    logger.critical(msg, **kwargs)


def exception(msg: str, **kwargs):
    """异常日志（自动捕获堆栈）"""
    logger.exception(msg, **kwargs)
