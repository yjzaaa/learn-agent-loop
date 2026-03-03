#!/usr/bin/env python3
"""
agent_s08.py - 后台任务 (Background Tasks)

重构后的面向对象版本。

在后台线程中运行命令，不阻塞主 Agent 循环。
通知队列在每个 LLM 调用之前被清空以传递结果。

核心洞察："即发即弃 —— agent 在命令运行时不会阻塞。"
"""

from core import BaseAgent, ToolsMixin, BackgroundMixin


class S08Agent(BackgroundMixin, ToolsMixin, BaseAgent):
    """
    后台任务 Agent - 添加异步执行能力。
    
    长时间运行的命令可以在后台执行，主循环继续处理其他任务。
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system_prompt = f"""You are a coding agent at {self.workdir}.
Use background_run for long-running commands.
Check status with check_background."""
        # BackgroundMixin 自动：
        # 1. 注册 background_run 和 check_background 工具
        # 2. 在 pre_loop_hook 中注入完成的后台任务通知


if __name__ == "__main__":
    agent = S08Agent()
    agent.interactive_mode("s08 >> ")
