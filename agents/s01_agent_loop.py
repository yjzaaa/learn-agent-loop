#!/usr/bin/env python3
"""
s01_agent_loop.py - 代理循环 (Agent Loop)

AI 编程代理的全部秘诀都包含在这个模式中：

    while stop_reason == "tool_calls":
        response = LLM(messages, tools)
        execute tools
        append results

    +----------+      +-------+      +---------+
    |   User   | ---> |  LLM  | ---> |  Tool   |
    |  prompt  |      |       |      | execute |
    +----------+      +---+---+      +----+----+
                          ^               |
                          |   tool_result |
                          +---------------+
                          (loop continues)

这是核心循环：将工具执行结果反馈给模型，
直到模型决定停止。生产级代理在此基础上
增加了策略、钩子和生命周期控制。
"""

import os
import subprocess
import json

from client import get_client, get_model

client = get_client()
MODEL = get_model()
WORKDIR = os.getcwd()

SYSTEM = f"You are a coding agent at {WORKDIR}. Use bash to solve tasks. Act, don't explain."

# OpenAI/DeepSeek 工具格式
tools = [{
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a shell command.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
}]


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


# -- 核心模式：一个 while 循环，持续调用工具直到模型停止 --
def agent_loop(messages: list):
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}] + messages,
            tools=tools,
            max_tokens=8000,
        )
        
        # 获取助手的消息
        assistant_message = response.choices[0].message
        
        # 添加助手回复到历史
        messages.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls] if assistant_message.tool_calls else None
        })
        
        # 如果模型没有调用工具，则结束
        if response.choices[0].finish_reason != "tool_calls":
            return
        
        # 执行每个工具调用，收集结果
        tool_results = []
        for tool_call in assistant_message.tool_calls:
            if tool_call.function.name == "bash":
                args = json.loads(tool_call.function.arguments)
                print(f"\033[33m$ {args['command']}\033[0m")
                output = run_bash(args["command"])
                print(output[:200])
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": output
                })
        
        messages.extend(tool_results)


if __name__ == "__main__":
    history = []
    while True:
        try:
            query = input("\033[36ms01 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        # 打印最后的回复
        if history[-1]["role"] == "assistant":
            content = history[-1].get("content", "")
            if content:
                print(content)
        print()
