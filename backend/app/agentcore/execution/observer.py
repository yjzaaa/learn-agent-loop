"""
Execution Observer

执行观察器 - 用于调试和监控
"""

from typing import Callable, List, Optional
from datetime import datetime

from ..graph.repository import GraphRepository
from ..graph.models import ExecutionStep, ToolCall


class ExecutionObserver:
    """执行观察器 - 监控和记录执行过程"""
    
    def __init__(self, graph_repo: Optional[GraphRepository] = None):
        self.graph_repo = graph_repo
        self._listeners: List[Callable] = []
        self._step_history: List[dict] = []
        self._current_session: Optional[str] = None
    
    def add_listener(self, handler: Callable):
        """添加事件监听器"""
        self._listeners.append(handler)
    
    def remove_listener(self, handler: Callable):
        """移除事件监听器"""
        self._listeners = [h for h in self._listeners if h != handler]
    
    def _notify(self, event_type: str, data: dict):
        """通知所有监听器"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._step_history.append(event)
        
        for handler in self._listeners:
            try:
                handler(event)
            except Exception as e:
                print(f"[ExecutionObserver] Handler error: {e}")
    
    def on_step_start(self, step: ExecutionStep):
        """步骤开始回调"""
        self._notify("step_start", {
            "step_id": step.id,
            "step_number": step.step_number,
            "type": step.type.value,
            "started_at": step.started_at.isoformat()
        })
    
    def on_step_end(self, step: ExecutionStep):
        """步骤结束回调"""
        self._notify("step_end", {
            "step_id": step.id,
            "step_number": step.step_number,
            "status": step.status.value,
            "duration_ms": step.duration_ms,
            "token_count": step.token_count
        })
    
    def on_tool_call(self, tool_call: ToolCall):
        """工具调用回调"""
        self._notify("tool_call", {
            "tool_id": tool_call.id,
            "name": tool_call.name,
            "status": tool_call.status.value,
            "started_at": tool_call.started_at.isoformat() if tool_call.started_at else None
        })
    
    def on_tool_result(self, tool_call: ToolCall):
        """工具结果回调"""
        self._notify("tool_result", {
            "tool_id": tool_call.id,
            "name": tool_call.name,
            "status": tool_call.status.value,
            "duration_ms": tool_call.duration_ms,
            "output_preview": tool_call.output_preview
        })
    
    def on_state_change(self, state_type: str, state_data: dict):
        """状态变更回调"""
        self._notify("state_change", {
            "state_type": state_type,
            "data": state_data
        })
    
    def get_history(self) -> List[dict]:
        """获取执行历史"""
        return self._step_history.copy()
    
    def clear_history(self):
        """清除历史"""
        self._step_history.clear()
    
    def get_stats(self) -> dict:
        """获取执行统计"""
        steps = [e for e in self._step_history if e["type"] == "step_end"]
        tools = [e for e in self._step_history if e["type"] == "tool_result"]
        
        total_duration = sum(
            (e["data"].get("duration_ms") or 0) for e in steps
        )
        total_tokens = sum(
            (e["data"].get("token_count") or 0) for e in steps
        )
        
        return {
            "total_steps": len(steps),
            "total_tool_calls": len(tools),
            "total_duration_ms": total_duration,
            "total_tokens": total_tokens,
            "avg_step_duration_ms": total_duration / len(steps) if steps else 0
        }


class ExecutionReplayer:
    """执行回放器 - 重现 Agent 执行过程"""
    
    def __init__(self, graph_repo: GraphRepository):
        self.graph_repo = graph_repo
    
    async def replay(self, session_id: str, speed: float = 1.0, 
                     on_event: Optional[Callable] = None):
        """
        回放执行过程
        
        Args:
            session_id: 会话ID
            speed: 回放速度 (1.0 = 实时)
            on_event: 事件回调函数
        """
        import asyncio
        
        timeline = self.graph_repo.get_step_timeline(session_id)
        
        for step in timeline:
            # 发送步骤开始事件
            if on_event:
                on_event({
                    "type": "step_start",
                    "data": step
                })
            
            # 模拟执行时间
            duration = (step.get("duration_ms") or 1000) / 1000 / speed
            await asyncio.sleep(min(duration, 2))  # 最多等待2秒
            
            # 发送步骤结束事件
            if on_event:
                on_event({
                    "type": "step_end",
                    "data": step
                })
        
        return {"completed": True, "steps_replayed": len(timeline)}
