#!/usr/bin/env python3
"""
Kimi Code 简单测试 - 非交互式，验证 API 连接

使用方法:
    1. 设置环境变量 KIMI_API_KEY
    2. python test_kimi_simple.py

注意:
    - 普通 Kimi API Key: 使用 https://api.moonshot.cn/v1
    - Kimi For Coding Key: 只能在 Kimi CLI 等官方工具中使用
"""

import os
import sys
from pathlib import Path

# 尝试导入 openai 库
try:
    from openai import OpenAI
except ImportError:
    print("[错误] 需要安装 openai 库")
    print("运行: pip install openai")
    sys.exit(1)


# =============================================================================
# 配置
# =============================================================================

KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
DEEPSEEK_API_KEY="sk-938dfb4cb1e741ed960e2882da9d2eea"
# 默认使用标准 Kimi API 端点
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
KIMI_MODEL = os.getenv("KIMI_MODEL", "moonshot-v1-8k")
WORKDIR = Path.cwd()


def main():
    """主函数"""
    global KIMI_BASE_URL
    
    print("=" * 60)
    print("Kimi Code 连接测试")
    print("=" * 60)
    
    # 检查 API 密钥
    if not KIMI_API_KEY:
        print("\n[错误] 请设置 KIMI_API_KEY 环境变量")
        print("示例: $env:KIMI_API_KEY='your-api-key'")
        print("\n获取 API Key: https://platform.moonshot.cn")
        sys.exit(1)
    
    # 检测是否为 Kimi For Coding Key
    is_coding_key = "kimi" in KIMI_API_KEY.lower() and KIMI_API_KEY.startswith("sk-kimi-")
    
    if is_coding_key and "kimi.com/coding" in KIMI_BASE_URL:
        print("\n[警告] 检测到 Kimi For Coding API Key!")
        print("       此 Key 只能在 Kimi CLI、Claude Code、Roo Code 等官方工具中使用。")
        print("       请使用普通 Kimi API Key，或安装 Kimi CLI 工具。")
        print("\n       尝试切换到标准 API 端点...")
        KIMI_BASE_URL = "https://api.moonshot.cn/v1"
    
    print("\n[配置信息]")
    print(f"   模型: {KIMI_MODEL}")
    print(f"   API 地址: {KIMI_BASE_URL}")
    print(f"   工作目录: {WORKDIR}")
    
    # 创建 OpenAI 客户端
    print("\n[连接] 正在连接 Kimi API...")
    try:
        client = OpenAI(
            api_key=KIMI_API_KEY,
            base_url=KIMI_BASE_URL
        )
    except Exception as e:
        print(f"[错误] 创建客户端失败: {e}")
        sys.exit(1)
    
    # 测试简单对话
    print("\n[测试] 发送测试消息...")
    try:
        response = client.chat.completions.create(
            model=KIMI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个简洁的助手。"},
                {"role": "user", "content": "你好！请用一句话介绍自己。"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        print(f"\n[成功] 连接成功!")
        print(f"\n[Kimi 回复]")
        print(f"   {content}")
        
    except Exception as e:
        print(f"\n[错误] API 调用失败: {e}")
        if "401" in str(e):
            print("\n提示: API Key 无效，请检查:")
            print("  1. Key 是否正确复制（无多余空格）")
            print("  2. 是否为普通 Kimi API Key（非 Coding Key）")
            print("  3. 账户是否有足够余额")
        sys.exit(1)
    
    # 测试工具调用
    print("\n[测试] 测试工具调用...")
    try:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "获取当前时间",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]
        
        response = client.chat.completions.create(
            model=KIMI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个可以使用工具的助手。"},
                {"role": "user", "content": "现在几点了？"}
            ],
            tools=tools,
            tool_choice="auto",
            max_tokens=100
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            print(f"\n[成功] 工具调用功能正常!")
            print(f"   工具: {message.tool_calls[0].function.name}")
        else:
            print(f"\n[提示] 模型未调用工具，回复: {message.content[:50]}...")
            
    except Exception as e:
        print(f"\n[错误] 工具调用测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("[完成] 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
