# agents/ - Python 教学代理 (s01-s12) + 参考代理 (s_full)
# 每个文件都是自包含且可运行的: python agents/s01_agent_loop.py
#
# 使用 DeepSeek API (OpenAI 格式)
# 设置环境变量:
#   $env:DEEPSEEK_API_KEY = "sk-xxx"
#   $env:DEEPSEEK_MODEL = "deepseek-chat"  # 或 "deepseek-reasoner"

from .client import get_client, get_model, client, MODEL

__all__ = ["get_client", "get_model", "client", "MODEL"]
