"""
LLM Client Configuration

提供统一的 LLM 客户端配置
"""

import os
from pathlib import Path
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# 尝试从多个位置加载 .env 文件
env_paths = [
    Path.cwd() / ".env",  # 当前目录
    Path(__file__).parent.parent.parent.parent.parent / ".env",  # 项目根目录
    Path(__file__).parent.parent.parent / ".env",  # backend 目录
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break

# 从环境变量读取配置
API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY", "")
BASE_URL = os.getenv("ANTHROPIC_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("MODEL_ID") or os.getenv("DEEPSEEK_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4")

# 创建共享客户端
_client: Optional[OpenAI] = None


def _create_client() -> OpenAI:
    """创建并返回 LLM 客户端实例"""
    global _client
    if _client is None:
        if not API_KEY:
            raise ValueError("API key not set. Please set ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, or OPENAI_API_KEY environment variable.")
        _client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL
        )
    return _client


def get_client() -> OpenAI:
    """获取 LLM 客户端实例"""
    return _create_client()


def get_model() -> str:
    """获取当前配置的模型名称"""
    return MODEL
