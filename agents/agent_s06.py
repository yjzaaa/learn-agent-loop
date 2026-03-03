#!/usr/bin/env python3
"""
agent_s06.py - 上下文压缩 (Context Compact)

重构后的面向对象版本。

三层压缩管道，使代理可以永久工作：
1. micro_compact: 静默压缩旧工具结果
2. auto_compact: 当 token 超过阈值时自动总结
3. compact 工具: 手动触发压缩

核心洞察："代理可以有策略地遗忘并永久工作。"
"""

from core import BaseAgent, ToolsMixin, CompressionMixin


class S06Agent(CompressionMixin, ToolsMixin, BaseAgent):
    """
    上下文压缩 Agent - 添加上下文管理能力。
    
    通过三层压缩确保代理可以长期运行而不超出上下文限制。
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system_prompt = f"""You are a coding agent at {self.workdir}.
Use tools to solve tasks.
The system will automatically compress context when needed."""
        # CompressionMixin 自动：
        # 1. 注册 compact 工具
        # 2. 在 pre_loop_hook 中执行 micro_compact 和 auto_compact
        # 3. 在 post_loop_hook 中处理手动压缩请求


if __name__ == "__main__":
    agent = S06Agent()
    agent.interactive_mode("s06 >> ")
