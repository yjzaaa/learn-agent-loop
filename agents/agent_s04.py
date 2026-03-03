#!/usr/bin/env python3
"""
agent_s04.py - 子代理 (Subagents)

重构后的面向对象版本。

子代理在自己的上下文中工作，共享文件系统，
然后只向父代理返回摘要。

核心洞察："进程隔离天然带来上下文隔离。"
"""

from core import BaseAgent, ToolsMixin, SubagentMixin


class S04Agent(SubagentMixin, ToolsMixin, BaseAgent):
    """
    子代理 Agent - 添加任务分发能力。
    
    特性：
    - 子代理拥有全新上下文
    - 子代理只能使用受限工具（无 task 工具）
    - 子代理完成后返回摘要，上下文被丢弃
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system_prompt = f"""You are a coding agent at {self.workdir}.
Use the task tool to delegate exploration or subtasks."""
        self._subagent_system = f"""You are a coding subagent at {self.workdir}.
Complete the given task, then summarize your findings."""
        # SubagentMixin 自动注册 task 工具


if __name__ == "__main__":
    agent = S04Agent()
    agent.interactive_mode("s04 >> ")
