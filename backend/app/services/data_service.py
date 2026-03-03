"""
数据服务层

负责读取和管理前端数据文件
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from functools import lru_cache

from app.core.config import settings
from app.core.logger import get_logger, info, error, exception
from app.models.schemas import (
    AgentVersion, AgentLayer, Scenario, VisualizationData,
    ExecutionFlow, DocItem, VersionDiff, ClassInfo, FunctionInfo
)

logger = get_logger(__name__)


class DataService:
    """数据服务类"""
    
    def __init__(self):
        # 尝试多种路径找到数据目录
        possible_paths = [
            Path(settings.DATA_DIR),
            Path(__file__).parent.parent.parent.parent / "web" / "src" / "data",
            Path(__file__).parent.parent.parent.parent.parent / "web" / "src" / "data",
            Path.cwd() / "web" / "src" / "data",
            Path.cwd().parent / "web" / "src" / "data",
        ]
        
        self.data_dir = None
        for path in possible_paths:
            if path.exists():
                self.data_dir = path
                break
        
        if self.data_dir is None:
            # 使用第一个路径作为默认值（即使不存在）
            self.data_dir = possible_paths[0]
            error(f"Data directory not found in any of: {[str(p) for p in possible_paths]}")
        
        self._versions_cache: Optional[List[AgentVersion]] = None
        self._scenarios_cache: Dict[str, List[Scenario]] = {}
        self._visualizations_cache: Dict[str, VisualizationData] = {}
        self._docs_cache: Optional[List[DocItem]] = None
        
        info("DataService initialized", extra={"data_dir": str(self.data_dir), "exists": self.data_dir.exists()})
    
    def _read_json(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """读取 JSON 文件"""
        try:
            if not filepath.exists():
                error(f"File not found: {filepath}")
                return None
            
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            error(f"Invalid JSON in {filepath}: {e}")
            return None
        except Exception as e:
            exception(f"Error reading {filepath}")
            return None
    
    def _read_text(self, filepath: Path) -> str:
        """读取文本文件"""
        try:
            if not filepath.exists():
                return ""
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            error(f"Error reading text file {filepath}: {e}")
            return ""
    
    # ==================== 版本数据 ====================
    
    def _convert_classes(self, classes_data: List[Any]) -> List[Any]:
        """转换类数据格式"""
        result = []
        for c in classes_data:
            if isinstance(c, str):
                result.append(c)
            elif isinstance(c, dict):
                result.append(ClassInfo(
                    name=c.get("name", ""),
                    startLine=c.get("startLine", 0),
                    endLine=c.get("endLine", 0)
                ))
        return result
    
    def _convert_functions(self, functions_data: List[Any]) -> List[Any]:
        """转换函数数据格式"""
        result = []
        for f in functions_data:
            if isinstance(f, str):
                result.append(f)
            elif isinstance(f, dict):
                result.append(FunctionInfo(
                    name=f.get("name", ""),
                    signature=f.get("signature", ""),
                    startLine=f.get("startLine", 0)
                ))
        return result
    
    def _extract_class_names(self, classes_data: List[Any]) -> List[str]:
        """提取类名列表"""
        result = []
        for c in classes_data:
            if isinstance(c, str):
                result.append(c)
            elif isinstance(c, dict):
                result.append(c.get("name", ""))
        return result
    
    def _extract_function_names(self, functions_data: List[Any]) -> List[str]:
        """提取函数名列表"""
        result = []
        for f in functions_data:
            if isinstance(f, str):
                result.append(f)
            elif isinstance(f, dict):
                result.append(f.get("name", ""))
        return result
    
    def get_versions(self) -> List[AgentVersion]:
        """获取所有版本列表"""
        if self._versions_cache is not None:
            return self._versions_cache
        
        versions = []
        versions_file = self.data_dir / "generated" / "versions.json"
        
        data = self._read_json(versions_file)
        if not data:
            return versions
        
        version_list = data.get("versions", [])
        version_meta = self._get_version_meta()
        
        for v in version_list:
            version_id = v.get("id", "")
            meta = version_meta.get(version_id, {})
            
            # 转换 classes 和 functions
            raw_classes = v.get("classes", [])
            raw_functions = v.get("functions", [])
            
            version = AgentVersion(
                id=version_id,
                title=v.get("title", meta.get("title", version_id)),
                subtitle=v.get("subtitle", meta.get("subtitle", "")),
                description=meta.get("description", ""),
                layer=v.get("layer", meta.get("layer", "tools")),
                prev_version=meta.get("prevVersion"),
                next_version=meta.get("nextVersion"),
                loc=v.get("loc", 0),
                filename=v.get("filename", ""),
                source=v.get("source", ""),
                tools=v.get("tools", []),
                classes=self._convert_classes(raw_classes),
                functions=self._convert_functions(raw_functions),
                newTools=v.get("newTools", []),
                coreAddition=v.get("coreAddition", ""),
                keyInsight=v.get("keyInsight", ""),
            )
            versions.append(version)
        
        # 按版本ID排序
        versions.sort(key=lambda x: x.id)
        
        self._versions_cache = versions
        info(f"Loaded {len(versions)} versions")
        return versions
    
    def get_version_by_id(self, version_id: str) -> Optional[AgentVersion]:
        """根据 ID 获取版本详情"""
        versions = self.get_versions()
        for v in versions:
            if v.id == version_id:
                return v
        return None
    
    def _get_version_meta(self) -> Dict[str, Any]:
        """获取版本元数据（从 constants.ts 解析）"""
        # 这里简化处理，实际可以从 TypeScript 文件解析或单独维护
        meta = {
            "s01": {
                "title": "L1: Agent Loop",
                "subtitle": "The Foundation",
                "description": "Basic agent loop implementation with tool dispatch",
                "layer": "L1-Coordination",
                "prevVersion": None,
                "nextVersion": "s02",
            },
            "s02": {
                "title": "L1: Tool Dispatch",
                "subtitle": "Enhanced Tools",
                "description": "Tool dispatch system with parallel execution",
                "layer": "L1-Coordination",
                "prevVersion": "s01",
                "nextVersion": "s03",
            },
            "s03": {
                "title": "L1: Todo Write",
                "subtitle": "Task Management",
                "description": "Task management with todo list support",
                "layer": "L1-Coordination",
                "prevVersion": "s02",
                "nextVersion": "s04",
            },
            "s04": {
                "title": "L1: Subagent",
                "subtitle": "Hierarchical Agents",
                "description": "Subagent support for complex tasks",
                "layer": "L1-Coordination",
                "prevVersion": "s03",
                "nextVersion": "s05",
            },
            "s05": {
                "title": "L2: Skill Loading",
                "subtitle": "Dynamic Skills",
                "description": "Dynamic skill loading and management",
                "layer": "L2-Orchestration",
                "prevVersion": "s04",
                "nextVersion": "s06",
            },
            "s06": {
                "title": "L2: Context Compact",
                "subtitle": "Context Management",
                "description": "Context compaction for long conversations",
                "layer": "L2-Orchestration",
                "prevVersion": "s05",
                "nextVersion": "s07",
            },
            "s07": {
                "title": "L2: Task System",
                "subtitle": "Advanced Tasks",
                "description": "Advanced task system with dependencies",
                "layer": "L2-Orchestration",
                "prevVersion": "s06",
                "nextVersion": "s08",
            },
            "s08": {
                "title": "L2: Background Tasks",
                "subtitle": "Async Processing",
                "description": "Background task processing",
                "layer": "L2-Orchestration",
                "prevVersion": "s07",
                "nextVersion": "s09",
            },
            "s09": {
                "title": "L3: Agent Teams",
                "subtitle": "Multi-Agent",
                "description": "Multi-agent team collaboration",
                "layer": "L3-Execution",
                "prevVersion": "s08",
                "nextVersion": "s10",
            },
            "s10": {
                "title": "L3: Team Protocols",
                "subtitle": "Communication",
                "description": "Inter-team communication protocols",
                "layer": "L3-Execution",
                "prevVersion": "s09",
                "nextVersion": "s11",
            },
            "s11": {
                "title": "L3: Autonomous Agents",
                "subtitle": "Self-Directed",
                "description": "Fully autonomous agent operations",
                "layer": "L3-Execution",
                "prevVersion": "s10",
                "nextVersion": "s12",
            },
            "s12": {
                "title": "L3: Worktree Isolation",
                "subtitle": "Task Isolation",
                "description": "Task-level worktree isolation",
                "layer": "L3-Execution",
                "prevVersion": "s11",
                "nextVersion": None,
            },
        }
        return meta
    
    def compare_versions(self, from_id: str, to_id: str) -> Optional[VersionDiff]:
        """比较两个版本的差异"""
        from_version = self.get_version_by_id(from_id)
        to_version = self.get_version_by_id(to_id)
        
        if not from_version or not to_version:
            return None
        
        loc_delta = to_version.loc - from_version.loc
        
        new_tools = list(set(to_version.tools) - set(from_version.tools))
        
        # 提取类名进行比较
        from_class_names = self._extract_class_names(from_version.classes)
        to_class_names = self._extract_class_names(to_version.classes)
        new_classes = list(set(to_class_names) - set(from_class_names))
        
        # 提取函数名进行比较
        from_func_names = self._extract_function_names(from_version.functions)
        to_func_names = self._extract_function_names(to_version.functions)
        new_functions = list(set(to_func_names) - set(from_func_names))
        
        return VersionDiff(
            from_version=from_id,
            to_version=to_id,
            loc_delta=loc_delta,
            new_tools=new_tools,
            new_classes=new_classes,
            new_functions=new_functions,
        )
    
    # ==================== 场景数据 ====================
    
    def get_scenarios(self, version_id: Optional[str] = None) -> List[Scenario]:
        """获取场景列表"""
        if version_id in self._scenarios_cache:
            return self._scenarios_cache[version_id]
        
        scenarios = []
        
        if version_id:
            # 获取指定版本的场景
            scenario_file = self.data_dir / "scenarios" / f"{version_id}.json"
            data = self._read_json(scenario_file)
            if data:
                scenario = Scenario(
                    id=f"{version_id}_scenario",
                    version_id=version_id,
                    title=data.get("title", ""),
                    description=data.get("description", ""),
                    steps=data.get("steps", []),
                )
                scenarios.append(scenario)
        else:
            # 获取所有场景
            scenarios_dir = self.data_dir / "scenarios"
            if scenarios_dir.exists():
                for file in scenarios_dir.glob("s*.json"):
                    version_id = file.stem
                    data = self._read_json(file)
                    if data:
                        scenario = Scenario(
                            id=f"{version_id}_scenario",
                            version_id=version_id,
                            title=data.get("title", ""),
                            description=data.get("description", ""),
                            steps=data.get("steps", []),
                        )
                        scenarios.append(scenario)
        
        self._scenarios_cache[version_id] = scenarios
        return scenarios
    
    def get_scenario_by_version(self, version_id: str) -> Optional[Scenario]:
        """根据版本ID获取场景"""
        scenarios = self.get_scenarios(version_id)
        return scenarios[0] if scenarios else None
    
    # ==================== 可视化数据 ====================
    
    def get_visualization(self, version_id: str) -> Optional[VisualizationData]:
        """获取可视化数据"""
        if version_id in self._visualizations_cache:
            return self._visualizations_cache[version_id]
        
        annotation_file = self.data_dir / "annotations" / f"{version_id}.json"
        data = self._read_json(annotation_file)
        
        if not data:
            return None
        
        # 构建可视化数据
        nodes = []
        edges = []
        states = []
        
        # 从注释数据构建节点和边
        for i, step in enumerate(data.get("steps", [])):
            # 添加节点
            node = {
                "id": f"node_{i}",
                "type": step.get("type", "default"),
                "label": step.get("title", f"Step {i}"),
                "x": i * 100,
                "y": 100,
                "data": step,
            }
            nodes.append(node)
            
            # 添加边
            if i > 0:
                edge = {
                    "id": f"edge_{i-1}_{i}",
                    "source": f"node_{i-1}",
                    "target": f"node_{i}",
                    "label": None,
                    "animated": True,
                }
                edges.append(edge)
            
            # 添加状态
            state = {
                "step": i,
                "title": step.get("title", ""),
                "description": step.get("description", ""),
                "active_nodes": [f"node_{i}"],
                "highlighted_edges": [f"edge_{i-1}_{i}"] if i > 0 else [],
            }
            states.append(state)
        
        viz_data = VisualizationData(
            id=f"{version_id}_viz",
            version_id=version_id,
            title=data.get("title", ""),
            description=data.get("description", ""),
            nodes=nodes,
            edges=edges,
            states=states,
        )
        
        self._visualizations_cache[version_id] = viz_data
        return viz_data
    
    # ==================== 执行流程数据 ====================
    
    def get_execution_flow(self, version_id: str) -> Optional[ExecutionFlow]:
        """获取执行流程数据"""
        # 从 execution-flows.ts 或单独文件读取
        # 这里简化处理
        version = self.get_version_by_id(version_id)
        if not version:
            return None
        
        # 构建执行流程步骤
        steps = [
            {
                "step": 1,
                "title": "Initialize",
                "description": "Initialize agent context and load configuration",
                "actor": "System",
                "action": "init",
                "details": {"version": version_id},
            },
            {
                "step": 2,
                "title": "Process Input",
                "description": "Process user input and parse intent",
                "actor": "Agent",
                "action": "parse",
                "details": {},
            },
            {
                "step": 3,
                "title": "Execute",
                "description": "Execute agent logic with available tools",
                "actor": "Agent",
                "action": "execute",
                "details": {"tools": version.tools},
            },
            {
                "step": 4,
                "title": "Return Result",
                "description": "Return execution result to user",
                "actor": "System",
                "action": "respond",
                "details": {},
            },
        ]
        
        return ExecutionFlow(
            id=f"{version_id}_flow",
            version_id=version_id,
            title=f"{version.title} - Execution Flow",
            description=f"Execution flow for {version.title}",
            steps=steps,
        )
    
    # ==================== 文档数据 ====================
    
    def get_docs(self, version_id: Optional[str] = None) -> List[DocItem]:
        """获取文档列表"""
        if self._docs_cache is not None:
            docs = self._docs_cache
        else:
            docs = []
            docs_file = self.data_dir / "generated" / "docs.json"
            data = self._read_json(docs_file)
            
            # docs.json 是一个数组，直接使用
            if isinstance(data, list):
                for i, doc in enumerate(data):
                    doc_item = DocItem(
                        id=doc.get("id", f"doc_{i}"),
                        version_id=doc.get("version", ""),
                        title=doc.get("title", ""),
                        content=doc.get("content", ""),
                        category=doc.get("category", "general"),
                        order=doc.get("order", i),
                    )
                    docs.append(doc_item)
            elif data and "docs" in data:
                for i, doc in enumerate(data["docs"]):
                    doc_item = DocItem(
                        id=doc.get("id", f"doc_{i}"),
                        version_id=doc.get("version_id", doc.get("version", "")),
                        title=doc.get("title", ""),
                        content=doc.get("content", ""),
                        category=doc.get("category", "general"),
                        order=doc.get("order", i),
                    )
                    docs.append(doc_item)
            
            self._docs_cache = docs
        
        if version_id:
            return [d for d in docs if d.version_id == version_id]
        return docs
    
    def get_doc_by_id(self, doc_id: str) -> Optional[DocItem]:
        """根据 ID 获取文档"""
        docs = self.get_docs()
        for doc in docs:
            if doc.id == doc_id:
                return doc
        return None


# 单例实例
data_service = DataService()
