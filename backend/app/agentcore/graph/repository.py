"""
Graph Repository

知识图谱数据操作仓库
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from .database import KuzuDatabase
from .models import (
    AgentSession, ExecutionStep, ToolCall, Message,
    Task, Todo, Skill, Teammate, BackgroundJob,
    SubagentRun, Artifact, Compression,
    StepType, StepStatus, ToolStatus, TaskStatus, TodoStatus,
    SessionStatus, ExecutionGraph
)


class GraphRepository:
    """图谱操作仓库"""
    
    def __init__(self, db: Optional[KuzuDatabase] = None):
        self.db = db or KuzuDatabase()
    
    # === Session Operations ===
    
    def create_session(self, name: str, workdir: str, model: str,
                       system_prompt: str, session_id: Optional[str] = None, **kwargs) -> AgentSession:
        """创建会话"""
        if session_id is None:
            session_id = f"sess_{uuid.uuid4().hex[:8]}"
        session = AgentSession(
            id=session_id,
            name=name,
            workdir=workdir,
            model=model,
            system_prompt=system_prompt,
            **kwargs
        )
        
        query = """
        CREATE (s:AgentSession {
            id: $id,
            name: $name,
            workdir: $workdir,
            model: $model,
            systemPrompt: $system_prompt,
            status: $status,
            startedAt: $started_at,
            maxTokens: $max_tokens,
            totalSteps: $total_steps,
            totalToolCalls: $total_tool_calls,
            metadata: $metadata
        })
        """
        
        self.db.execute(query, {
            "id": session.id,
            "name": session.name,
            "workdir": session.workdir,
            "model": session.model,
            "system_prompt": session.system_prompt,
            "status": session.status.value,
            "started_at": session.started_at,
            "max_tokens": session.max_tokens,
            "total_steps": session.total_steps,
            "total_tool_calls": session.total_tool_calls,
            "metadata": session.metadata or ""
        })
        
        return session
    
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """获取会话"""
        query = "MATCH (s:AgentSession {id: $id}) RETURN s"
        result = self.db.execute(query, {"id": session_id})
        
        if result.has_next():
            row = result.get_next()
            props = row[0]
            return AgentSession(
                id=props["id"],
                name=props["name"],
                workdir=props["workdir"],
                model=props["model"],
                system_prompt=props["systemPrompt"],
                status=SessionStatus(props["status"]),
                started_at=props["startedAt"],
                max_tokens=props["maxTokens"],
                total_steps=props["totalSteps"],
                total_tool_calls=props["totalToolCalls"],
                metadata=props.get("metadata")
            )
        return None
    
    def update_session_status(self, session_id: str, status: SessionStatus,
                              ended_at: Optional[datetime] = None):
        """更新会话状态"""
        query = """
        MATCH (s:AgentSession {id: $id})
        SET s.status = $status
        """
        params = {"id": session_id, "status": status.value}
        
        if ended_at:
            query += ", s.endedAt = $ended_at"
            params["ended_at"] = ended_at
        
        self.db.execute(query, params)
    
    # === Execution Step Operations ===
    
    def create_execution_step(self, session_id: str, step_type: StepType,
                              step_number: int) -> ExecutionStep:
        """创建执行步骤"""
        step_id = f"{session_id}:step_{step_number}"
        step = ExecutionStep(
            id=step_id,
            step_number=step_number,
            type=step_type,
            status=StepStatus.RUNNING
        )
        
        # 创建节点 (使用 MERGE 避免重复)
        query = """
        MERGE (s:ExecutionStep {id: $id})
        ON CREATE SET s.stepNumber = $step_number,
                      s.type = $type,
                      s.status = $status,
                      s.startedAt = $started_at
        ON MATCH SET s.status = $status,
                     s.startedAt = $started_at
        """
        self.db.execute(query, {
            "id": step.id,
            "step_number": step.step_number,
            "type": step.type.value,
            "status": step.status.value,
            "started_at": step.started_at
        })
        
        # 创建 HAS_STEP 关系
        query2 = """
        MATCH (sess:AgentSession {id: $session_id})
        MATCH (step:ExecutionStep {id: $step_id})
        CREATE (sess)-[:HAS_STEP]->(step)
        """
        self.db.execute(query2, {
            "session_id": session_id,
            "step_id": step_id
        })
        
        # 创建 NEXT_STEP 关系（如果不是第一步）
        if step_number > 1:
            prev_step_id = f"{session_id}:step_{step_number - 1}"
            query3 = """
            MATCH (prev:ExecutionStep {id: $prev_id})
            MATCH (curr:ExecutionStep {id: $curr_id})
            CREATE (prev)-[:NEXT_STEP]->(curr)
            """
            try:
                self.db.execute(query3, {
                    "prev_id": prev_step_id,
                    "curr_id": step_id
                })
            except Exception:
                pass  # 前一步可能不存在
        
        return step
    
    def update_execution_step(self, step_id: str,
                              status: Optional[StepStatus] = None,
                              finish_reason: Optional[str] = None,
                              token_count: Optional[int] = None):
        """更新执行步骤"""
        ended_at = datetime.utcnow() if status == StepStatus.COMPLETED else None
        
        query = "MATCH (s:ExecutionStep {id: $id})"
        sets = []
        params = {"id": step_id}
        
        if status:
            sets.append("s.status = $status")
            params["status"] = status.value
        
        if finish_reason:
            sets.append("s.finishReason = $finish_reason")
            params["finish_reason"] = finish_reason
        
        if token_count is not None:
            sets.append("s.tokenCount = $token_count")
            params["token_count"] = token_count
        
        if ended_at:
            sets.append("s.endedAt = $ended_at")
            params["ended_at"] = ended_at
            sets.append("s.durationMs = timestamp() - s.startedAt")
        
        if sets:
            query += " SET " + ", ".join(sets)
            self.db.execute(query, params)
    
    # === Tool Call Operations ===
    
    def create_tool_call(self, step_id: str, name: str,
                         arguments: dict) -> ToolCall:
        """创建工具调用"""
        tool_id = f"{step_id}:tool_{uuid.uuid4().hex[:6]}"
        tool = ToolCall(
            id=tool_id,
            name=name,
            arguments=json.dumps(arguments)
        )
        
        # 创建节点
        query = """
        CREATE (t:ToolCall {
            id: $id,
            name: $name,
            arguments: $arguments,
            status: $status,
            startedAt: $started_at
        })
        """
        self.db.execute(query, {
            "id": tool.id,
            "name": tool.name,
            "arguments": tool.arguments,
            "status": tool.status.value,
            "started_at": tool.started_at
        })
        
        # 创建 CALLS_TOOL 关系
        query2 = """
        MATCH (step:ExecutionStep {id: $step_id})
        MATCH (tool:ToolCall {id: $tool_id})
        CREATE (step)-[:CALLS_TOOL]->(tool)
        """
        self.db.execute(query2, {
            "step_id": step_id,
            "tool_id": tool_id
        })
        
        return tool
    
    def update_tool_call(self, tool_id: str, output: str,
                         status: ToolStatus = ToolStatus.SUCCESS,
                         error_message: Optional[str] = None):
        """更新工具调用结果"""
        ended_at = datetime.utcnow()
        output_preview = output[:200] if len(output) > 200 else output
        
        query = """
        MATCH (t:ToolCall {id: $id})
        SET t.output = $output,
            t.outputPreview = $output_preview,
            t.status = $status,
            t.endedAt = $ended_at,
            t.durationMs = timestamp() - t.startedAt
        """
        params = {
            "id": tool_id,
            "output": output,
            "output_preview": output_preview,
            "status": status.value,
            "ended_at": ended_at.isoformat()
        }
        
        if error_message:
            query += ", t.errorMessage = $error_message"
            params["error_message"] = error_message
        
        self.db.execute(query, params)
    
    # === Message Operations ===
    
    def create_message(self, step_id: str, role: str, content: str,
                       tool_calls: Optional[list] = None) -> Message:
        """创建消息"""
        msg_id = f"{step_id}:msg_{uuid.uuid4().hex[:6]}"
        content_preview = content[:200] if len(content) > 200 else content
        
        msg = Message(
            id=msg_id,
            role=role,
            content=content,
            content_preview=content_preview,
            tool_calls=json.dumps(tool_calls) if tool_calls else None
        )
        
        # 创建节点
        query = """
        CREATE (m:Message {
            id: $id,
            role: $role,
            content: $content,
            contentPreview: $content_preview,
            toolCalls: $tool_calls,
            createdAt: $created_at
        })
        """
        self.db.execute(query, {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "content_preview": msg.content_preview or "",
            "tool_calls": msg.tool_calls or "",
            "created_at": msg.created_at
        })
        
        # 创建 HAS_MESSAGE 关系
        query2 = """
        MATCH (step:ExecutionStep {id: $step_id})
        MATCH (msg:Message {id: $msg_id})
        CREATE (step)-[:HAS_MESSAGE]->(msg)
        """
        self.db.execute(query2, {
            "step_id": step_id,
            "msg_id": msg_id
        })
        
        return msg
    
    # === Query Operations ===
    
    def get_execution_graph(self, session_id: str) -> Optional[ExecutionGraph]:
        """获取完整执行图谱"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # 获取所有步骤
        steps_query = """
        MATCH (s:AgentSession {id: $session_id})-[:HAS_STEP]->(step:ExecutionStep)
        RETURN step
        ORDER BY step.stepNumber
        """
        steps_result = self.db.execute(steps_query, {"session_id": session_id})
        steps = []
        while steps_result.has_next():
            row = steps_result.get_next()
            props = row[0]
            steps.append(ExecutionStep(
                id=props["id"],
                step_number=props["stepNumber"],
                type=StepType(props["type"]),
                status=StepStatus(props["status"]),
                started_at=props["startedAt"],
                token_count=props.get("tokenCount")
            ))
        
        # 获取所有工具调用
        tools_query = """
        MATCH (s:AgentSession {id: $session_id})-[:HAS_STEP]->(:ExecutionStep)-[:CALLS_TOOL]->(tool:ToolCall)
        RETURN tool
        """
        tools_result = self.db.execute(tools_query, {"session_id": session_id})
        tool_calls = []
        while tools_result.has_next():
            row = tools_result.get_next()
            props = row[0]
            tool_calls.append(ToolCall(
                id=props["id"],
                name=props["name"],
                arguments=props["arguments"],
                output=props.get("output"),
                status=ToolStatus(props["status"])
            ))
        
        return ExecutionGraph(
            session=session,
            steps=steps,
            tool_calls=tool_calls,
            messages=[],
            tasks=[],
            todos=[],
            edges=[]
        )
    
    def get_step_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """获取执行时间线"""
        # 先获取所有步骤
        query = """
        MATCH (s:AgentSession {id: $session_id})-[:HAS_STEP]->(step:ExecutionStep)
        RETURN step
        ORDER BY step.stepNumber
        """
        result = self.db.execute(query, {"session_id": session_id})
        
        timeline = []
        while result.has_next():
            row = result.get_next()
            step_props = row[0]
            
            # 单独查询每个步骤的工具调用数量
            tool_query = """
            MATCH (step:ExecutionStep {id: $step_id})-[:CALLS_TOOL]->(tool:ToolCall)
            RETURN count(tool) as tool_count
            """
            tool_result = self.db.execute(tool_query, {"step_id": step_props["id"]})
            tool_count = 0
            if tool_result.has_next():
                tool_row = tool_result.get_next()
                tool_count = tool_row[0]
            
            timeline.append({
                "step_number": step_props["stepNumber"],
                "type": step_props["type"],
                "status": step_props["status"],
                "started_at": step_props["startedAt"].isoformat() if step_props.get("startedAt") else None,
                "duration_ms": step_props.get("durationMs"),
                "token_count": step_props.get("tokenCount"),
                "finish_reason": step_props.get("finishReason"),
                "tool_count": tool_count
            })
        
        return timeline
    
    def get_tool_stats(self, session_id: str) -> List[Dict[str, Any]]:
        """获取工具调用统计"""
        query = """
        MATCH (s:AgentSession {id: $session_id})-[:HAS_STEP]->(:ExecutionStep)-[:CALLS_TOOL]->(tool:ToolCall)
        RETURN tool.name as tool_name,
               count(*) as call_count,
               avg(tool.durationMs) as avg_duration,
               sum(CASE WHEN tool.status = 'error' THEN 1 ELSE 0 END) as error_count
        ORDER BY call_count DESC
        """
        result = self.db.execute(query, {"session_id": session_id})
        
        stats = []
        while result.has_next():
            row = result.get_next()
            stats.append({
                "tool_name": row[0],
                "call_count": row[1],
                "avg_duration": row[2],
                "error_count": row[3]
            })
        
        return stats
    
    # === Task Operations ===
    
    def create_task_node(self, session_id: str, task_data: dict) -> None:
        """创建任务节点并关联到会话"""
        task_id = f"{session_id}:task_{task_data['id']}"
        
        query = """
        CREATE (t:Task {
            id: $id,
            taskId: $task_id,
            subject: $subject,
            description: $description,
            status: $status,
            owner: $owner,
            createdAt: $created_at
        })
        """
        self.db.execute(query, {
            "id": task_id,
            "task_id": task_data["id"],
            "subject": task_data["subject"],
            "description": task_data.get("description", ""),
            "status": task_data["status"],
            "owner": task_data.get("owner", ""),
            "created_at": datetime.utcnow()
        })
        
        # 创建 HAS_TASK 关系
        query2 = """
        MATCH (s:AgentSession {id: $session_id})
        MATCH (t:Task {id: $task_id})
        CREATE (s)-[:HAS_TASK]->(t)
        """
        self.db.execute(query2, {
            "session_id": session_id,
            "task_id": task_id
        })
    
    def get_sessions(self) -> List[AgentSession]:
        """获取所有会话"""
        query = "MATCH (s:AgentSession) RETURN s ORDER BY s.startedAt DESC"
        result = self.db.execute(query)
        
        sessions = []
        while result.has_next():
            row = result.get_next()
            props = row[0]
            sessions.append(AgentSession(
                id=props["id"],
                name=props["name"],
                workdir=props["workdir"],
                model=props["model"],
                system_prompt=props["systemPrompt"],
                status=SessionStatus(props["status"]),
                started_at=props["startedAt"],
                ended_at=props.get("endedAt"),
                max_tokens=props.get("maxTokens", 8000),
                total_steps=props.get("totalSteps", 0),
                total_tool_calls=props.get("totalToolCalls", 0)
            ))
        
        return sessions
