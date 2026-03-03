"""
Kuzu Database Connection

管理知识图谱数据库连接和会话
"""

import os
import threading
from pathlib import Path
from typing import Optional
import kuzu


class KuzuDatabase:
    """Kuzu 图数据库管理器"""
    
    _instance: Optional['KuzuDatabase'] = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: Optional[str] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: Optional[str] = None):
        if self._initialized:
            return
            
        self.db_path = db_path or os.getenv("KUZU_DB_PATH", "./data/agentcore.db")
        self._db: Optional[kuzu.Database] = None
        self._conn: Optional[kuzu.Connection] = None
        self._initialized = False
        
        # 确保目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._connect()
        self._initialize_schema()
        self._initialized = True
    
    def _connect(self):
        """建立数据库连接"""
        self._db = kuzu.Database(self.db_path)
        self._conn = kuzu.Connection(self._db)
        print(f"[Kuzu] Connected to {self.db_path}")
    
    def _initialize_schema(self):
        """初始化数据库 Schema"""
        # 节点表定义
        node_tables = [
            """
            CREATE NODE TABLE IF NOT EXISTS AgentSession (
                id STRING PRIMARY KEY,
                name STRING,
                workdir STRING,
                model STRING,
                systemPrompt STRING,
                status STRING,
                startedAt TIMESTAMP,
                endedAt TIMESTAMP,
                maxTokens INT64,
                totalSteps INT64,
                totalToolCalls INT64,
                metadata STRING
            )
            """,
            """
            CREATE NODE TABLE IF NOT EXISTS ExecutionStep (
                id STRING PRIMARY KEY,
                stepNumber INT64,
                type STRING,
                status STRING,
                startedAt TIMESTAMP,
                endedAt TIMESTAMP,
                durationMs INT64,
                tokenCount INT64,
                finishReason STRING,
                metadata STRING
            )
            """,
            """
            CREATE NODE TABLE IF NOT EXISTS ToolCall (
                id STRING PRIMARY KEY,
                name STRING,
                arguments STRING,
                output STRING,
                outputPreview STRING,
                status STRING,
                errorMessage STRING,
                startedAt TIMESTAMP,
                endedAt TIMESTAMP,
                durationMs INT64
            )
            """,
            """
            CREATE NODE TABLE IF NOT EXISTS Message (
                id STRING PRIMARY KEY,
                role STRING,
                content STRING,
                contentPreview STRING,
                toolCalls STRING,
                tokenCount INT64,
                createdAt TIMESTAMP,
                compressionRef STRING
            )
            """,
            """
            CREATE NODE TABLE IF NOT EXISTS Task (
                id STRING PRIMARY KEY,
                taskId INT64,
                subject STRING,
                description STRING,
                status STRING,
                owner STRING,
                createdAt TIMESTAMP,
                updatedAt TIMESTAMP,
                completedAt TIMESTAMP
            )
            """,
            """
            CREATE NODE TABLE IF NOT EXISTS Todo (
                id STRING PRIMARY KEY,
                itemId STRING,
                text STRING,
                status STRING,
                updatedAt TIMESTAMP
            )
            """,
            """
            CREATE NODE TABLE IF NOT EXISTS Skill (
                id STRING PRIMARY KEY,
                name STRING,
                description STRING,
                tags STRING,
                body STRING,
                filePath STRING
            )
            """,
            """
            CREATE NODE TABLE IF NOT EXISTS Teammate (
                id STRING PRIMARY KEY,
                name STRING,
                role STRING,
                status STRING,
                prompt STRING,
                threadId STRING
            )
            """,
            """
            CREATE NODE TABLE IF NOT EXISTS BackgroundJob (
                id STRING PRIMARY KEY,
                taskId STRING,
                command STRING,
                status STRING,
                result STRING,
                startedAt TIMESTAMP,
                endedAt TIMESTAMP
            )
            """,
            """
            CREATE NODE TABLE IF NOT EXISTS SubagentRun (
                id STRING PRIMARY KEY,
                prompt STRING,
                agentType STRING,
                maxRounds INT64,
                actualRounds INT64,
                status STRING,
                summary STRING,
                startedAt TIMESTAMP,
                endedAt TIMESTAMP
            )
            """,
            """
            CREATE NODE TABLE IF NOT EXISTS Artifact (
                id STRING PRIMARY KEY,
                type STRING,
                name STRING,
                filePath STRING,
                contentPreview STRING,
                sizeBytes INT64,
                createdAt TIMESTAMP
            )
            """,
            """
            CREATE NODE TABLE IF NOT EXISTS Compression (
                id STRING PRIMARY KEY,
                type STRING,
                transcriptPath STRING,
                summary STRING,
                originalTokens INT64,
                compressedTokens INT64,
                createdAt TIMESTAMP
            )
            """,
        ]
        
        # 关系表定义
        rel_tables = [
            "CREATE REL TABLE IF NOT EXISTS HAS_STEP (FROM AgentSession TO ExecutionStep, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS NEXT_STEP (FROM ExecutionStep TO ExecutionStep, ONE_ONE)",
            "CREATE REL TABLE IF NOT EXISTS CALLS_TOOL (FROM ExecutionStep TO ToolCall, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS PRODUCES (FROM ToolCall TO Message, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS HAS_MESSAGE (FROM ExecutionStep TO Message, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS IN_STATE (FROM AgentSession TO ExecutionStep, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS DEPENDS_ON (FROM Task TO Task, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS HAS_TASK (FROM AgentSession TO Task, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS HAS_TODO (FROM AgentSession TO Todo, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS USES_SKILL (FROM ExecutionStep TO Skill, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS HAS_TEAMMEMBER (FROM AgentSession TO Teammate, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS SENDS_MESSAGE (FROM Teammate TO Teammate, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS TRIGGERS_COMPRESSION (FROM ExecutionStep TO Compression, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS SPAWNS_SUBAGENT (FROM ExecutionStep TO SubagentRun, MANY_MANY)",
            "CREATE REL TABLE IF NOT EXISTS CREATES_ARTIFACT (FROM ToolCall TO Artifact, MANY_MANY)",
        ]
        
        # 执行创建语句
        for ddl in node_tables + rel_tables:
            try:
                self._conn.execute(ddl)
            except Exception as e:
                # 表已存在时忽略错误
                if "already exists" not in str(e).lower():
                    print(f"[Kuzu] Schema warning: {e}")
        
        print("[Kuzu] Schema initialized")
    
    @property
    def connection(self) -> kuzu.Connection:
        """获取数据库连接"""
        if self._conn is None:
            raise RuntimeError("Database not connected")
        return self._conn
    
    def execute(self, query: str, parameters: Optional[dict] = None):
        """执行 Cypher 查询"""
        try:
            result = self._conn.execute(query, parameters or {})
            return result
        except Exception as e:
            print(f"[Kuzu] Query error: {e}")
            print(f"[Kuzu] Query: {query[:200]}...")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
        if self._db:
            self._db.close()
            self._db = None
        KuzuDatabase._instance = None
        print("[Kuzu] Connection closed")


# 全局数据库实例
_db_instance: Optional[KuzuDatabase] = None


def get_db() -> KuzuDatabase:
    """获取数据库实例（单例模式）"""
    global _db_instance
    if _db_instance is None:
        _db_instance = KuzuDatabase()
    return _db_instance
