#!/usr/bin/env python3
"""
s04_subagent.py - 子代理（Subagents）

生成一个消息列表为空的子代理。子代理在自己的上下文中工作，
共享文件系统，然后只向父代理返回摘要。

    父代理                         子代理
    +------------------+             +------------------+
    | messages=[...]   |             | messages=[]      |  <-- 全新的
    |                  |  分发       |                  |
    | tool: task       | ---------->| while tool_use:  |
    |   prompt="..."   |            |   调用工具       |
    |   description="" |            |   追加结果       |
    |                  |  摘要       |                  |
    |   result = "..." | <--------- | 返回最后文本     |
    +------------------+             +------------------+
              |
    父代理上下文保持干净。
    子代理上下文被丢弃。

核心洞察："进程隔离天然带来上下文隔离。"
"""

import json
import os
import subprocess
from pathlib import Path

from client import get_client, get_model

WORKDIR = Path.cwd()
client = get_client()
MODEL = get_model()

SYSTEM = f"You are a coding agent at {WORKDIR}. Use the task tool to delegate exploration or subtasks."
SUBAGENT_SYSTEM = f"You are a coding subagent at {WORKDIR}. Complete the given task, then summarize your findings."


# -- 父代理和子代理共享的工具实现 --
def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path

def run_bash(command: str) -> str:
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(command, shell=True, cwd=WORKDIR,
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"

def run_read(path: str, limit: int = None) -> str:
    try:
        lines = safe_path(path).read_text().splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
        return "\n".join(lines)[:50000]
    except Exception as e:
        return f"Error: {e}"

def run_write(path: str, content: str) -> str:
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        return f"Wrote {len(content)} bytes"
    except Exception as e:
        return f"Error: {e}"

def run_edit(path: str, old_text: str, new_text: str) -> str:
    try:
        fp = safe_path(path)
        content = fp.read_text()
        if old_text not in content:
            return f"Error: Text not found in {path}"
        fp.write_text(content.replace(old_text, new_text, 1))
        return f"Edited {path}"
    except Exception as e:
        return f"Error: {e}"


TOOL_HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
}

# 子代理获取所有基础工具，除了 task（不允许递归生成）
CHILD_TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run a shell command.",
     "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read file contents.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write content to file.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Replace exact text in file.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}}},
]


# -- 子代理：全新的上下文，过滤的工具，仅返回摘要 --
def run_subagent(prompt: str) -> str:
    sub_messages = [{"role": "user", "content": prompt}]  # 全新的上下文
    for _ in range(30):  # 安全限制
        response = client.chat.completions.create(
            model=MODEL, messages=[{"role": "system", "content": SUBAGENT_SYSTEM}] + sub_messages,
            tools=CHILD_TOOLS, max_tokens=8000,
        )
        assistant_message = response.choices[0].message
        messages.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls] if assistant_message.tool_calls else None
        })
        if response.choices[0].finish_reason != "tool_calls":
            break
        results = []
        for tool_call in assistant_message.tool_calls:
            handler = TOOL_HANDLERS.get(tool_call.function.name)
            tool_input = json.loads(tool_call.function.arguments)
            output = handler(**tool_input) if handler else f"Unknown tool: {tool_call.function.name}"
            results.append({"role": "tool", "tool_call_id": tool_call.id, "content": str(output)[:50000]})
        sub_messages.append({"role": "user", "content": results})
    # 只有最终文本返回给父代理 -- 子代理上下文被丢弃
    return assistant_message.content or "(no summary)"


# -- 父代理工具：基础工具 + 任务分发器 --
PARENT_TOOLS = CHILD_TOOLS + [
    {"type": "function", "function": {"name": "task", "description": "Spawn a subagent with fresh context. It shares the filesystem but not conversation history.",
     "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}, "description": {"type": "string", "description": "Short description of the task"}}, "required": ["prompt"]}}},
]


def agent_loop(messages: list):
    while True:
        response = client.chat.completions.create(
            model=MODEL, messages=[{"role": "system", "content": SYSTEM}] + messages,
            tools=PARENT_TOOLS, max_tokens=8000,
        )
        assistant_message = response.choices[0].message
        messages.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls] if assistant_message.tool_calls else None
        })
        if response.choices[0].finish_reason != "tool_calls":
            return
        results = []
        for tool_call in assistant_message.tool_calls:
            tool_input = json.loads(tool_call.function.arguments)
            if tool_call.function.name == "task":
                desc = tool_input.get("description", "subtask")
                print(f"> task ({desc}): {tool_input['prompt'][:80]}")
                output = run_subagent(tool_input["prompt"])
            else:
                handler = TOOL_HANDLERS.get(tool_call.function.name)
                output = handler(**tool_input) if handler else f"Unknown tool: {tool_call.function.name}"
            print(f"  {str(output)[:200]}")
            results.append({"role": "tool", "tool_call_id": tool_call.id, "content": str(output)})
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    history = []
    while True:
        try:
            query = input("\033[36ms04 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        response_content = history[-1]["content"]
        if isinstance(response_content, str):
            print(response_content)
        print()
