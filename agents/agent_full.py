#!/usr/bin/env python3
"""
agent_full.py - 完整 Agent

重构后的面向对象版本。

组合所有功能：
- 基础工具 (S02)
- 待办事项 (S03)
- 子代理 (S04)
- 技能加载 (S05)
- 上下文压缩 (S06)
- 任务系统 (S07)
- 后台任务 (S08)
- 团队协作 (S09)

核心洞察："组合胜过继承 —— 通过 Mixin 构建复杂功能。"
"""

import json

from core import (
    BaseAgent,
    ToolsMixin,
    TodoMixin,
    TaskMixin,
    SkillMixin,
    CompressionMixin,
    BackgroundMixin,
    TeamMixin,
    SubagentMixin,
)


class FullAgent(
    CompressionMixin,   # 最先处理上下文压缩
    TeamMixin,          # 处理收件箱和队友
    BackgroundMixin,    # 处理后台通知
    TodoMixin,          # 待办事项管理
    SubagentMixin,      # 子代理
    SkillMixin,         # 技能加载
    TaskMixin,          # 任务系统
    ToolsMixin,         # 基础工具
    BaseAgent,          # 基类最后
):
    """
    完整 Agent - 包含所有功能。
    
    Mixin 顺序决定 pre_loop_hook 和 post_loop_hook 的调用顺序。
    使用 MRO（方法解析顺序）确保所有钩子都被正确调用。
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 构建包含所有技能描述的系统提示词
        self.system_prompt = f"""You are a coding agent at {self.workdir}.
Use tools to solve tasks.

Features available:
- TodoWrite: Short checklists for immediate work
- task_create/update/list: Persistent tasks with dependencies
- task: Subagent delegation for isolated work
- load_skill: Specialized knowledge on demand
- compact: Manual conversation compression
- background_run: Non-blocking command execution
- spawn_teammate: Create persistent team members

Skills available:
{self.get_skill_descriptions()}

The system will automatically compress context when needed."""
    
    def _handle_command(self, cmd: str, history: list) -> bool:
        """处理斜杠命令"""
        if cmd == "/compact":
            if history:
                print("[manual compact via /compact]")
                history[:] = self._auto_compact(history)
            return True
        elif cmd == "/tasks":
            print(self.task_list())
            return True
        elif cmd == "/team":
            print(self.list_teammates())
            return True
        elif cmd == "/inbox":
            print(json.dumps(self._read_inbox("lead"), indent=2))
            return True
        return super()._handle_command(cmd, history)


if __name__ == "__main__":
    agent = FullAgent()
    agent.interactive_mode("full >> ")
