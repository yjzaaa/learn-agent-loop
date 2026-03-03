#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目启动脚本 - 运行前后端

功能：
1. 启动后端 Agent 交互式会话
2. 启动前端 Next.js 开发服务器
3. 同时启动前后端

使用方法:
    python start.py backend     # 只启动后端
    python start.py frontend    # 只启动前端
    python start.py all         # 同时启动前后端（默认）
    python start.py full        # 启动完整功能 Agent
    python start.py s01~s09     # 启动特定阶段的 Agent
"""

import subprocess
import sys
import os
import time
import signal
import argparse
from pathlib import Path
from typing import Optional, List

# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"


def print_header(text: str):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.RESET}\n")


def print_info(text: str):
    print(f"{Colors.CYAN}[INFO] {text}{Colors.RESET}")


def print_success(text: str):
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")


def print_error(text: str):
    print(f"{Colors.RED}[ERROR] {text}{Colors.RESET}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.RESET}")


class ProcessManager:
    """进程管理器"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        print_info("\n收到终止信号，正在关闭所有进程...")
        self.stop_all()
        sys.exit(0)
    
    def start_process(self, name: str, cmd: List[str], cwd: Path, env: Optional[dict] = None) -> subprocess.Popen:
        """启动进程"""
        print_info(f"启动 {name}...")
        print_info(f"命令: {' '.join(cmd)}")
        
        # 合并环境变量
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        try:
            # Windows 使用 creationflags
            kwargs = {}
            if sys.platform == "win32":
                kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=process_env,
                **kwargs
            )
            
            self.processes.append(process)
            print_success(f"{name} 已启动 (PID: {process.pid})")
            return process
            
        except Exception as e:
            print_error(f"启动 {name} 失败: {e}")
            raise
    
    def stop_all(self):
        """停止所有进程"""
        for process in self.processes:
            if process.poll() is None:  # 进程还在运行
                try:
                    if sys.platform == "win32":
                        process.terminate()
                    else:
                        process.send_signal(signal.SIGTERM)
                    
                    # 等待进程结束
                    process.wait(timeout=5)
                    print_info(f"进程 {process.pid} 已停止")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print_warning(f"进程 {process.pid} 被强制终止")
                except Exception as e:
                    print_error(f"停止进程 {process.pid} 时出错: {e}")
        
        self.processes.clear()
    
    def wait_for_any(self):
        """等待任意一个进程结束"""
        while True:
            for process in self.processes:
                if process.poll() is not None:
                    return process
            time.sleep(0.5)


class BackendRunner:
    """后端运行器"""
    
    AGENT_STAGES = {
        "s01": ("S01 Agent (基础循环)", "agent_s01.py"),
        "s02": ("S02 Agent (工具扩展)", "agent_s02.py"),
        "s03": ("S03 Agent (待办事项)", "agent_s03.py"),
        "s04": ("S04 Agent (子代理)", "agent_s04.py"),
        "s05": ("S05 Agent (技能加载)", "agent_s05.py"),
        "s06": ("S06 Agent (上下文压缩)", "agent_s06.py"),
        "s07": ("S07 Agent (任务系统)", "agent_s07.py"),
        "s08": ("S08 Agent (后台任务)", "agent_s08.py"),
        "s09": ("S09 Agent (团队协作)", "agent_s09.py"),
        "full": ("Full Agent (完整功能)", "agent_full.py"),
    }
    
    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir
    
    def list_stages(self):
        """列出所有可用阶段"""
        print_header("可用的 Agent 阶段")
        for key, (name, _) in self.AGENT_STAGES.items():
            print(f"  {Colors.CYAN}{key:6}{Colors.RESET} - {name}")
        print()
    
    def run(self, stage: str = "full", pm: Optional[ProcessManager] = None) -> Optional[subprocess.Popen]:
        """运行指定阶段的 Agent"""
        if stage not in self.AGENT_STAGES:
            print_error(f"未知的阶段: {stage}")
            print_info(f"可用阶段: {', '.join(self.AGENT_STAGES.keys())}")
            return None
        
        name, filename = self.AGENT_STAGES[stage]
        agent_file = self.agents_dir / filename
        
        if not agent_file.exists():
            print_error(f"Agent 文件不存在: {agent_file}")
            return None
        
        print_header(f"启动后端: {name}")
        
        # 检查环境变量
        if not os.environ.get("DEEPSEEK_API_KEY"):
            print_warning("未设置 DEEPSEEK_API_KEY 环境变量")
            print_info("请先设置: set DEEPSEEK_API_KEY=your_key")
            print_info("或使用 .env 文件")
        
        cmd = [sys.executable, str(filename)]
        
        if pm:
            return pm.start_process(f"Backend ({name})", cmd, self.agents_dir)
        else:
            # 直接运行，阻塞
            try:
                subprocess.run(cmd, cwd=self.agents_dir)
            except KeyboardInterrupt:
                print_info("后端已停止")
            return None


class FrontendRunner:
    """前端运行器"""
    
    def __init__(self, web_dir: Path):
        self.web_dir = web_dir
        self.npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    
    def check_dependencies(self) -> bool:
        """检查依赖是否已安装"""
        node_modules = self.web_dir / "node_modules"
        if not node_modules.exists():
            print_warning("node_modules 不存在，需要先安装依赖")
            print_info("运行: npm install")
            return False
        return True
    
    def install_dependencies(self):
        """安装依赖"""
        print_header("安装前端依赖")
        try:
            result = subprocess.run(
                [self.npm_cmd, "install"],
                cwd=self.web_dir,
                check=True
            )
            print_success("依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print_error(f"依赖安装失败: {e}")
            return False
    
    def extract_content(self):
        """提取内容"""
        print_info("提取文档内容...")
        try:
            result = subprocess.run(
                [self.npm_cmd, "run", "extract"],
                cwd=self.web_dir,
                check=True,
                capture_output=True,
                text=True
            )
            print_success("内容提取完成")
            return True
        except subprocess.CalledProcessError as e:
            print_warning(f"内容提取可能已是最新: {e}")
            return True
    
    def run(self, pm: Optional[ProcessManager] = None) -> Optional[subprocess.Popen]:
        """运行前端开发服务器"""
        print_header("启动前端开发服务器")
        
        # 检查依赖
        if not self.check_dependencies():
            if not self.install_dependencies():
                return None
        
        # 提取内容
        self.extract_content()
        
        cmd = [self.npm_cmd, "run", "dev"]
        
        if pm:
            process = pm.start_process("Frontend (Next.js)", cmd, self.web_dir)
            print_info("前端将在 http://localhost:3000 启动")
            print_info("按 Ctrl+C 停止所有服务")
            return process
        else:
            # 直接运行，阻塞
            try:
                subprocess.run(cmd, cwd=self.web_dir)
            except KeyboardInterrupt:
                print_info("前端已停止")
            return None


def run_both(agents_dir: Path, web_dir: Path, backend_stage: str = "full"):
    """同时运行前后端"""
    print_header("启动前后端服务")
    
    pm = ProcessManager()
    
    # 启动前端
    frontend = FrontendRunner(web_dir)
    frontend_process = frontend.run(pm)
    
    if not frontend_process:
        print_error("前端启动失败")
        return 1
    
    # 等待前端启动
    print_info("等待前端初始化...")
    time.sleep(3)
    
    # 启动后端
    backend = BackendRunner(agents_dir)
    backend_process = backend.run(backend_stage, pm)
    
    if not backend_process:
        print_error("后端启动失败")
        pm.stop_all()
        return 1
    
    print_header("所有服务已启动")
    print_info("前端: http://localhost:3000")
    print_info(f"后端: {backend_stage} Agent 交互式会话")
    print_info("按 Ctrl+C 停止所有服务")
    print()
    
    # 等待任意进程结束
    try:
        finished_process = pm.wait_for_any()
        print_warning(f"进程已结束 (返回码: {finished_process.returncode})")
    except KeyboardInterrupt:
        print_info("\n用户中断")
    finally:
        pm.stop_all()
    
    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="启动 Agent Loop 项目的前后端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python start.py              # 启动完整功能 Agent
  python start.py backend      # 只启动后端
  python start.py frontend     # 只启动前端
  python start.py all          # 同时启动前后端
  python start.py s03          # 启动 S03 Agent
  python start.py --list       # 列出所有可用阶段
        """
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="full",
        help="要启动的服务 (backend, frontend, all, full, s01~s09)"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有可用的 Agent 阶段"
    )
    
    args = parser.parse_args()
    
    # 获取目录
    project_dir = Path(__file__).parent.resolve()
    agents_dir = project_dir / "agents"
    web_dir = project_dir / "web"
    
    # 检查目录
    if not agents_dir.exists():
        print_error(f"Agents 目录不存在: {agents_dir}")
        return 1
    
    if not web_dir.exists():
        print_error(f"Web 目录不存在: {web_dir}")
        return 1
    
    # 列出阶段
    if args.list:
        backend = BackendRunner(agents_dir)
        backend.list_stages()
        return 0
    
    # 处理命令
    command = args.command.lower()
    
    if command in ["backend", "back", "b"]:
        # 只启动后端
        backend = BackendRunner(agents_dir)
        backend.run("full")
        
    elif command in ["frontend", "front", "f", "web", "w"]:
        # 只启动前端
        frontend = FrontendRunner(web_dir)
        frontend.run()
        
    elif command in ["all", "both", "a"]:
        # 同时启动前后端
        return run_both(agents_dir, web_dir, "full")
        
    elif command in BackendRunner.AGENT_STAGES:
        # 启动指定阶段
        backend = BackendRunner(agents_dir)
        backend.run(command)
        
    else:
        print_error(f"未知命令: {command}")
        print_info("可用命令: backend, frontend, all, full, s01~s09")
        print_info("使用 --list 查看所有阶段")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
