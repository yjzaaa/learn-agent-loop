#!/usr/bin/env python3
"""
客户端配置管理

提供统一的 LLM 客户端配置和访问。
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# 模型选择
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 创建共享客户端
_client = None


def _create_client() -> OpenAI:
    """创建并返回 DeepSeek 客户端实例"""
    global _client
    if _client is None:
        if not DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY not set. Please set the environment variable.")
        _client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
    return _client


def get_client() -> OpenAI:
    """获取 DeepSeek 客户端实例"""
    return _create_client()


def get_model() -> str:
    """获取当前配置的模型名称"""
    return MODEL
