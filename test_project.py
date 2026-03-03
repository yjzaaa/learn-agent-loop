#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目测试脚本 - 测试前后端

功能：
1. 测试后端 (Python Agents)
2. 测试前端 (Next.js Web)
3. 端到端集成测试

使用方法:
    python test_project.py
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from typing import Optional, Tuple

# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_header(text: str):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.RESET}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}[PASS] {text}{Colors.RESET}")


def print_error(text: str):
    print(f"{Colors.RED}[FAIL] {text}{Colors.RESET}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.RESET}")


def run_command(cmd: list, cwd: Optional[Path] = None, timeout: int = 60, encoding: str = 'utf-8') -> Tuple[int, str, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding=encoding,
            errors='replace'
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


class BackendTester:
    """后端测试器"""
    
    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir
        self.results = []
    
    def test_imports(self) -> bool:
        """测试模块导入"""
        print_header("Backend: Testing Module Imports")
        
        test_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
os.environ['DEEPSEEK_API_KEY'] = 'test-key'
os.environ['DEEPSEEK_MODEL'] = 'deepseek-chat'

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试 core 模块
from core import BaseAgent, ToolsMixin, TodoMixin, TaskMixin
from core import SkillMixin, CompressionMixin, BackgroundMixin
from core import TeamMixin, SubagentMixin
print("Core imports: OK")

# 测试所有 Agent
from agent_s01 import S01Agent
from agent_s02 import S02Agent
from agent_s03 import S03Agent
from agent_s04 import S04Agent
from agent_s05 import S05Agent
from agent_s06 import S06Agent
from agent_s07 import S07Agent
from agent_s08 import S08Agent
from agent_s09 import S09Agent
from agent_full import FullAgent
print("Agent imports: OK")

# 测试初始化
agents = [
    ('S01', S01Agent),
    ('S02', S02Agent),
    ('S03', S03Agent),
    ('S04', S04Agent),
    ('S05', S05Agent),
    ('S06', S06Agent),
    ('S07', S07Agent),
    ('S08', S08Agent),
    ('S09', S09Agent),
    ('Full', FullAgent),
]

for name, cls in agents:
    agent = cls()
    tools = agent.get_tools()
    print(f"{name}: {len(tools)} tools")

print("All agents initialized successfully!")
'''
        
        test_file = self.agents_dir / "_test_imports.py"
        try:
            test_file.write_text(test_code, encoding='utf-8')
            returncode, stdout, stderr = run_command(
                [sys.executable, str(test_file.name)],
                cwd=self.agents_dir,
                timeout=30
            )
            
            if returncode == 0:
                print(stdout)
                print_success("All imports successful")
                return True
            else:
                print_error(f"Import failed:\n{stderr}")
                return False
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_tools(self) -> bool:
        """测试工具功能"""
        print_header("Backend: Testing Tool Functions")
        
        test_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
os.environ['DEEPSEEK_API_KEY'] = 'test-key'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_s02 import S02Agent

agent = S02Agent()

# 测试 bash 工具
print("Testing bash tool...")
result = agent.run_bash("echo Hello from test")
assert "Hello from test" in result, f"Bash test failed: {result}"
print(f"  bash: {result.strip()}")

# 测试文件操作
print("Testing file operations...")
test_file = "_test_file.txt"
write_result = agent.run_write(test_file, "Hello World")
print(f"  write: {write_result}")

read_result = agent.run_read(test_file)
assert "Hello World" in read_result, f"Read test failed: {read_result}"
print(f"  read: {read_result.strip()}")

edit_result = agent.run_edit(test_file, "Hello", "Hi")
print(f"  edit: {edit_result}")

read_result2 = agent.run_read(test_file)
assert "Hi World" in read_result2, f"Edit test failed: {read_result2}"
print(f"  read after edit: {read_result2.strip()}")

# 清理
import os as os_module
os_module.remove(test_file)

print("All tool tests passed!")
'''
        
        test_file = self.agents_dir / "_test_tools.py"
        try:
            test_file.write_text(test_code, encoding='utf-8')
            returncode, stdout, stderr = run_command(
                [sys.executable, str(test_file.name)],
                cwd=self.agents_dir,
                timeout=30
            )
            
            if returncode == 0:
                print(stdout)
                print_success("All tool tests passed")
                return True
            else:
                print_error(f"Tool test failed:\n{stderr}")
                return False
        finally:
            if test_file.exists():
                test_file.unlink()
            test_txt = self.agents_dir / "_test_file.txt"
            if test_txt.exists():
                test_txt.unlink()
    
    def test_todo_system(self) -> bool:
        """测试待办系统"""
        print_header("Backend: Testing Todo System")
        
        test_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
os.environ['DEEPSEEK_API_KEY'] = 'test-key'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_s03 import S03Agent

agent = S03Agent()

# 测试待办更新
items = [
    {"id": "1", "text": "Task 1", "status": "pending"},
    {"id": "2", "text": "Task 2", "status": "in_progress"},
]
result = agent.update_todos(items)
print("Todo update result:")
print(result)

# 测试渲染
rendered = agent._render_todos()
assert "Task 1" in rendered
assert "Task 2" in rendered
print("Rendered todos:")
print(rendered)

print("Todo system test passed!")
'''
        
        test_file = self.agents_dir / "_test_todo.py"
        try:
            test_file.write_text(test_code, encoding='utf-8')
            returncode, stdout, stderr = run_command(
                [sys.executable, str(test_file.name)],
                cwd=self.agents_dir,
                timeout=30
            )
            
            if returncode == 0:
                print(stdout)
                print_success("Todo system test passed")
                return True
            else:
                print_error(f"Todo test failed:\n{stderr}")
                return False
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_task_system(self) -> bool:
        """测试任务系统"""
        print_header("Backend: Testing Task System")
        
        test_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

os.environ['DEEPSEEK_API_KEY'] = 'test-key'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_s07 import S07Agent

# 使用临时目录
temp_dir = tempfile.mkdtemp()

agent = S07Agent(tasks_dir=Path(temp_dir) / ".tasks")

# 测试创建任务
result1 = agent.task_create("Test Task 1", "Description 1")
print("Created task:")
print(result1)

result2 = agent.task_create("Test Task 2", "Description 2")
task2 = json.loads(result2)
print(f"Created task 2: ID={task2['id']}")

# 测试列出任务
list_result = agent.task_list()
print("Task list:")
print(list_result)

# 测试更新任务
update_result = agent.task_update(task2['id'], status="in_progress")
print("Updated task:")
print(update_result)

# 验证更新
updated_task = json.loads(update_result)
assert updated_task['status'] == 'in_progress'

# 清理
shutil.rmtree(temp_dir)

print("Task system test passed!")
'''
        
        test_file = self.agents_dir / "_test_tasks.py"
        try:
            test_file.write_text(test_code, encoding='utf-8')
            returncode, stdout, stderr = run_command(
                [sys.executable, str(test_file.name)],
                cwd=self.agents_dir,
                timeout=30
            )
            
            if returncode == 0:
                print(stdout)
                print_success("Task system test passed")
                return True
            else:
                print_error(f"Task test failed:\n{stderr}")
                return False
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def run_all_tests(self) -> bool:
        """运行所有后端测试"""
        print_header("BACKEND TESTS")
        
        tests = [
            ("Module Imports", self.test_imports),
            ("Tool Functions", self.test_tools),
            ("Todo System", self.test_todo_system),
            ("Task System", self.test_task_system),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print_error(f"{name} test crashed: {e}")
                failed += 1
        
        print_header("BACKEND TEST SUMMARY")
        print(f"Passed: {Colors.GREEN}{passed}{Colors.RESET}")
        print(f"Failed: {Colors.RED}{failed}{Colors.RESET}")
        
        return failed == 0


class FrontendTester:
    """前端测试器"""
    
    def __init__(self, web_dir: Path):
        self.web_dir = web_dir
        self.node_modules = web_dir / "node_modules"
    
    def check_node_installed(self) -> bool:
        """检查 Node.js 是否安装"""
        returncode, stdout, stderr = run_command(["node", "--version"])
        if returncode == 0:
            print_success(f"Node.js version: {stdout.strip()}")
            return True
        else:
            print_error("Node.js not found")
            return False
    
    def check_npm_installed(self) -> bool:
        """检查 npm 是否安装"""
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        returncode, stdout, stderr = run_command([npm_cmd, "--version"])
        if returncode == 0:
            print_success(f"npm version: {stdout.strip()}")
            return True
        else:
            print_error("npm not found")
            return False
    
    def install_dependencies(self) -> bool:
        """安装依赖"""
        print_header("Frontend: Installing Dependencies")
        
        if self.node_modules.exists():
            print_warning("node_modules already exists, skipping install")
            return True
        
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        returncode, stdout, stderr = run_command(
            [npm_cmd, "install"],
            cwd=self.web_dir,
            timeout=180
        )
        
        if returncode == 0:
            print_success("Dependencies installed")
            return True
        else:
            print_error(f"Failed to install dependencies:\n{stderr}")
            return False
    
    def test_build(self) -> bool:
        """测试构建"""
        print_header("Frontend: Testing Build")
        
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        
        # 先运行 extract
        returncode, stdout, stderr = run_command(
            [npm_cmd, "run", "extract"],
            cwd=self.web_dir,
            timeout=60
        )
        
        if returncode != 0:
            print_error(f"Extract failed:\n{stderr}")
            return False
        
        print_success("Content extracted")
        
        # 然后构建
        returncode, stdout, stderr = run_command(
            [npm_cmd, "run", "build"],
            cwd=self.web_dir,
            timeout=300
        )
        
        if returncode == 0:
            print_success("Build successful")
            out_dir = self.web_dir / ".next"
            if out_dir.exists():
                print_success(f"Build output directory exists: {out_dir}")
            return True
        else:
            print_error(f"Build failed:\n{stderr}")
            return False
    
    def test_typescript(self) -> bool:
        """测试 TypeScript 类型检查"""
        print_header("Frontend: TypeScript Type Check")
        
        npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
        returncode, stdout, stderr = run_command(
            [npx_cmd, "tsc", "--noEmit"],
            cwd=self.web_dir,
            timeout=60
        )
        
        if returncode == 0:
            print_success("TypeScript type check passed")
            return True
        else:
            # TypeScript 错误可能很长，只显示前 500 字符
            error_msg = stderr[:500] if stderr else stdout[:500]
            print_error(f"TypeScript errors:\n{error_msg}...")
            return False
    
    def check_files_structure(self) -> bool:
        """检查文件结构"""
        print_header("Frontend: Checking File Structure")
        
        required_dirs = [
            "src/app",
            "src/components",
            "src/data",
            "src/hooks",
            "src/lib",
            "src/types",
            "src/i18n",
        ]
        
        all_exist = True
        for dir_path in required_dirs:
            full_path = self.web_dir / dir_path
            if full_path.exists():
                print_success(f"{dir_path} exists")
            else:
                print_error(f"{dir_path} missing")
                all_exist = False
        
        required_files = [
            "package.json",
            "tsconfig.json",
            "next.config.ts",
            "src/app/page.tsx",
        ]
        
        for file_path in required_files:
            full_path = self.web_dir / file_path
            if full_path.exists():
                print_success(f"{file_path} exists")
            else:
                print_error(f"{file_path} missing")
                all_exist = False
        
        return all_exist
    
    def run_all_tests(self) -> bool:
        """运行所有前端测试"""
        print_header("FRONTEND TESTS")
        
        if not self.check_node_installed() or not self.check_npm_installed():
            print_error("Node.js or npm not available, skipping frontend tests")
            return False
        
        tests = [
            ("File Structure", self.check_files_structure),
            ("Install Dependencies", self.install_dependencies),
            ("TypeScript Check", self.test_typescript),
            ("Build Test", self.test_build),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
                    if name == "Install Dependencies":
                        print_error(f"Critical test '{name}' failed, stopping frontend tests")
                        break
            except Exception as e:
                print_error(f"{name} test crashed: {e}")
                failed += 1
        
        print_header("FRONTEND TEST SUMMARY")
        print(f"Passed: {Colors.GREEN}{passed}{Colors.RESET}")
        print(f"Failed: {Colors.RED}{failed}{Colors.RESET}")
        
        return failed == 0


class IntegrationTester:
    """集成测试器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.agents_dir = project_dir / "agents"
        self.web_dir = project_dir / "web"
    
    def test_docs_sync(self) -> bool:
        """测试文档同步"""
        print_header("Integration: Testing Docs Sync")
        
        docs_dir = self.project_dir / "docs"
        if not docs_dir.exists():
            print_warning("docs directory not found")
            return True
        
        generated_dir = self.web_dir / "src" / "data" / "generated"
        if generated_dir.exists():
            docs_json = generated_dir / "docs.json"
            if docs_json.exists():
                print_success("Generated docs.json exists")
                return True
            else:
                print_warning("docs.json not generated yet (run npm run extract)")
                return True
        else:
            print_warning("Generated data directory not found")
            return True
    
    def test_agents_core_importable(self) -> bool:
        """测试 agents/core 可以从项目根目录导入"""
        print_header("Integration: Testing Import Paths")
        
        test_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, 'agents')

os.environ['DEEPSEEK_API_KEY'] = 'test'

from core import BaseAgent, ToolsMixin
print("agents.core importable from project root")

class TestAgent(ToolsMixin, BaseAgent):
    pass

agent = TestAgent()
print(f"Agent created with {len(agent.get_tools())} tools")
print("Import path test passed!")
'''
        
        test_file = self.project_dir / "_test_import.py"
        try:
            test_file.write_text(test_code, encoding='utf-8')
            returncode, stdout, stderr = run_command(
                [sys.executable, str(test_file.name)],
                cwd=self.project_dir,
                timeout=30
            )
            
            if returncode == 0:
                print(stdout)
                print_success("Import paths working")
                return True
            else:
                print_error(f"Import test failed:\n{stderr}")
                return False
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def run_all_tests(self) -> bool:
        """运行所有集成测试"""
        print_header("INTEGRATION TESTS")
        
        tests = [
            ("Import Paths", self.test_agents_core_importable),
            ("Docs Sync", self.test_docs_sync),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print_error(f"{name} test crashed: {e}")
                failed += 1
        
        print_header("INTEGRATION TEST SUMMARY")
        print(f"Passed: {Colors.GREEN}{passed}{Colors.RESET}")
        print(f"Failed: {Colors.RED}{failed}{Colors.RESET}")
        
        return failed == 0


def main():
    """主函数"""
    project_dir = Path(__file__).parent.resolve()
    agents_dir = project_dir / "agents"
    web_dir = project_dir / "web"
    
    print_header("PROJECT TEST SUITE")
    print(f"Project directory: {project_dir}")
    print(f"Agents directory: {agents_dir}")
    print(f"Web directory: {web_dir}")
    
    if not agents_dir.exists():
        print_error(f"Agents directory not found: {agents_dir}")
        return 1
    
    if not web_dir.exists():
        print_error(f"Web directory not found: {web_dir}")
        return 1
    
    results = []
    
    backend_tester = BackendTester(agents_dir)
    results.append(("Backend", backend_tester.run_all_tests()))
    
    frontend_tester = FrontendTester(web_dir)
    results.append(("Frontend", frontend_tester.run_all_tests()))
    
    integration_tester = IntegrationTester(project_dir)
    results.append(("Integration", integration_tester.run_all_tests()))
    
    print_header("FINAL TEST SUMMARY")
    for name, passed in results:
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if passed else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"  {name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print(f"\n{Colors.GREEN}All tests passed!{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}Some tests failed!{Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
