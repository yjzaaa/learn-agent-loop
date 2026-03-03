#!/usr/bin/env python3
"""
BaseAgent - Agent 基类

提供所有 Agent 共用的基础功能：
- 客户端配置
- 基础 Agent 循环
- 工具注册和执行机制
- 消息历史管理
"""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Optional

from .client import get_client, get_model


class BaseAgent(ABC):
    """
    Agent 基类，提供通用功能。
    
    子类应该：
    1. 在 __init__ 中设置 self.system_prompt
    2. 在 __init__ 后调用 _init_tools() 注册工具
    3. 可选：重写 pre_loop_hook() 和 post_loop_hook()
    
    Mixin 类应该：
    1. 在 __init__ 中调用 super().__init__()
    2. 实现 _init_tools() 方法调用 register_tool()
    """
    
    def __init__(self, workdir: Optional[Path] = None, max_tokens: int = 8000):
        """
        初始化 Agent。
        
        Args:
            workdir: 工作目录，默认为当前目录
            max_tokens: 每次 LLM 调用的最大 token 数
        """
        self.client = get_client()
        self.model = get_model()
        self.workdir = workdir or Path.cwd()
        self.max_tokens = max_tokens
        
        # 系统提示词，子类应该设置
        self.system_prompt = f"You are a coding agent at {self.workdir}."
        
        # 工具注册表: {tool_name: (handler_func, tool_schema)}
        self._tools: dict[str, tuple[Callable, dict]] = {}
        
        # 工具调用历史记录
        self._tool_history: list[dict] = []
        
        # 调用工具初始化（让 Mixin 类注册工具）
        self._init_tools()
    
    def _init_tools(self) -> None:
        """
        初始化工具。子类和 Mixin 类应该重写此方法注册工具。
        
        注意：此方法在 __init__ 末尾调用，确保所有属性已设置。
        """
        pass
    
    # === 工具注册 ===
    
    def register_tool(
        self,
        name: str,
        handler: Callable,
        description: str,
        parameters: dict,
        required: Optional[list[str]] = None
    ) -> None:
        """
        注册一个工具。
        
        Args:
            name: 工具名称
            handler: 处理函数，接收关键字参数
            description: 工具描述
            parameters: 参数定义字典
            required: 必需参数列表
        """
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required or [],
                },
            },
        }
        self._tools[name] = (handler, schema)
    
    def get_tools(self) -> list[dict]:
        """获取所有注册工具的 schema 列表"""
        return [schema for _, schema in self._tools.values()]
    
    # === 核心 Agent 循环 ===
    
    def run(self, messages: Optional[list] = None) -> list:
        """
        运行 Agent 循环。
        
        Args:
            messages: 初始消息列表，为空则创建新列表
            
        Returns:
            完整的消息历史
        """
        if messages is None:
            messages = []
        
        while True:
            # 子类可以通过钩子干预循环
            self.pre_loop_hook(messages)
            
            # 调用 LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self.system_prompt}] + messages,
                tools=self.get_tools(),
                max_tokens=self.max_tokens,
            )
            
            assistant_message = response.choices[0].message
            messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls] if assistant_message.tool_calls else None
            })
            
            # 检查是否结束
            if response.choices[0].finish_reason != "tool_calls":
                break
            
            # 执行工具调用
            results = self._execute_tools(assistant_message.tool_calls)
            messages.append({"role": "user", "content": results})
            
            # 子类钩子
            self.post_loop_hook(messages)
        
        return messages
    
    def _execute_tools(self, tool_calls: list) -> list[dict]:
        """执行工具调用列表"""
        results = []
        for tool_call in tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            handler, _ = self._tools.get(name, (None, None))
            
            try:
                if handler:
                    output = handler(**args)
                else:
                    output = f"Unknown tool: {name}"
            except Exception as e:
                output = f"Error: {e}"
            
            # 打印工具调用（用于调试）
            self._log_tool_call(name, str(output)[:200])
            
            results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(output),
            })
            
            # 记录到历史
            self._tool_history.append({
                "name": name,
                "args": args,
                "output": str(output),
            })
        
        return results
    
    def _log_tool_call(self, name: str, output_preview: str) -> None:
        """打印工具调用信息，子类可以重写"""
        print(f"> {name}: {output_preview}")
    
    # === 钩子方法 ===
    
    def pre_loop_hook(self, messages: list) -> None:
        """
        每次 LLM 调用前执行的钩子。
        子类可以重写以实现自定义逻辑。
        """
        pass
    
    def post_loop_hook(self, messages: list) -> None:
        """
        每次工具执行后执行的钩子。
        子类可以重写以实现自定义逻辑。
        """
        pass
    
    # === 实用方法 ===
    
    def safe_path(self, path: str) -> Path:
        """
        验证路径是否在工作目录内。
        
        Args:
            path: 相对或绝对路径
            
        Returns:
            解析后的 Path 对象
            
        Raises:
            ValueError: 如果路径逃逸出工作目录
        """
        resolved = (self.workdir / path).resolve()
        if not resolved.is_relative_to(self.workdir):
            raise ValueError(f"Path escapes workspace: {path}")
        return resolved
    
    def interactive_mode(self, prompt: str = ">> ") -> None:
        """
        运行交互式 REPL 模式。
        
        Args:
            prompt: 输入提示符
        """
        history = []
        
        while True:
            try:
                query = input(f"\033[36m{prompt}\033[0m")
            except (EOFError, KeyboardInterrupt):
                break
            
            query = query.strip()
            if query.lower() in ("q", "exit", "quit"):
                break
            
            # 处理斜杠命令
            if query.startswith("/"):
                if self._handle_command(query, history):
                    continue
            
            if query:
                history.append({"role": "user", "content": query})
                history = self.run(history)
                
                # 打印最后的回复
                if history and history[-1]["role"] == "assistant":
                    content = history[-1].get("content", "")
                    if content:
                        print(content)
                print()
    
    def _handle_command(self, cmd: str, history: list) -> bool:
        """
        处理斜杠命令。
        
        Args:
            cmd: 命令字符串
            history: 消息历史
            
        Returns:
            如果命令被处理返回 True
        """
        # 基础命令，子类可以扩展
        if cmd == "/clear":
            history.clear()
            print("History cleared.")
            return True
        elif cmd == "/history":
            for msg in history:
                role = msg["role"]
                content = msg.get("content", "")
                if content:
                    print(f"[{role}] {content[:100]}...")
            return True
        return False
