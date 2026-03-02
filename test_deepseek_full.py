#!/usr/bin/env python3
"""
DeepSeek API 完整测试 - 测试所有可用模型和功能

支持的模型:
    - deepseek-chat (V3系列，推荐日常使用)
    - deepseek-reasoner (R1系列，推理任务)

使用方法:
    $env:DEEPSEEK_API_KEY = "sk-xxx"
    python test_deepseek_full.py

获取 API Key: https://platform.deepseek.com
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    print("[错误] 需要安装 openai 库: pip install openai")
    sys.exit(1)

# =============================================================================
# 配置
# =============================================================================

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

if not API_KEY:
    print("[错误] 请设置 DEEPSEEK_API_KEY 环境变量")
    print("示例: $env:DEEPSEEK_API_KEY='sk-xxx'")
    sys.exit(1)

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# =============================================================================
# 测试工具定义
# =============================================================================

TOOLS = [
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
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '2 + 2' 或 'sqrt(16)'"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

# =============================================================================
# 测试函数
# =============================================================================

def test_basic_chat(model="deepseek-chat"):
    """测试基础对话"""
    print(f"\n{'='*60}")
    print(f"[测试] 基础对话 - {model}")
    print('='*60)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个简洁的助手。"},
                {"role": "user", "content": "你好！请用一句话介绍自己。"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        usage = response.usage
        
        print(f"[OK] 成功!")
        print(f"\n回复:\n{content}")
        print(f"\nToken 使用: 输入={usage.prompt_tokens}, 输出={usage.completion_tokens}, 总计={usage.total_tokens}")
        return True
        
    except Exception as e:
        print(f"[FAIL] 失败: {e}")
        return False


def test_tool_calling(model="deepseek-chat"):
    """测试工具调用"""
    print(f"\n{'='*60}")
    print(f"[测试] 工具调用 - {model}")
    print('='*60)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个可以使用工具的助手。"},
                {"role": "user", "content": "现在几点了？顺便帮我计算 15 * 23"}
            ],
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=200
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            print(f"[OK] 工具调用成功!")
            for tool_call in message.tool_calls:
                print(f"   工具: {tool_call.function.name}")
                print(f"   参数: {tool_call.function.arguments}")
            return True
        else:
            print(f"[WARN] 模型未调用工具，直接回复:\n{message.content}")
            return False
            
    except Exception as e:
        print(f"[FAIL] 失败: {e}")
        if "tool" in str(e).lower():
            print("   提示: 此模型可能不支持工具调用")
        return False


def test_streaming(model="deepseek-chat"):
    """测试流式输出"""
    print(f"\n{'='*60}")
    print(f"[测试] 流式输出 - {model}")
    print('='*60)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "用3个词形容编程，并简单解释每个词"}
            ],
            max_tokens=150,
            stream=True
        )
        
        print("回复: ", end="", flush=True)
        full_content = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_content += content
        print("\n[OK] 流式输出完成!")
        return True
        
    except Exception as e:
        print(f"[FAIL] 失败: {e}")
        return False


def test_reasoning(model="deepseek-reasoner"):
    """测试推理模式 (R1)"""
    print(f"\n{'='*60}")
    print(f"[测试] 推理模式 - {model}")
    print('='*60)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "一个水池有进水管和出水管，单开进水管5小时注满，单开出水管7小时排空。同时打开两个管子，几小时注满水池？"}
            ],
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # 检查是否有 reasoning_content (R1 的思考过程)
        if hasattr(response.choices[0].message, 'reasoning_content'):
            reasoning = response.choices[0].message.reasoning_content
            print(f"[思考过程]:\n{reasoning[:200]}...")
            print(f"\n[OK] 最终答案:\n{content}")
        else:
            print(f"[OK] 回复:\n{content}")
        
        usage = response.usage
        print(f"\nToken 使用: 输入={usage.prompt_tokens}, 输出={usage.completion_tokens}, 总计={usage.total_tokens}")
        return True
        
    except Exception as e:
        print(f"[FAIL] 失败: {e}")
        return False


def test_json_mode(model="deepseek-chat"):
    """测试 JSON 模式"""
    print(f"\n{'='*60}")
    print(f"[测试] JSON 模式 - {model}")
    print('='*60)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个JSON生成器。请以JSON格式输出。"},
                {"role": "user", "content": "列出3种编程语言及其特点，格式: [{\"name\": \"\", \"features\": []}]"}
            ],
            response_format={"type": "json_object"},
            max_tokens=300
        )
        
        content = response.choices[0].message.content
        
        # 验证 JSON
        try:
            data = json.loads(content)
            print(f"[OK] JSON 解析成功!")
            print(f"\n内容:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        except json.JSONDecodeError:
            print(f"[WARN] 返回的不是有效 JSON:\n{content}")
            return False
            
    except Exception as e:
        print(f"[FAIL] 失败: {e}")
        return False


def test_multi_turn(model="deepseek-chat"):
    """测试多轮对话"""
    print(f"\n{'='*60}")
    print(f"[测试] 多轮对话 - {model}")
    print('='*60)
    
    messages = [
        {"role": "user", "content": "我叫张三，请记住我的名字。"}
    ]
    
    try:
        # 第一轮
        response1 = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=50
        )
        reply1 = response1.choices[0].message.content
        messages.append({"role": "assistant", "content": reply1})
        print(f"用户: 我叫张三，请记住我的名字。")
        print(f"助手: {reply1}")
        
        # 第二轮
        messages.append({"role": "user", "content": "我叫什么名字？"})
        response2 = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=50
        )
        reply2 = response2.choices[0].message.content
        
        print(f"\n用户: 我叫什么名字？")
        print(f"助手: {reply2}")
        
        if "张三" in reply2:
            print("\n[OK] 多轮对话记忆正常!")
            return True
        else:
            print("\n[WARN] 模型似乎没有记住名字")
            return False
            
    except Exception as e:
        print(f"[FAIL] 失败: {e}")
        return False


# =============================================================================
# 主函数
# =============================================================================

def main():
    print("="*60)
    print("DeepSeek API 完整测试")
    print("="*60)
    print(f"\nAPI Key: {API_KEY[:15]}...{API_KEY[-4:]}")
    print(f"Base URL: {BASE_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 1. 测试 deepseek-chat (V3)
    print("\n" + "="*60)
    print("[测试包] deepseek-chat (V3 系列)")
    print("="*60)
    
    results.append(("chat-basic", test_basic_chat("deepseek-chat")))
    results.append(("chat-tool", test_tool_calling("deepseek-chat")))
    results.append(("chat-stream", test_streaming("deepseek-chat")))
    results.append(("chat-json", test_json_mode("deepseek-chat")))
    results.append(("chat-multi", test_multi_turn("deepseek-chat")))
    
    # 2. 测试 deepseek-reasoner (R1)
    print("\n" + "="*60)
    print("[测试包] deepseek-reasoner (R1 系列)")
    print("="*60)
    
    results.append(("reasoner-basic", test_basic_chat("deepseek-reasoner")))
    results.append(("reasoner-reasoning", test_reasoning("deepseek-reasoner")))
    # R1 在 thinking 模式下不支持 tool calling，这里跳过
    
    # 3. 汇总结果
    print("\n" + "="*60)
    print("[测试结果汇总]")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    
    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"   {name:20s} {status}")
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    print("="*60)


if __name__ == "__main__":
    main()
