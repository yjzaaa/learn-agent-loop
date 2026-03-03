#!/usr/bin/env python3
"""
agent_s07.py - 任务系统 (Tasks)

重构后的面向对象版本。

任务以 JSON 文件形式持久化存储，因此它们能在上下文压缩后依然存在。
每个任务都有一个依赖图（blockedBy/blocks）。

核心洞察："状态在压缩后依然保留 —— 因为它在对话之外。"
"""

from core import BaseAgent, ToolsMixin, TaskMixin


class S07Agent(TaskMixin, ToolsMixin, BaseAgent):
    """
    任务系统 Agent - 添加持久化任务管理能力。
    
    任务存储在 .tasks/ 目录的 JSON 文件中，支持依赖关系。
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system_prompt = f"""You are a coding agent at {self.workdir}.
Use task tools to plan and track work across multiple steps.
Tasks persist across context compressions."""
        # TaskMixin 自动注册：
        # - task_create
        # - task_update
        # - task_list
        # - task_get


if __name__ == "__main__":
    agent = S07Agent()
    agent.interactive_mode("s07 >> ")
