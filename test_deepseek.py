#!/usr/bin/env python3
"""
DeepSeek API 测试 - 验证 API 连接

使用方法:
    1. 设置环境变量 DEEPSEEK_API_KEY
    2. python test_deepseek.py

获取 API Key: https://platform.deepseek.com
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

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-938dfb4cb1e741ed960e2882da9d2eea")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

WORKDIR = Path.cwd()


def main():
    """主函数"""
    
    print("=" * 60)
    print("DeepSeek API 连接测试")
    print("=" * 60)
    
    # 检查 API 密钥
    if not DEEPSEEK_API_KEY:
        print("\n[错误] 请设置 DEEPSEEK_API_KEY 环境变量")
        print("示例: $env:DEEPSEEK_API_KEY='your-api-key'")
        print("\n获取 API Key: https://platform.deepseek.com")
        sys.exit(1)
    
    print("\n[配置信息]")
    print(f"   模型: {DEEPSEEK_MODEL}")
    print(f"   API 地址: {DEEPSEEK_BASE_URL}")
    print(f"   工作目录: {WORKDIR}")
    
    # 创建 OpenAI 客户端
    print("\n[连接] 正在连接 DeepSeek API...")
    try:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
    except Exception as e:
        print(f"[错误] 创建客户端失败: {e}")
        sys.exit(1)
    
    # 测试简单对话
    print("\n[测试] 发送测试消息...")
    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个简洁的助手。"},
                {"role": "user", "content": "你好！请用一句话介绍自己。"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        usage = response.usage
        
        print(f"\n[成功] 连接成功!")
        print(f"\n[DeepSeek 回复]")
        print(f"   {content}")
        print(f"\n[Token 使用]")
        print(f"   输入: {usage.prompt_tokens}")
        print(f"   输出: {usage.completion_tokens}")
        print(f"   总计: {usage.total_tokens}")
        
    except Exception as e:
        print(f"\n[错误] API 调用失败: {e}")
        if "401" in str(e):
            print("\n提示: API Key 无效，请检查:")
            print("  1. Key 是否正确复制（无多余空格）")
            print("  2. 账户是否有足够余额")
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
            model=DEEPSEEK_MODEL,
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
            print(f"\n[提示] 模型未调用工具，直接回复: {message.content[:50]}...")
            
    except Exception as e:
        print(f"\n[错误] 工具调用测试失败: {e}")
    
    # 测试流式输出
    print("\n[测试] 测试流式输出...")
    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "user", "content": "用3个词形容编程"}
            ],
            max_tokens=50,
            temperature=0.7,
            stream=True
        )
        
        print("   ", end="", flush=True)
        for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print(" [流式完成]")
        
    except Exception as e:
        print(f"\n[错误] 流式输出测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("[完成] 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
