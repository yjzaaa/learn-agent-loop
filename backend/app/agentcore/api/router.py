"""
AgentCore API Router

REST API 路由定义
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from ..execution.engine import ExecutionEngine
from ..execution.events import event_emitter
from ..graph.repository import GraphRepository
from .schemas import (
    CreateSessionRequest, CreateSessionResponse,
    RunAgentRequest, RunAgentResponse,
    SessionResponse, SessionTimelineResponse,
    ToolStatsResponse, ErrorResponse
)

router = APIRouter(prefix="/agentcore", tags=["agentcore"])

# 全局执行引擎
execution_engine: Optional[ExecutionEngine] = None
graph_repo: Optional[GraphRepository] = None


def get_engine() -> ExecutionEngine:
    """获取执行引擎（懒加载）"""
    global execution_engine, graph_repo
    if execution_engine is None:
        graph_repo = GraphRepository()
        execution_engine = ExecutionEngine(graph_repo)
    return execution_engine


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """创建新的 Agent 会话"""
    try:
        engine = get_engine()
        session_id = engine.create_session(
            name=request.name,
            workdir=request.workdir,
            model=request.model
        )
        
        return CreateSessionResponse(
            session_id=session_id,
            name=request.name,
            workdir=request.workdir,
            created_at=__import__('datetime').datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    """列出所有会话"""
    try:
        engine = get_engine()
        sessions = engine.list_sessions()
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """获取会话详情"""
    try:
        engine = get_engine()
        status = engine.get_session_status(session_id)
        
        if not status["exists"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/run", response_model=RunAgentResponse)
async def run_agent(session_id: str, request: RunAgentRequest):
    """运行 Agent"""
    try:
        engine = get_engine()
        result = engine.run_agent(
            session_id=session_id,
            query=request.query,
            workdir=request.workdir
        )
        
        return RunAgentResponse(
            session_id=result["session_id"],
            status=result["status"],
            steps=result["steps"],
            message="Agent execution completed"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        import traceback
        print(f"[AgentCore] Run error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/sessions/{session_id}/timeline")
async def get_timeline(session_id: str):
    """获取会话执行时间线"""
    try:
        engine = get_engine()
        repo = engine.graph_repo
        timeline = repo.get_step_timeline(session_id)
        
        return {
            "session_id": session_id,
            "timeline": timeline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/tools/stats")
async def get_tool_stats(session_id: str):
    """获取工具调用统计"""
    try:
        engine = get_engine()
        repo = engine.graph_repo
        stats = repo.get_tool_stats(session_id)
        
        return {
            "session_id": session_id,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/graph")
async def get_execution_graph(session_id: str):
    """获取执行图谱"""
    try:
        engine = get_engine()
        graph = engine.get_execution_graph(session_id)
        
        if not graph:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return graph
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    # TODO: 实现删除逻辑
    return {"message": "Not implemented yet"}


# WebSocket 端点
@router.websocket("/ws/sessions/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 实时推送"""
    await websocket.accept()
    
    # 注册 WebSocket 连接
    event_emitter.add_websocket(session_id, websocket)
    
    try:
        while True:
            # 等待客户端消息
            data = await websocket.receive_text()
            # 可以处理客户端发送的命令
            
    except WebSocketDisconnect:
        # 移除 WebSocket 连接
        event_emitter.remove_websocket(session_id, websocket)
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        event_emitter.remove_websocket(session_id, websocket)
