#!/usr/bin/env python3
"""
agent_s03.py - 待办事项 (TodoWrite)

重构后的面向对象版本。

模型通过 TodoManager 跟踪自己的进度。
一个提醒机制会在模型忘记更新时强制它保持更新。

核心洞察："代理可以跟踪自己的进度 —— 而我能看到它。"
"""

from core import BaseAgent, ToolsMixin, TodoMixin


class S03Agent(TodoMixin, ToolsMixin, BaseAgent):
    """
    待办事项 Agent - 添加任务跟踪能力。
    
    Mixin 顺序：TodoMixin -> ToolsMixin -> BaseAgent
    这样方法解析顺序会先找到 TodoMixin 的工具
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system_prompt = f"""You are a coding agent at {self.workdir}.
Use the todo tool to plan multi-step tasks. Mark in_progress before starting, completed when done.
Prefer tools over prose."""
        # TodoMixin 自动注册 todo 工具并添加提醒机制


if __name__ == "__main__":
    agent = S03Agent()
    agent.interactive_mode("s03 >> ")
