#!/usr/bin/env python3
"""
agent_s01.py - 代理循环 (Agent Loop)

重构后的面向对象版本。

AI 编程代理的全部秘诀都包含在这个模式中：

    while stop_reason == "tool_calls":
        response = LLM(messages, tools)
        execute tools
        append results

核心洞察："循环本身很简单 —— 复杂性来自组合。"
"""

from core import BaseAgent


class S01Agent(BaseAgent):
    """
    基础 Agent - 仅支持 bash 工具。
    
    这是最简单的 Agent 实现，展示核心循环模式。
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system_prompt = f"""You are a coding agent at {self.workdir}.
Use bash to solve tasks. Act, don't explain."""
    
    def _init_tools(self) -> None:
        """只注册 bash 工具"""
        # 不调用 super()._init_tools()，只注册我们需要的工具
        self.register_tool(
            name="bash",
            handler=self.run_bash,
            description="Run a shell command.",
            parameters={"command": {"type": "string"}},
            required=["command"]
        )
    
    def run_bash(self, command: str) -> str:
        """执行 shell 命令"""
        import subprocess
        
        dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
        if any(d in command for d in dangerous):
            return "Error: Dangerous command blocked"
        
        try:
            result = subprocess.run(
                command, shell=True, cwd=self.workdir,
                capture_output=True, text=True, timeout=120
            )
            output = (result.stdout + result.stderr).strip()
            return output[:50000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Timeout (120s)"


if __name__ == "__main__":
    agent = S01Agent()
    agent.interactive_mode("s01 >> ")
