#!/usr/bin/env python3
"""
混入类 - 提供各种 Agent 功能的模块化组件

每个混入类专注于特定功能领域，可以被组合使用。
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
from typing import Optional

from .client import get_client, get_model


# === 基础工具混入 ===

class ToolsMixin(ABC):
    """
    提供基础文件和 shell 操作工具。
    
    包含工具：
    - bash: 执行 shell 命令
    - read_file: 读取文件
    - write_file: 写入文件
    - edit_file: 编辑文件
    """
    
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
        """执行 shell 命令，带有安全检查"""
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
        """读取文件内容"""
        try:
            fp = self.safe_path(path)
            lines = fp.read_text().splitlines()
            if limit and limit < len(lines):
                lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
            return "\n".join(lines)[:self.OUTPUT_LIMIT]
        except Exception as e:
            return f"Error: {e}"
    
    def run_write(self, path: str, content: str) -> str:
        """写入文件内容"""
        try:
            fp = self.safe_path(path)
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content)
            return f"Wrote {len(content)} bytes to {path}"
        except Exception as e:
            return f"Error: {e}"
    
    def run_edit(self, path: str, old_text: str, new_text: str) -> str:
        """编辑文件中的文本"""
        try:
            fp = self.safe_path(path)
            content = fp.read_text()
            if old_text not in content:
                return f"Error: Text not found in {path}"
            fp.write_text(content.replace(old_text, new_text, 1))
            return f"Edited {path}"
        except Exception as e:
            return f"Error: {e}"


# === Todo 管理混入 ===

class TodoMixin(ABC):
    """
    提供待办事项管理功能。
    
    包含工具：
    - todo: 更新待办事项列表
    
    特性：
    - 自动提醒机制（3轮未更新则提醒）
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._todo_items: list[dict] = []
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
    
    def update_todos(self, items: list) -> str:
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
        return self._render_todos()
    
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
    
    def post_loop_hook(self, messages: list) -> None:
        """添加待办提醒逻辑"""
        super().post_loop_hook(messages)
        
        # 更新计数器
        used_todo = self._last_tool_was_todo
        self._last_tool_was_todo = False
        
        self._rounds_since_todo = 0 if used_todo else self._rounds_since_todo + 1
        
        # 添加提醒
        if self._has_open_todos() and self._rounds_since_todo >= 3:
            if messages and messages[-1]["role"] == "user":
                content = messages[-1].get("content", [])
                if isinstance(content, list):
                    content.insert(0, {
                        "role": "tool",
                        "tool_call_id": "reminder",
                        "content": "<reminder>Update your todos.</reminder>"
                    })


# === 任务系统混入 ===

class TaskMixin(ABC):
    """
    提供持久化任务管理功能。
    
    任务以 JSON 文件形式存储在 .tasks/ 目录中。
    
    包含工具：
    - task_create: 创建任务
    - task_update: 更新任务
    - task_list: 列出所有任务
    - task_get: 获取任务详情
    """
    
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


# === 技能加载混入 ===

class SkillMixin(ABC):
    """
    提供技能加载功能。
    
    技能从 skills/<name>/SKILL.md 加载，包含 YAML 前言和正文。
    
    包含工具：
    - load_skill: 加载指定技能的内容
    """
    
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
        """获取技能描述列表（用于系统提示词）"""
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


# === 上下文压缩混入 ===

class CompressionMixin(ABC):
    """
    提供上下文压缩功能，使 Agent 可以永久工作。
    
    包含工具：
    - compact: 手动触发压缩
    
    自动压缩：
    - micro_compact: 静默压缩旧工具结果
    - auto_compact: 当 token 超过阈值时自动总结
    """
    
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
        
        # 第1层：micro_compact
        self._micro_compact(messages)
        
        # 第2层：auto_compact
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
        
        # 构建 tool_call_id -> tool_name 映射
        tool_name_map = {}
        for msg in messages:
            if msg["role"] == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    if isinstance(tc, dict) and tc.get("id"):
                        tool_name_map[tc["id"]] = tc.get("function", {}).get("name", "unknown")
        
        # 清除旧结果
        for _, _, result in tool_results[:-self.KEEP_RECENT]:
            if isinstance(result.get("content"), str) and len(result["content"]) > 100:
                tool_id = result.get("tool_call_id", "")
                tool_name = tool_name_map.get(tool_id, "unknown")
                result["content"] = f"[Previous: used {tool_name}]"
    
    def _auto_compact(self, messages: list) -> list:
        """自动压缩：保存记录并总结"""
        # 保存完整记录
        transcript_path = self._transcript_dir / f"transcript_{int(time.time())}.jsonl"
        with open(transcript_path, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg, default=str) + "\n")
        print(f"[transcript saved: {transcript_path}]")
        
        # 请求 LLM 总结
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
        
        # 替换为总结
        return [
            {"role": "user", "content": f"[Conversation compressed. Transcript: {transcript_path}]\n\n{summary}"},
            {"role": "assistant", "content": "Understood. I have the context from the summary. Continuing."},
        ]


# === 后台任务混入 ===

class BackgroundMixin(ABC):
    """
    提供后台任务执行功能。
    
    包含工具：
    - background_run: 在后台运行命令
    - check_background: 检查后台任务状态
    """
    
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


# === 子代理混入 ===

class SubagentMixin(ABC):
    """
    提供子代理功能。
    
    包含工具：
    - task: 启动子代理执行任务
    
    子代理在一个独立的上下文中运行，仅返回摘要。
    """
    
    SUBAGENT_MAX_ROUNDS = 30
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subagent_system = f"You are a coding subagent at {self.workdir}. Complete the given task, then summarize your findings."
    
    def _init_tools(self) -> None:
        """注册子代理工具"""
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
        """运行子代理"""
        # 子代理的基础工具
        sub_tools = [
            {"type": "function", "function": {"name": "bash", "description": "Run command",
             "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
            {"type": "function", "function": {"name": "read_file", "description": "Read file",
             "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        ]
        
        if agent_type != "Explore":
            sub_tools.extend([
                {"type": "function", "function": {"name": "write_file", "description": "Write file",
                 "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
                {"type": "function", "function": {"name": "edit_file", "description": "Edit file",
                 "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}}},
            ])
        
        # 子代理工具处理器
        sub_handlers = {
            "bash": lambda **kw: self.run_bash(kw["command"]),
            "read_file": lambda **kw: self.run_read(kw["path"]),
        }
        
        if agent_type != "Explore":
            sub_handlers["write_file"] = lambda **kw: self.run_write(kw["path"], kw["content"])
            sub_handlers["edit_file"] = lambda **kw: self.run_edit(kw["path"], kw["old_text"], kw["new_text"])
        
        # 子代理循环
        sub_messages = [{"role": "user", "content": prompt}]
        
        for _ in range(self.SUBAGENT_MAX_ROUNDS):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self._subagent_system}] + sub_messages,
                tools=sub_tools,
                max_tokens=self.max_tokens,
            )
            
            assistant_message = response.choices[0].message
            sub_messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls] if assistant_message.tool_calls else None
            })
            
            if response.choices[0].finish_reason != "tool_calls":
                break
            
            results = []
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    handler = sub_handlers.get(tool_call.function.name, lambda **kw: "Unknown tool")
                    args = json.loads(tool_call.function.arguments)
                    output = handler(**args)
                    results.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(output)[:50000]
                    })
            sub_messages.append({"role": "user", "content": results})
        
        return assistant_message.content or "(no summary)"


# === 团队协作混入 ===

class TeamMixin(ABC):
    """
    提供团队协作功能。
    
    包含工具：
    - spawn_teammate: 创建队友
    - list_teammates: 列出队友
    - send_message: 发送消息
    - read_inbox: 读取收件箱
    - broadcast: 广播消息
    """
    
    VALID_MSG_TYPES = {
        "message", "broadcast", "shutdown_request",
        "shutdown_response", "plan_approval_response"
    }
    
    def __init__(self, *args, team_dir: Optional[Path] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._team_dir = team_dir or (self.workdir / ".team")
        self._inbox_dir = self._team_dir / "inbox"
        self._inbox_dir.mkdir(parents=True, exist_ok=True)
        self._team_config_path = self._team_dir / "config.json"
        self._team_config = self._load_team_config()
        self._team_threads: dict[str, threading.Thread] = {}
    
    def _init_tools(self) -> None:
        """注册团队工具"""
        super()._init_tools()
        self.register_tool(
            name="spawn_teammate",
            handler=self.spawn_teammate,
            description="Spawn a persistent teammate that runs in its own thread.",
            parameters={
                "name": {"type": "string"},
                "role": {"type": "string"},
                "prompt": {"type": "string"}
            },
            required=["name", "role", "prompt"]
        )
        self.register_tool(
            name="list_teammates",
            handler=self.list_teammates,
            description="List all teammates with name, role, status.",
            parameters={},
            required=[]
        )
        self.register_tool(
            name="send_message",
            handler=self.send_message,
            description="Send a message to a teammate's inbox.",
            parameters={
                "to": {"type": "string"},
                "content": {"type": "string"},
                "msg_type": {"type": "string", "enum": list(self.VALID_MSG_TYPES)}
            },
            required=["to", "content"]
        )
        self.register_tool(
            name="read_inbox",
            handler=self.read_inbox,
            description="Read and drain the inbox.",
            parameters={},
            required=[]
        )
        self.register_tool(
            name="broadcast",
            handler=self.broadcast,
            description="Send a message to all teammates.",
            parameters={"content": {"type": "string"}},
            required=["content"]
        )
    
    def _load_team_config(self) -> dict:
        """加载团队配置"""
        if self._team_config_path.exists():
            return json.loads(self._team_config_path.read_text())
        return {"team_name": "default", "members": []}
    
    def _save_team_config(self) -> None:
        """保存团队配置"""
        self._team_config_path.write_text(json.dumps(self._team_config, indent=2))
    
    def spawn_teammate(self, name: str, role: str, prompt: str) -> str:
        """创建队友"""
        member = self._find_member(name)
        if member:
            if member["status"] not in ("idle", "shutdown"):
                return f"Error: '{name}' is currently {member['status']}"
            member["status"] = "working"
            member["role"] = role
        else:
            member = {"name": name, "role": role, "status": "working"}
            self._team_config["members"].append(member)
        
        self._save_team_config()
        
        thread = threading.Thread(
            target=self._teammate_loop,
            args=(name, role, prompt),
            daemon=True
        )
        self._team_threads[name] = thread
        thread.start()
        
        return f"Spawned '{name}' (role: {role})"
    
    def _find_member(self, name: str) -> Optional[dict]:
        """查找成员"""
        for m in self._team_config["members"]:
            if m["name"] == name:
                return m
        return None
    
    def _teammate_loop(self, name: str, role: str, prompt: str) -> None:
        """队友主循环（简化版）"""
        sys_prompt = f"You are '{name}', role: {role}, at {self.workdir}. Use send_message to communicate."
        messages = [{"role": "user", "content": prompt}]
        
        teammate_tools = [
            {"type": "function", "function": {"name": "bash", "description": "Run command",
             "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
            {"type": "function", "function": {"name": "read_file", "description": "Read file",
             "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
            {"type": "function", "function": {"name": "send_message", "description": "Send message",
             "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "content": {"type": "string"}}, "required": ["to", "content"]}}},
            {"type": "function", "function": {"name": "read_inbox", "description": "Read inbox",
             "parameters": {"type": "object", "properties": {}}}},
        ]
        
        for _ in range(50):
            # 检查收件箱
            inbox = self._read_inbox(name)
            for msg in inbox:
                messages.append({"role": "user", "content": json.dumps(msg)})
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": sys_prompt}] + messages,
                    tools=teammate_tools,
                    max_tokens=self.max_tokens,
                )
            except Exception:
                break
            
            assistant_message = response.choices[0].message
            messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls] if assistant_message.tool_calls else None
            })
            
            if response.choices[0].finish_reason != "tool_calls":
                break
            
            results = []
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    if tool_call.function.name == "send_message":
                        output = self.send_message(args["to"], args["content"])
                    elif tool_call.function.name == "read_inbox":
                        output = json.dumps(self._read_inbox(name), indent=2)
                    elif tool_call.function.name == "bash":
                        output = self.run_bash(args["command"])
                    elif tool_call.function.name == "read_file":
                        output = self.run_read(args["path"])
                    else:
                        output = "Unknown tool"
                    
                    print(f"  [{name}] {tool_call.function.name}: {str(output)[:120]}")
                    results.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(output)
                    })
            messages.append({"role": "user", "content": results})
        
        member = self._find_member(name)
        if member and member["status"] != "shutdown":
            member["status"] = "idle"
            self._save_team_config()
    
    def list_teammates(self) -> str:
        """列出所有队友"""
        if not self._team_config["members"]:
            return "No teammates."
        
        lines = [f"Team: {self._team_config['team_name']}"]
        for m in self._team_config["members"]:
            lines.append(f"  {m['name']} ({m['role']}): {m['status']}")
        return "\n".join(lines)
    
    def send_message(self, to: str, content: str, msg_type: str = "message") -> str:
        """发送消息"""
        if msg_type not in self.VALID_MSG_TYPES:
            return f"Error: Invalid type '{msg_type}'"
        
        msg = {
            "type": msg_type,
            "from": "lead",
            "content": content,
            "timestamp": time.time(),
        }
        
        inbox_path = self._inbox_dir / f"{to}.jsonl"
        with open(inbox_path, "a") as f:
            f.write(json.dumps(msg) + "\n")
        
        return f"Sent {msg_type} to {to}"
    
    def _read_inbox(self, name: str) -> list:
        """读取收件箱（内部方法）"""
        inbox_path = self._inbox_dir / f"{name}.jsonl"
        if not inbox_path.exists():
            return []
        
        content = inbox_path.read_text().strip()
        messages = [json.loads(line) for line in content.splitlines() if line]
        inbox_path.write_text("")
        return messages
    
    def read_inbox(self) -> str:
        """读取收件箱（工具方法）"""
        return json.dumps(self._read_inbox("lead"), indent=2)
    
    def broadcast(self, content: str) -> str:
        """广播消息"""
        count = 0
        for member in self._team_config["members"]:
            if member["name"] != "lead":
                self.send_message(member["name"], content, "broadcast")
                count += 1
        return f"Broadcast to {count} teammates"
    
    def pre_loop_hook(self, messages: list) -> None:
        """注入收件箱消息"""
        super().pre_loop_hook(messages)
        
        inbox = self._read_inbox("lead")
        if inbox:
            messages.append({
                "role": "user",
                "content": f"<inbox>{json.dumps(inbox, indent=2)}</inbox>"
            })
            messages.append({
                "role": "assistant",
                "content": "Noted inbox messages."
            })
