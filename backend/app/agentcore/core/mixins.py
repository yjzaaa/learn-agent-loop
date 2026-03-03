"""
Mixin Classes

提供各种 Agent 功能的模块化组件（图谱感知版本）
"""

import json
import os
import re
import subprocess
import threading
import time
import uuid
from abc import ABC
from pathlib import Path
from queue import Queue
from typing import Optional, List

from .client import get_client, get_model
from ..graph.repository import GraphRepository
from ..graph.models import (
    TaskStatus, TodoStatus, TeammateStatus,
    BackgroundJobStatus, CompressionType
)


class ToolsMixin(ABC):
    """提供基础文件和 shell 操作工具"""
    
    DANGEROUS_COMMANDS = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    OUTPUT_LIMIT = 50000
    TIMEOUT = 120
    
    def _init_tools(self) -> None:
        """注册基础工具"""
        super()._init_tools()
        self.register_tool(
            name="bash",
            handler=self.run_bash,
            description="Run a shell command.",
            parameters={"command": {"type": "string"}},
            required=["command"]
        )
        self.register_tool(
            name="read_file",
            handler=self.run_read,
            description="Read file contents.",
            parameters={
                "path": {"type": "string"},
                "limit": {"type": "integer"}
            },
            required=["path"]
        )
        self.register_tool(
            name="write_file",
            handler=self.run_write,
            description="Write content to file.",
            parameters={
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            required=["path", "content"]
        )
        self.register_tool(
            name="edit_file",
            handler=self.run_edit,
            description="Replace exact text in file.",
            parameters={
                "path": {"type": "string"},
                "old_text": {"type": "string"},
                "new_text": {"type": "string"}
            },
            required=["path", "old_text", "new_text"]
        )
    
    def run_bash(self, command: str) -> str:
        """执行 shell 命令"""
        if any(d in command for d in self.DANGEROUS_COMMANDS):
            return "Error: Dangerous command blocked"
        
        try:
            result = subprocess.run(
                command, shell=True, cwd=self.workdir,
                capture_output=True, text=True, timeout=self.TIMEOUT
            )
            output = (result.stdout + result.stderr).strip()
            return output[:self.OUTPUT_LIMIT] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return f"Error: Timeout ({self.TIMEOUT}s)"
    
    def run_read(self, path: str, limit: Optional[int] = None) -> str:
        """读取文件"""
        try:
            fp = self.safe_path(path)
            lines = fp.read_text().splitlines()
            if limit and limit < len(lines):
                lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
            return "\n".join(lines)[:self.OUTPUT_LIMIT]
        except Exception as e:
            return f"Error: {e}"
    
    def run_write(self, path: str, content: str) -> str:
        """写入文件"""
        try:
            fp = self.safe_path(path)
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content)
            return f"Wrote {len(content)} bytes to {path}"
        except Exception as e:
            return f"Error: {e}"
    
    def run_edit(self, path: str, old_text: str, new_text: str) -> str:
        """编辑文件"""
        try:
            fp = self.safe_path(path)
            content = fp.read_text()
            if old_text not in content:
                return f"Error: Text not found in {path}"
            fp.write_text(content.replace(old_text, new_text, 1))
            return f"Edited {path}"
        except Exception as e:
            return f"Error: {e}"


class TodoMixin(ABC):
    """提供待办事项管理功能"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._todo_items: List[dict] = []
        self._rounds_since_todo = 0
        self._last_tool_was_todo = False
    
    def _init_tools(self) -> None:
        """注册待办事项工具"""
        super()._init_tools()
        self.register_tool(
            name="todo",
            handler=self.update_todos,
            description="Update task list. Track progress on multi-step tasks.",
            parameters={
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "text": {"type": "string"},
                            "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]}
                        },
                        "required": ["id", "text", "status"]
                    }
                }
            },
            required=["items"]
        )
    
    def update_todos(self, items: List[dict]) -> str:
        """更新待办事项列表"""
        if len(items) > 20:
            raise ValueError("Max 20 todos allowed")
        
        validated = []
        in_progress_count = 0
        
        for i, item in enumerate(items):
            text = str(item.get("text", "")).strip()
            status = str(item.get("status", "pending")).lower()
            item_id = str(item.get("id", str(i + 1)))
            
            if not text:
                raise ValueError(f"Item {item_id}: text required")
            if status not in ("pending", "in_progress", "completed"):
                raise ValueError(f"Item {item_id}: invalid status '{status}'")
            if status == "in_progress":
                in_progress_count += 1
            
            validated.append({"id": item_id, "text": text, "status": status})
        
        if in_progress_count > 1:
            raise ValueError("Only one task can be in_progress at a time")
        
        self._todo_items = validated
        self._last_tool_was_todo = True
        
        # 如果有 graph_repo，同步到图谱
        if hasattr(self, 'graph_repo') and hasattr(self, 'session_id'):
            self._sync_todos_to_graph()
        
        return self._render_todos()
    
    def _sync_todos_to_graph(self):
        """同步待办事项到图谱"""
        # 这里可以实现将 todo 写入图谱的逻辑
        pass
    
    def _render_todos(self) -> str:
        """渲染待办事项列表"""
        if not self._todo_items:
            return "No todos."
        
        markers = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}
        lines = [f"{markers[item['status']]} #{item['id']}: {item['text']}" 
                 for item in self._todo_items]
        
        done = sum(1 for t in self._todo_items if t["status"] == "completed")
        lines.append(f"\n({done}/{len(self._todo_items)} completed)")
        
        return "\n".join(lines)
    
    def _has_open_todos(self) -> bool:
        """检查是否有未完成的待办事项"""
        return any(item.get("status") != "completed" for item in self._todo_items)
    
    def post_loop_hook(self, messages: List[dict]) -> None:
        """添加待办提醒逻辑"""
        super().post_loop_hook(messages)
        
        used_todo = self._last_tool_was_todo
        self._last_tool_was_todo = False
        self._rounds_since_todo = 0 if used_todo else self._rounds_since_todo + 1
        
        if self._has_open_todos() and self._rounds_since_todo >= 3:
            if messages and messages[-1]["role"] == "user":
                content = messages[-1].get("content", [])
                if isinstance(content, list):
                    content.insert(0, {
                        "role": "tool",
                        "tool_call_id": "reminder",
                        "content": "<reminder>Update your todos.</reminder>"
                    })


class TaskMixin(ABC):
    """提供持久化任务管理功能"""
    
    def __init__(self, *args, tasks_dir: Optional[Path] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._tasks_dir = tasks_dir or (self.workdir / ".tasks")
        self._tasks_dir.mkdir(exist_ok=True)
        self._next_task_id = self._calculate_next_id()
    
    def _init_tools(self) -> None:
        """注册任务管理工具"""
        super()._init_tools()
        self.register_tool(
            name="task_create",
            handler=self.task_create,
            description="Create a new task.",
            parameters={
                "subject": {"type": "string"},
                "description": {"type": "string"}
            },
            required=["subject"]
        )
        self.register_tool(
            name="task_update",
            handler=self.task_update,
            description="Update a task's status or dependencies.",
            parameters={
                "task_id": {"type": "integer"},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                "addBlockedBy": {"type": "array", "items": {"type": "integer"}},
                "addBlocks": {"type": "array", "items": {"type": "integer"}}
            },
            required=["task_id"]
        )
        self.register_tool(
            name="task_list",
            handler=self.task_list,
            description="List all tasks with status summary.",
            parameters={},
            required=[]
        )
        self.register_tool(
            name="task_get",
            handler=self.task_get,
            description="Get full details of a task by ID.",
            parameters={"task_id": {"type": "integer"}},
            required=["task_id"]
        )
    
    def _calculate_next_id(self) -> int:
        """计算下一个任务 ID"""
        ids = [int(f.stem.split("_")[1]) for f in self._tasks_dir.glob("task_*.json")]
        return max(ids) + 1 if ids else 1
    
    def _load_task(self, task_id: int) -> dict:
        """加载任务"""
        path = self._tasks_dir / f"task_{task_id}.json"
        if not path.exists():
            raise ValueError(f"Task {task_id} not found")
        return json.loads(path.read_text())
    
    def _save_task(self, task: dict) -> None:
        """保存任务"""
        path = self._tasks_dir / f"task_{task['id']}.json"
        path.write_text(json.dumps(task, indent=2))
    
    def task_create(self, subject: str, description: str = "") -> str:
        """创建新任务"""
        task = {
            "id": self._next_task_id,
            "subject": subject,
            "description": description,
            "status": "pending",
            "blockedBy": [],
            "blocks": [],
            "owner": ""
        }
        self._save_task(task)
        self._next_task_id += 1
        
        # 同步到图谱
        if hasattr(self, 'graph_repo') and hasattr(self, 'session_id'):
            self.graph_repo.create_task_node(self.session_id, task)
        
        return json.dumps(task, indent=2)
    
    def task_update(self, task_id: int, status: Optional[str] = None,
                    addBlockedBy: Optional[list] = None, 
                    addBlocks: Optional[list] = None) -> str:
        """更新任务"""
        task = self._load_task(task_id)
        
        if status:
            if status not in ("pending", "in_progress", "completed"):
                raise ValueError(f"Invalid status: {status}")
            task["status"] = status
            if status == "completed":
                self._clear_dependency(task_id)
        
        if addBlockedBy:
            task["blockedBy"] = list(set(task["blockedBy"] + addBlockedBy))
        
        if addBlocks:
            task["blocks"] = list(set(task["blocks"] + addBlocks))
            for blocked_id in addBlocks:
                try:
                    blocked = self._load_task(blocked_id)
                    if task_id not in blocked["blockedBy"]:
                        blocked["blockedBy"].append(task_id)
                        self._save_task(blocked)
                except ValueError:
                    pass
        
        self._save_task(task)
        return json.dumps(task, indent=2)
    
    def _clear_dependency(self, completed_id: int) -> None:
        """清除已完成任务的依赖关系"""
        for f in self._tasks_dir.glob("task_*.json"):
            task = json.loads(f.read_text())
            if completed_id in task.get("blockedBy", []):
                task["blockedBy"].remove(completed_id)
                self._save_task(task)
    
    def task_list(self) -> str:
        """列出所有任务"""
        tasks = []
        for f in sorted(self._tasks_dir.glob("task_*.json")):
            tasks.append(json.loads(f.read_text()))
        
        if not tasks:
            return "No tasks."
        
        markers = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}
        lines = []
        for t in tasks:
            marker = markers.get(t["status"], "[?]")
            blocked = f" (blocked by: {t['blockedBy']})" if t.get("blockedBy") else ""
            lines.append(f"{marker} #{t['id']}: {t['subject']}{blocked}")
        
        return "\n".join(lines)
    
    def task_get(self, task_id: int) -> str:
        """获取任务详情"""
        return json.dumps(self._load_task(task_id), indent=2)


class SkillMixin(ABC):
    """提供技能加载功能"""
    
    def __init__(self, *args, skills_dir: Optional[Path] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._skills_dir = skills_dir or (self.workdir / "skills")
        self._skills: dict[str, dict] = {}
        self._load_skills()
    
    def _init_tools(self) -> None:
        """注册技能加载工具"""
        super()._init_tools()
        self.register_tool(
            name="load_skill",
            handler=self.load_skill,
            description="Load specialized knowledge by name.",
            parameters={"name": {"type": "string", "description": "Skill name to load"}},
            required=["name"]
        )
    
    def _load_skills(self) -> None:
        """加载所有技能"""
        if not self._skills_dir.exists():
            return
        
        for f in sorted(self._skills_dir.rglob("SKILL.md")):
            text = f.read_text()
            meta, body = self._parse_frontmatter(text)
            name = meta.get("name", f.parent.name)
            self._skills[name] = {"meta": meta, "body": body, "path": str(f)}
    
    def _parse_frontmatter(self, text: str) -> tuple[dict, str]:
        """解析 YAML 前言"""
        match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
        if not match:
            return {}, text
        
        meta = {}
        for line in match.group(1).strip().splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip()
        
        return meta, match.group(2).strip()
    
    def load_skill(self, name: str) -> str:
        """加载技能内容"""
        skill = self._skills.get(name)
        if not skill:
            available = ", ".join(self._skills.keys())
            return f"Error: Unknown skill '{name}'. Available: {available}"
        return f"<skill name=\"{name}\">\n{skill['body']}\n</skill>"
    
    def get_skill_descriptions(self) -> str:
        """获取技能描述列表"""
        if not self._skills:
            return "(no skills available)"
        
        lines = []
        for name, skill in self._skills.items():
            desc = skill["meta"].get("description", "No description")
            tags = skill["meta"].get("tags", "")
            line = f"  - {name}: {desc}"
            if tags:
                line += f" [{tags}]"
            lines.append(line)
        
        return "\n".join(lines)


class CompressionMixin(ABC):
    """提供上下文压缩功能"""
    
    TOKEN_THRESHOLD = 50000
    KEEP_RECENT = 3
    
    def __init__(self, *args, transcript_dir: Optional[Path] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._transcript_dir = transcript_dir or (self.workdir / ".transcripts")
        self._transcript_dir.mkdir(exist_ok=True)
        self._manual_compact_requested = False
    
    def _init_tools(self) -> None:
        """注册压缩工具"""
        super()._init_tools()
        self.register_tool(
            name="compact",
            handler=self.request_compact,
            description="Trigger manual conversation compression.",
            parameters={"focus": {"type": "string", "description": "What to preserve in the summary"}},
            required=[]
        )
    
    def request_compact(self, focus: str = "") -> str:
        """请求手动压缩"""
        self._manual_compact_requested = True
        return "Compressing..."
    
    @staticmethod
    def estimate_tokens(messages: list) -> int:
        """粗略估计 token 数"""
        return len(str(messages)) // 4
    
    def pre_loop_hook(self, messages: list) -> None:
        """执行压缩检查"""
        super().pre_loop_hook(messages)
        self._micro_compact(messages)
        
        if self.estimate_tokens(messages) > self.TOKEN_THRESHOLD:
            print("[auto_compact triggered]")
            messages[:] = self._auto_compact(messages)
    
    def post_loop_hook(self, messages: list) -> None:
        """处理手动压缩请求"""
        super().post_loop_hook(messages)
        
        if self._manual_compact_requested:
            print("[manual compact]")
            messages[:] = self._auto_compact(messages)
            self._manual_compact_requested = False
    
    def _micro_compact(self, messages: list) -> None:
        """静默压缩旧工具结果"""
        tool_results = []
        for msg_idx, msg in enumerate(messages):
            if msg["role"] == "user" and isinstance(msg.get("content"), list):
                for part_idx, part in enumerate(msg["content"]):
                    if isinstance(part, dict) and part.get("role") == "tool":
                        tool_results.append((msg_idx, part_idx, part))
        
        if len(tool_results) <= self.KEEP_RECENT:
            return
        
        tool_name_map = {}
        for msg in messages:
            if msg["role"] == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    if isinstance(tc, dict) and tc.get("id"):
                        tool_name_map[tc["id"]] = tc.get("function", {}).get("name", "unknown")
        
        for _, _, result in tool_results[:-self.KEEP_RECENT]:
            if isinstance(result.get("content"), str) and len(result["content"]) > 100:
                tool_id = result.get("tool_call_id", "")
                tool_name = tool_name_map.get(tool_id, "unknown")
                result["content"] = f"[Previous: used {tool_name}]"
    
    def _auto_compact(self, messages: list) -> list:
        """自动压缩"""
        transcript_path = self._transcript_dir / f"transcript_{int(time.time())}.jsonl"
        with open(transcript_path, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg, default=str) + "\n")
        print(f"[transcript saved: {transcript_path}]")
        
        conversation_text = json.dumps(messages, default=str)[:80000]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content":
                    "Summarize this conversation for continuity. Include: "
                    "1) What was accomplished, 2) Current state, 3) Key decisions made. "
                    "Be concise but preserve critical details.\n\n" + conversation_text}
            ],
            max_tokens=2000,
        )
        summary = response.choices[0].message.content
        
        return [
            {"role": "user", "content": f"[Conversation compressed. Transcript: {transcript_path}]\n\n{summary}"},
            {"role": "assistant", "content": "Understood. I have the context from the summary. Continuing."},
        ]


class BackgroundMixin(ABC):
    """提供后台任务执行功能"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bg_tasks: dict[str, dict] = {}
        self._bg_notifications: Queue = Queue()
        self._bg_lock = threading.Lock()
    
    def _init_tools(self) -> None:
        """注册后台任务工具"""
        super()._init_tools()
        self.register_tool(
            name="background_run",
            handler=self.bg_run,
            description="Run command in background thread. Returns task_id immediately.",
            parameters={"command": {"type": "string"}},
            required=["command"]
        )
        self.register_tool(
            name="check_background",
            handler=self.bg_check,
            description="Check background task status. Omit task_id to list all.",
            parameters={"task_id": {"type": "string"}},
            required=[]
        )
    
    def bg_run(self, command: str) -> str:
        """启动后台任务"""
        task_id = str(uuid.uuid4())[:8]
        self._bg_tasks[task_id] = {
            "status": "running",
            "result": None,
            "command": command
        }
        
        thread = threading.Thread(
            target=self._bg_execute,
            args=(task_id, command),
            daemon=True
        )
        thread.start()
        
        return f"Background task {task_id} started: {command[:80]}"
    
    def _bg_execute(self, task_id: str, command: str) -> None:
        """后台执行命令"""
        try:
            result = subprocess.run(
                command, shell=True, cwd=self.workdir,
                capture_output=True, text=True, timeout=300
            )
            output = (result.stdout + result.stderr).strip()[:50000]
            status = "completed"
        except subprocess.TimeoutExpired:
            output = "Error: Timeout (300s)"
            status = "timeout"
        except Exception as e:
            output = f"Error: {e}"
            status = "error"
        
        self._bg_tasks[task_id].update({"status": status, "result": output})
        
        with self._bg_lock:
            self._bg_notifications.put({
                "task_id": task_id,
                "status": status,
                "command": command[:80],
                "result": output[:500],
            })
    
    def bg_check(self, task_id: Optional[str] = None) -> str:
        """检查后台任务状态"""
        if task_id:
            task = self._bg_tasks.get(task_id)
            if not task:
                return f"Error: Unknown task {task_id}"
            return f"[{task['status']}] {task['command'][:60]}\n{task.get('result') or '(running)'}"
        
        lines = [f"{tid}: [{t['status']}] {t['command'][:60]}" 
                 for tid, t in self._bg_tasks.items()]
        return "\n".join(lines) if lines else "No background tasks."
    
    def pre_loop_hook(self, messages: list) -> None:
        """注入后台通知"""
        super().pre_loop_hook(messages)
        
        with self._bg_lock:
            notifications = []
            while not self._bg_notifications.empty():
                notifications.append(self._bg_notifications.get_nowait())
        
        if notifications and messages:
            notif_text = "\n".join(
                f"[bg:{n['task_id']}] {n['status']}: {n['result']}" for n in notifications
            )
            messages.append({
                "role": "user",
                "content": f"<background-results>\n{notif_text}\n</background-results>"
            })
            messages.append({
                "role": "assistant",
                "content": "Noted background results."
            })


class TeamMixin(ABC):
    """提供团队协作功能（简化版）"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _init_tools(self) -> None:
        super()._init_tools()
        # 简化版，不实现完整团队功能
        pass


class SubagentMixin(ABC):
    """提供子代理功能（简化版）"""
    
    SUBAGENT_MAX_ROUNDS = 30
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subagent_system = f"You are a coding subagent. Complete the given task, then summarize your findings."
    
    def _init_tools(self) -> None:
        super()._init_tools()
        self.register_tool(
            name="task",
            handler=self.run_subagent,
            description="Spawn a subagent with fresh context for isolated work.",
            parameters={
                "prompt": {"type": "string"},
                "agent_type": {"type": "string", "enum": ["Explore", "general-purpose"]}
            },
            required=["prompt"]
        )
    
    def run_subagent(self, prompt: str, agent_type: str = "Explore") -> str:
        """运行子代理（简化版）"""
        sub_messages = [{"role": "user", "content": prompt}]
        
        for _ in range(self.SUBAGENT_MAX_ROUNDS):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self._subagent_system}] + sub_messages,
                max_tokens=self.max_tokens,
            )
            
            content = response.choices[0].message.content
            sub_messages.append({"role": "assistant", "content": content or ""})
            
            if response.choices[0].finish_reason != "tool_calls":
                break
        
        return content or "(no summary)"
