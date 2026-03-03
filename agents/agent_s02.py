#!/usr/bin/env python3
"""
agent_s02.py - 工具扩展 (Tools)

重构后的面向对象版本。

在基础循环上添加文件操作工具：
- read_file: 读取文件内容
- write_file: 写入文件
- edit_file: 编辑文件

核心洞察："循环没变，只是添加了工具。"
"""

from core import BaseAgent, ToolsMixin


class S02Agent(ToolsMixin, BaseAgent):
    """
    工具扩展 Agent - 添加文件操作能力。
    
    继承 ToolsMixin 获得所有基础工具：
    - bash
    - read_file
    - write_file
    - edit_file
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system_prompt = f"""You are a coding agent at {self.workdir}.
Use tools to solve tasks. Act, don't explain."""
        # ToolsMixin 自动注册所有基础工具


if __name__ == "__main__":
    agent = S02Agent()
    agent.interactive_mode("s02 >> ")
