"""
Execution Events

事件系统用于实时通知执行状态
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Callable, List
from pydantic import BaseModel
import asyncio


class EventType(str, Enum):
    """事件类型"""
    STEP_START = "step_start"
    STEP_END = "step_end"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MESSAGE = "message"
    STATE_CHANGE = "state_change"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    ERROR = "error"


class ExecutionEvent(BaseModel):
    """执行事件"""
    type: EventType
    session_id: str
    data: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventEmitter:
    """事件发射器 - 管理事件订阅和广播"""
    
    def __init__(self):
        self._listeners: Dict[EventType, List[Callable]] = {}
        self._all_listeners: List[Callable] = []
        self._websocket_connections: Dict[str, List] = {}  # session_id -> connections
    
    def on(self, event_type: EventType, handler: Callable):
        """订阅特定类型的事件"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(handler)
        return self
    
    def on_any(self, handler: Callable):
        """订阅所有事件"""
        self._all_listeners.append(handler)
        return self
    
    def off(self, event_type: EventType, handler: Callable):
        """取消订阅"""
        if event_type in self._listeners:
            self._listeners[event_type] = [
                h for h in self._listeners[event_type] if h != handler
            ]
    
    def emit(self, event: ExecutionEvent):
        """发射事件"""
        # 调用特定类型的监听器
        if event.type in self._listeners:
            for handler in self._listeners[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"[EventEmitter] Handler error: {e}")
        
        # 调用通用监听器
        for handler in self._all_listeners:
            try:
                handler(event)
            except Exception as e:
                print(f"[EventEmitter] Handler error: {e}")
        
        # 发送到 WebSocket
        self._broadcast_to_websocket(event)
    
    def add_websocket(self, session_id: str, websocket):
        """添加 WebSocket 连接"""
        if session_id not in self._websocket_connections:
            self._websocket_connections[session_id] = []
        self._websocket_connections[session_id].append(websocket)
    
    def remove_websocket(self, session_id: str, websocket):
        """移除 WebSocket 连接"""
        if session_id in self._websocket_connections:
            self._websocket_connections[session_id] = [
                ws for ws in self._websocket_connections[session_id] if ws != websocket
            ]
    
    def _broadcast_to_websocket(self, event: ExecutionEvent):
        """广播到 WebSocket 连接"""
        connections = self._websocket_connections.get(event.session_id, [])
        for ws in connections:
            try:
                # 异步发送
                if hasattr(ws, 'send_json'):
                    asyncio.create_task(ws.send_json(event.model_dump(mode='json')))
            except Exception as e:
                print(f"[EventEmitter] WebSocket send error: {e}")


# 全局事件发射器实例
event_emitter = EventEmitter()
