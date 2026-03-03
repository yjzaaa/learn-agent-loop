"""
Base Agent Classes

提供基础 Agent 功能和图谱感知 Agent
"""

import json
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Optional, List, Dict
from datetime import datetime

from .client import get_client, get_model
from ..graph.repository import GraphRepository
from ..graph.models import (
    StepType, StepStatus, ToolStatus, SessionStatus,
    TodoStatus, TaskStatus
)


class BaseAgent(ABC):
    """
    Agent 基类，提供通用功能
    """
    
    def __init__(self, workdir: Optional[Path] = None, max_tokens: int = 8000):
        self.client = get_client()
        self.model = get_model()
        self.workdir = workdir or Path.cwd()
        self.max_tokens = max_tokens
        self.system_prompt = f"You are a coding agent at {self.workdir}."
        
        # 工具注册表
        self._tools: Dict[str, tuple[Callable, dict]] = {}
        
        # 调用工具初始化
        self._init_tools()
    
    def _init_tools(self) -> None:
        """初始化工具。子类和 Mixin 类应该重写此方法注册工具。"""
        pass
    
    def register_tool(
        self,
        name: str,
        handler: Callable,
        description: str,
        parameters: dict,
        required: Optional[List[str]] = None
    ) -> None:
        """注册一个工具"""
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
    
    def get_tools(self) -> List[dict]:
        """获取所有注册工具的 schema 列表"""
        return [schema for _, schema in self._tools.values()]
    
    def run(self, messages: Optional[List[dict]] = None) -> List[dict]:
        """运行 Agent 循环"""
        if messages is None:
            messages = []
        
        while True:
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
            
            self.post_loop_hook(messages)
        
        return messages
    
    def _execute_tools(self, tool_calls: List[Any]) -> List[dict]:
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
            
            self._log_tool_call(name, str(output)[:200])
            
            results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(output),
            })
        
        return results
    
    def _log_tool_call(self, name: str, output_preview: str) -> None:
        """打印工具调用信息"""
        print(f"> {name}: {output_preview}")
    
    def pre_loop_hook(self, messages: List[dict]) -> None:
        """每次 LLM 调用前执行的钩子"""
        pass
    
    def post_loop_hook(self, messages: List[dict]) -> None:
        """每次工具执行后执行的钩子"""
        pass
    
    def safe_path(self, path: str) -> Path:
        """验证路径是否在工作目录内"""
        resolved = (self.workdir / path).resolve()
        if not resolved.is_relative_to(self.workdir):
            raise ValueError(f"Path escapes workspace: {path}")
        return resolved


class GraphAwareAgent(BaseAgent):
    """
    图谱感知的 Agent 基类
    
    在运行时自动构建知识图谱
    """
    
    def __init__(self, session_id: Optional[str] = None, 
                 graph_repo: Optional[GraphRepository] = None,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.session_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        self.graph_repo = graph_repo or GraphRepository()
        
        self._current_step_id: Optional[str] = None
        self._step_counter = 0
        self._tool_counter = 0
        
        # 创建会话记录
        self._create_session_record()
    
    def _create_session_record(self):
        """创建会话记录（如果不存在）"""
        try:
            # 先检查会话是否已存在
            existing = self.graph_repo.get_session(self.session_id)
            if existing:
                return  # 会话已存在，跳过创建
            
            self.graph_repo.create_session(
                session_id=self.session_id,
                name=f"Session {self.session_id}",
                workdir=str(self.workdir),
                model=self.model,
                system_prompt=self.system_prompt
            )
        except Exception as e:
            print(f"[GraphAwareAgent] Warning: Failed to create session record: {e}")
    
    def run(self, messages: Optional[List[dict]] = None) -> List[dict]:
        """运行 Agent，同时构建知识图谱"""
        if messages is None:
            messages = []
        
        try:
            # 更新会话状态为活跃
            self.graph_repo.update_session_status(
                self.session_id, 
                SessionStatus.ACTIVE
            )
            
            while True:
                # 1. 创建 LLM 调用步骤
                self._step_counter += 1
                step = self.graph_repo.create_execution_step(
                    session_id=self.session_id,
                    step_type=StepType.LLM_CALL,
                    step_number=self._step_counter
                )
                self._current_step_id = step.id
                
                self.pre_loop_hook(messages)
                
                # 2. 调用 LLM
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": self.system_prompt}] + messages,
                    tools=self.get_tools(),
                    max_tokens=self.max_tokens,
                )
                
                assistant_message = response.choices[0].message
                
                # 3. 创建消息记录
                tool_calls_data = None
                if assistant_message.tool_calls:
                    tool_calls_data = [tc.model_dump() for tc in assistant_message.tool_calls]
                
                self.graph_repo.create_message(
                    step_id=step.id,
                    role="assistant",
                    content=assistant_message.content or "",
                    tool_calls=tool_calls_data
                )
                
                # 4. 更新步骤
                self.graph_repo.update_execution_step(
                    step_id=step.id,
                    status=StepStatus.COMPLETED,
                    finish_reason=response.choices[0].finish_reason,
                    token_count=response.usage.total_tokens if response.usage else None
                )
                
                # 5. 添加到消息历史
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": tool_calls_data
                })
                
                # 6. 检查是否结束
                if response.choices[0].finish_reason != "tool_calls":
                    break
                
                # 7. 执行工具（带图谱记录）
                self._execute_tools_with_graph(assistant_message.tool_calls, step.id)
                
                self.post_loop_hook(messages)
            
            # 更新会话状态为完成
            self.graph_repo.update_session_status(
                self.session_id,
                SessionStatus.COMPLETED,
                ended_at=datetime.utcnow()
            )
            
        except Exception as e:
            # 更新会话状态为错误
            self.graph_repo.update_session_status(
                self.session_id,
                SessionStatus.ERROR,
                ended_at=datetime.utcnow()
            )
            raise
        
        return messages
    
    def _execute_tools_with_graph(self, tool_calls: List[Any], step_id: str) -> List[dict]:
        """执行工具调用并记录到图谱"""
        results = []
        
        # 创建工具执行步骤
        self._step_counter += 1
        tool_step = self.graph_repo.create_execution_step(
            session_id=self.session_id,
            step_type=StepType.TOOL_EXECUTION,
            step_number=self._step_counter
        )
        
        for tool_call in tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            # 创建工具调用记录
            tool_record = self.graph_repo.create_tool_call(
                step_id=tool_step.id,
                name=name,
                arguments=args
            )
            
            handler, _ = self._tools.get(name, (None, None))
            
            try:
                if handler:
                    output = handler(**args)
                    status = ToolStatus.SUCCESS
                    error_msg = None
                else:
                    output = f"Unknown tool: {name}"
                    status = ToolStatus.ERROR
                    error_msg = "Tool not found"
            except Exception as e:
                output = f"Error: {e}"
                status = ToolStatus.ERROR
                error_msg = str(e)
            
            # 更新工具调用结果
            self.graph_repo.update_tool_call(
                tool_id=tool_record.id,
                output=str(output),
                status=status,
                error_message=error_msg
            )
            
            # 创建工具结果消息
            self.graph_repo.create_message(
                step_id=tool_step.id,
                role="tool",
                content=str(output)
            )
            
            self._log_tool_call(name, str(output)[:200])
            
            results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(output),
            })
        
        # 更新工具执行步骤
        self.graph_repo.update_execution_step(
            step_id=tool_step.id,
            status=StepStatus.COMPLETED
        )
        
        return results
