#!/usr/bin/env python3
"""
agents/client.py - 共享的 DeepSeek 客户端

为所有 agent 提供统一的 DeepSeek API 客户端配置。
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# 模型选择
# - deepseek-chat: V3系列，支持工具调用，推荐日常使用
# - deepseek-reasoner: R1系列，推理能力强，thinking模式下不支持工具调用
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 创建共享客户端
if DEEPSEEK_API_KEY:
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL
    )
else:
    client = None


def get_client() -> OpenAI:
    """获取 DeepSeek 客户端实例"""
    if client is None:
        raise ValueError("DEEPSEEK_API_KEY not set. Please set the environment variable.")
    return client


def get_model() -> str:
    """获取当前配置的模型名称"""
    return MODEL
