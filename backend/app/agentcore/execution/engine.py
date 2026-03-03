"""
Execution Engine

管理 Agent 执行和图谱构建
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from ..core.base_agent import GraphAwareAgent
from ..core.mixins import (
    ToolsMixin, TodoMixin, TaskMixin, SkillMixin,
    CompressionMixin, BackgroundMixin, SubagentMixin
)
from ..graph.repository import GraphRepository
from ..graph.models import SessionStatus
from .events import event_emitter, ExecutionEvent, EventType


class FullAgent(
    CompressionMixin,
    BackgroundMixin,
    TodoMixin,
    SubagentMixin,
    SkillMixin,
    TaskMixin,
    ToolsMixin,
    GraphAwareAgent
):
    """
    完整 Agent - 包含所有功能
    
    Mixin 顺序决定钩子调用顺序
    """
    
    def __init__(self, session_id: Optional[str] = None, **kwargs):
        super().__init__(session_id=session_id, **kwargs)
        
        self.system_prompt = f"""You are a coding agent at {self.workdir}.
Use tools to solve tasks.

Features available:
- TodoWrite: Short checklists for immediate work
- task_create/update/list: Persistent tasks with dependencies
- task: Subagent delegation for isolated work
- load_skill: Specialized knowledge on demand
- compact: Manual conversation compression
- background_run: Non-blocking command execution

Skills available:
{self.get_skill_descriptions()}

The system will automatically compress context when needed."""


class ExecutionEngine:
    """执行引擎 - 管理 Agent 执行"""
    
    def __init__(self, graph_repo: Optional[GraphRepository] = None):
        self.graph_repo = graph_repo or GraphRepository()
        self._active_sessions: Dict[str, FullAgent] = {}
    
    def create_session(self, name: str, workdir: str, model: Optional[str] = None) -> str:
        """创建新会话"""
        import uuid
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        
        # 创建工作目录
        work_path = Path(workdir)
        work_path.mkdir(parents=True, exist_ok=True)
        
        # 创建会话记录
        system_prompt = f"You are a coding agent at {workdir}."
        self.graph_repo.create_session(
            name=name,
            workdir=str(work_path),
            model=model or "gpt-4",
            system_prompt=system_prompt,
            session_id=session_id
        )
        
        # 发射会话开始事件
        event_emitter.emit(ExecutionEvent(
            type=EventType.SESSION_START,
            session_id=session_id,
            data={"name": name, "workdir": str(work_path)}
        ))
        
        return session_id
    
    def run_agent(self, session_id: str, query: str, 
                  workdir: Optional[str] = None) -> Dict[str, Any]:
        """运行 Agent"""
        # 获取会话信息
        session = self.graph_repo.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # 检查 API key 是否配置
        from ..core.client import API_KEY
        if not API_KEY:
            raise ValueError("API key not configured. Please set ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, or OPENAI_API_KEY environment variable.")
        
        # 创建 Agent 实例
        try:
            agent = FullAgent(
                session_id=session_id,
                graph_repo=self.graph_repo,
                workdir=Path(workdir or session.workdir),
                max_tokens=session.max_tokens
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize agent: {e}")
        
        self._active_sessions[session_id] = agent
        
        try:
            # 发射步骤开始事件
            event_emitter.emit(ExecutionEvent(
                type=EventType.STEP_START,
                session_id=session_id,
                data={"step_number": 1, "type": "llm_call"}
            ))
            
            # 运行 Agent
            messages = [{"role": "user", "content": query}]
            result = agent.run(messages)
            
            # 发射会话结束事件
            event_emitter.emit(ExecutionEvent(
                type=EventType.SESSION_END,
                session_id=session_id,
                data={"status": "completed", "step_count": agent._step_counter}
            ))
            
            return {
                "session_id": session_id,
                "status": "completed",
                "messages": result,
                "steps": agent._step_counter
            }
            
        except Exception as e:
            # 发射错误事件
            event_emitter.emit(ExecutionEvent(
                type=EventType.ERROR,
                session_id=session_id,
                data={"error": str(e)}
            ))
            raise
        finally:
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
        session = self.graph_repo.get_session(session_id)
        if not session:
            return {"exists": False}
        
        # 获取执行时间线
        timeline = self.graph_repo.get_step_timeline(session_id)
        
        return {
            "exists": True,
            "session": session.dict(),
            "timeline": timeline,
            "is_running": session_id in self._active_sessions
        }
    
    def get_execution_graph(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取执行图谱"""
        graph = self.graph_repo.get_execution_graph(session_id)
        if not graph:
            return None
        
        return {
            "session": graph.session.dict(),
            "steps": [s.dict() for s in graph.steps],
            "tool_calls": [t.dict() for t in graph.tool_calls],
            "node_count": len(graph.steps) + len(graph.tool_calls),
            "edge_count": len(graph.steps) - 1 if len(graph.steps) > 0 else 0
        }
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        sessions = self.graph_repo.get_sessions()
        return [{
            "id": s.id,
            "name": s.name,
            "status": s.status.value,
            "started_at": s.started_at.isoformat(),
            "model": s.model,
            "total_steps": s.total_steps
        } for s in sessions]
