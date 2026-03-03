#!/usr/bin/env python3
"""
agent_s09.py - Agent 团队 (Agent Teams)

重构后的面向对象版本。

持久化的命名 agent，使用基于文件的 JSONL 收件箱通信。
每个队友在单独的线程中运行自己的 agent 循环。

核心洞察："可以互相交谈的队友。"
"""

import json
from core import BaseAgent, ToolsMixin, TeamMixin


class S09Agent(TeamMixin, ToolsMixin, BaseAgent):
    """
    团队 Agent - 添加多 Agent 协作能力。
    
    团队成员：
    - 持久化状态
    - 独立线程
    - 通过收件箱通信
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system_prompt = f"""You are a team lead at {self.workdir}.
Spawn teammates and communicate via inboxes.
Each teammate runs in its own thread."""
        # TeamMixin 自动：
        # 1. 注册 spawn_teammate, list_teammates, send_message, read_inbox, broadcast 工具
        # 2. 在 pre_loop_hook 中注入收件箱消息
    
    def _handle_command(self, cmd: str, history: list) -> bool:
        """扩展命令处理"""
        if cmd == "/team":
            print(self.list_teammates())
            return True
        elif cmd == "/inbox":
            print(json.dumps(self._read_inbox("lead"), indent=2))
            return True
        return super()._handle_command(cmd, history)


if __name__ == "__main__":
    agent = S09Agent()
    agent.interactive_mode("s09 >> ")
