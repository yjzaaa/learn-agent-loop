#!/usr/bin/env python3
"""
agent_s05.py - 技能加载 (Skills)

重构后的面向对象版本。

两层技能注入机制：
- 第1层（廉价）：系统提示词中的技能名称
- 第2层（按需）：工具结果中的完整技能内容

核心洞察："不要把所有内容都放入系统提示词。按需加载。"
"""

from core import BaseAgent, ToolsMixin, SkillMixin


class S05Agent(SkillMixin, ToolsMixin, BaseAgent):
    """
    技能加载 Agent - 添加动态知识加载能力。
    
    技能从 skills/<name>/SKILL.md 加载。
    """
    
    def __init__(self, **kwargs):
        # 注意：需要先初始化 SkillMixin 来加载技能
        super().__init__(**kwargs)
        
        # 构建包含技能描述的系统提示词
        self.system_prompt = f"""You are a coding agent at {self.workdir}.
Use load_skill to access specialized knowledge before tackling unfamiliar topics.

Skills available:
{self.get_skill_descriptions()}"""
        # SkillMixin 自动注册 load_skill 工具


if __name__ == "__main__":
    agent = S05Agent()
    agent.interactive_mode("s05 >> ")
