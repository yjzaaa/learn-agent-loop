#!/usr/bin/env python3
"""
Kimi Code 测试脚本 - 使用 OpenAI 兼容格式连接 Kimi Code 模型

使用方法:
    1. 设置环境变量 KIMI_API_KEY
    2. .venv\Scripts\python test_kimi_code.py
    3. 输入问题，输入 'q' 或 'exit' 退出

环境变量:
    KIMI_API_KEY - Kimi API 密钥
    KIMI_BASE_URL - API 基础 URL (可选，默认: https://api.moonshot.cn/v1)
    KIMI_MODEL - 模型名称 (可选，默认: kimi-k2-0711-preview)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# 尝试导入 openai 库
try:
    from openai import OpenAI
except ImportError:
    print("[错误] 需要安装 openai 库")
    print("运行: .venv\\Scripts\\pip install openai")
    sys.exit(1)


# =============================================================================
# 配置
# =============================================================================

# API 配置
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
KIMI_MODEL = os.getenv("KIMI_MODEL", "kimi-k2-0711-preview")

# 工作目录
WORKDIR = Path.cwd()

# 系统提示词
SYSTEM_PROMPT = f"""你是一个 Kimi Code 编程助手，工作目录: {WORKDIR}

你可以使用以下工具来帮助用户:
- bash: 执行 shell 命令
- read_file: 读取文件内容
- write_file: 写入文件内容
- edit_file: 编辑文件内容

请使用工具来完成用户的请求，并在完成后提供简洁的总结。"""


# =============================================================================
# 工具定义
# =============================================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "执行 shell 命令，如 ls、grep、find、cat 等",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 shell 命令"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "最大读取行数（可选）"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
            "function": {
            "name": "write_file",
            "description": "写入内容到文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "替换文件中的文本",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "old_text": {
                        "type": "string",
                        "description": "要替换的旧文本"
                    },
                    "new_text": {
                        "type": "string",
                        "description": "新文本"
                    }
                },
                "required": ["path", "old_text", "new_text"]
            }
        }
    }
]


# =============================================================================
# 工具实现
# =============================================================================

import subprocess


def safe_path(p: str) -> Path:
    """确保路径不会逃逸出工作目录"""
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"路径逃逸出工作区: {p}")
    return path


def run_bash(command: str) -> str:
    """执行 shell 命令"""
    # 危险命令检查
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "错误: 危险命令被阻止"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        output = (result.stdout + result.stderr).strip()
        return output[:50000] if output else "(无输出)"
    except subprocess.TimeoutExpired:
        return "错误: 命令超时 (60秒)"
    except Exception as e:
        return f"错误: {e}"


def run_read_file(path: str, limit: Optional[int] = None) -> str:
    """读取文件内容"""
    try:
        text = safe_path(path).read_text(encoding="utf-8")
        lines = text.splitlines()
        
        if limit and limit < len(lines):
            lines = lines[:limit]
            lines.append(f"... ({len(text.splitlines()) - limit} 行更多)")
        
        return "\n".join(lines)[:50000]
    except Exception as e:
        return f"错误: {e}"


def run_write_file(path: str, content: str) -> str:
    """写入文件"""
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
        return f"已写入 {len(content)} 字节到 {path}"
    except Exception as e:
        return f"错误: {e}"


def run_edit_file(path: str, old_text: str, new_text: str) -> str:
    """编辑文件"""
    try:
        fp = safe_path(path)
        content = fp.read_text(encoding="utf-8")
        
        if old_text not in content:
            return f"错误: 在 {path} 中未找到文本"
        
        new_content = content.replace(old_text, new_text, 1)
        fp.write_text(new_content, encoding="utf-8")
        return f"已编辑 {path}"
    except Exception as e:
        return f"错误: {e}"


def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    """执行工具调用"""
    if name == "bash":
        return run_bash(arguments.get("command", ""))
    elif name == "read_file":
        return run_read_file(arguments.get("path", ""), arguments.get("limit"))
    elif name == "write_file":
        return run_write_file(arguments.get("path", ""), arguments.get("content", ""))
    elif name == "edit_file":
        return run_edit_file(
            arguments.get("path", ""),
            arguments.get("old_text", ""),
            arguments.get("new_text", "")
        )
    else:
        return f"未知工具: {name}"


# =============================================================================
# 主代理循环
# =============================================================================

def run_agent(client: OpenAI, messages: List[Dict[str, Any]]) -> str:
    """运行代理循环"""
    
    while True:
        # 调用模型
        response = client.chat.completions.create(
            model=KIMI_MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=8000,
            temperature=0.7
        )
        
        message = response.choices[0].message
        
        # 如果有工具调用
        if message.tool_calls:
            # 添加助手的消息（包含工具调用）
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })
            
            # 执行工具调用
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                import json
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"  [工具] {tool_name}: {tool_args}")
                
                # 执行工具
                result = execute_tool(tool_name, tool_args)
                
                # 截断显示
                display_result = result[:200] + "..." if len(result) > 200 else result
                print(f"  [结果] {display_result}")
                
                # 添加工具结果到消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        
        # 如果没有工具调用，返回文本回复
        else:
            content = message.content or ""
            messages.append({"role": "assistant", "content": content})
            return content


# =============================================================================
# REPL 交互
# =============================================================================

def main():
    """主函数"""
    
    # 检查 API 密钥
    if not KIMI_API_KEY:
        print("[错误] 请设置 KIMI_API_KEY 环境变量")
        print("示例: set KIMI_API_KEY=your-api-key")
        print("\n获取 API Key: https://platform.moonshot.cn")
        sys.exit(1)
    
    # 创建 OpenAI 客户端
    client = OpenAI(
        api_key=KIMI_API_KEY,
        base_url=KIMI_BASE_URL
    )
    
    print("=" * 60)
    print("Kimi Code 测试脚本")
    print("=" * 60)
    print(f"模型: {KIMI_MODEL}")
    print(f"工作目录: {WORKDIR}")
    print(f"API 地址: {KIMI_BASE_URL}")
    print()
    print("可用命令:")
    print("  /tools - 显示可用工具")
    print("  /clear - 清除对话历史")
    print("  q/exit - 退出")
    print()
    print("输入您的问题:")
    print("-" * 60)
    
    # 对话历史
    history: List[Dict[str, Any]] = []
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n你: ").strip()
            
            # 空输入跳过
            if not user_input:
                continue
            
            # 退出命令
            if user_input.lower() in ("q", "quit", "exit"):
                print("再见!")
                break
            
            # 显示工具
            if user_input == "/tools":
                print("\n可用工具:")
                for tool in TOOLS:
                    print(f"  - {tool['function']['name']}: {tool['function']['description']}")
                continue
            
            # 清除历史
            if user_input == "/clear":
                history = []
                print("对话历史已清除")
                continue
            
            # 添加用户消息
            history.append({"role": "user", "content": user_input})
            
            # 运行代理
            print("\nKimi Code:")
            response = run_agent(client, history)
            print(response)
            
        except KeyboardInterrupt:
            print("\n再见!")
            break
        except Exception as e:
            print(f"\n错误: {e}")


if __name__ == "__main__":
    main()
