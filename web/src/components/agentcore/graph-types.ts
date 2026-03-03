/**
 * 知识图谱类型定义
 * 参考: docs/agentcore-knowledge-graph-design.md
 */

export interface GraphNode {
  id: string;
  type: 'AgentSession' | 'ExecutionStep' | 'ToolCall' | 'Message' | 
        'Task' | 'Todo' | 'Skill' | 'Teammate' | 'BackgroundJob' | 
        'SubagentRun' | 'Artifact' | 'Compression' | 'AgentState';
  label: string;
  x?: number;
  y?: number;
  size?: number;
  color?: string;
  data: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: 'HAS_STEP' | 'NEXT_STEP' | 'CALLS_TOOL' | 'PRODUCES' | 
        'DEPENDS_ON' | 'HAS_TODO' | 'USES_SKILL' | 'HAS_TEAMMEMBER' |
        'SENDS_MESSAGE' | 'TRIGGERS_COMPRESSION' | 'SPAWNS_SUBAGENT' |
        'CREATES_ARTIFACT' | 'HAS_MESSAGE' | 'IN_STATE' | 'HAS_TASK';
  label?: string;
  color?: string;
}

export interface KnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// 节点颜色映射 (根据设计文档)
export const NODE_COLORS: Record<string, string> = {
  AgentSession: '#7c3aed',    // 紫色
  ExecutionStep: '#6366f1',   // 靛蓝
  ToolCall: '#10b981',        // 翠绿
  Message: '#3b82f6',         // 蓝色
  Task: '#f59e0b',            // 琥珀
  Todo: '#14b8a6',            // 青色
  Skill: '#ec4899',           // 粉色
  Teammate: '#8b5cf6',        // 紫罗兰
  BackgroundJob: '#f97316',   // 橙色
  SubagentRun: '#06b6d4',     // 青色
  Artifact: '#84cc16',        // 柠檬绿
  Compression: '#64748b',     // 灰色
  AgentState: '#94a3b8',      // 浅灰
};

// 节点形状映射
export const NODE_SHAPES: Record<string, 'circle' | 'square' | 'diamond' | 'hexagon' | 'rect'> = {
  AgentSession: 'circle',
  ExecutionStep: 'square',
  ToolCall: 'diamond',
  Message: 'circle',
  Task: 'hexagon',
  Todo: 'rect',
  Skill: 'rect',
  Teammate: 'circle',
  BackgroundJob: 'rect',
  SubagentRun: 'square',
  Artifact: 'rect',
  Compression: 'square',
  AgentState: 'circle',
};

// 边颜色映射
export const EDGE_COLORS: Record<string, string> = {
  HAS_STEP: '#5a5a70',
  NEXT_STEP: '#7c3aed',
  CALLS_TOOL: '#10b981',
  PRODUCES: '#3b82f6',
  DEPENDS_ON: '#f59e0b',
  HAS_TODO: '#14b8a6',
  USES_SKILL: '#ec4899',
  HAS_TEAMMEMBER: '#8b5cf6',
  SENDS_MESSAGE: '#06b6d4',
  TRIGGERS_COMPRESSION: '#64748b',
  SPAWNS_SUBAGENT: '#f97316',
  CREATES_ARTIFACT: '#84cc16',
  HAS_MESSAGE: '#3b82f6',
  IN_STATE: '#94a3b8',
  HAS_TASK: '#f59e0b',
};

// 生成模拟知识图谱数据
export function generateMockGraph(sessionId: string): KnowledgeGraph {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];

  // AgentSession 节点
  nodes.push({
    id: sessionId,
    type: 'AgentSession',
    label: 'Session',
    size: 20,
    color: NODE_COLORS.AgentSession,
    data: { name: 'Test Session', status: 'active' },
  });

  // ExecutionStep 节点
  for (let i = 1; i <= 5; i++) {
    const stepId = `${sessionId}:step_${i}`;
    nodes.push({
      id: stepId,
      type: 'ExecutionStep',
      label: `Step ${i}`,
      size: 15,
      color: NODE_COLORS.ExecutionStep,
      data: { stepNumber: i, type: i % 2 === 1 ? 'llm_call' : 'tool_execution' },
    });

    // HAS_STEP 关系
    edges.push({
      id: `${sessionId}-has-${stepId}`,
      source: sessionId,
      target: stepId,
      type: 'HAS_STEP',
      color: EDGE_COLORS.HAS_STEP,
    });

    // NEXT_STEP 关系
    if (i > 1) {
      const prevStepId = `${sessionId}:step_${i - 1}`;
      edges.push({
        id: `${prevStepId}-next-${stepId}`,
        source: prevStepId,
        target: stepId,
        type: 'NEXT_STEP',
        color: EDGE_COLORS.NEXT_STEP,
      });
    }

    // ToolCall 节点 (偶数步骤)
    if (i % 2 === 0) {
      const toolId = `${stepId}:tool_1`;
      nodes.push({
        id: toolId,
        type: 'ToolCall',
        label: 'bash',
        size: 12,
        color: NODE_COLORS.ToolCall,
        data: { name: 'bash', status: 'success' },
      });

      edges.push({
        id: `${stepId}-calls-${toolId}`,
        source: stepId,
        target: toolId,
        type: 'CALLS_TOOL',
        color: EDGE_COLORS.CALLS_TOOL,
      });

      // Message 节点
      const msgId = `${stepId}:msg_1`;
      nodes.push({
        id: msgId,
        type: 'Message',
        label: 'tool',
        size: 10,
        color: NODE_COLORS.Message,
        data: { role: 'tool' },
      });

      edges.push({
        id: `${stepId}-has-msg-${msgId}`,
        source: stepId,
        target: msgId,
        type: 'HAS_MESSAGE',
        color: EDGE_COLORS.HAS_MESSAGE,
      });
    }
  }

  // Todo 节点
  const todoId = `${sessionId}:todo_1`;
  nodes.push({
    id: todoId,
    type: 'Todo',
    label: 'Todo',
    size: 12,
    color: NODE_COLORS.Todo,
    data: { text: 'Fix login bug', status: 'completed' },
  });

  edges.push({
    id: `${sessionId}-has-todo-${todoId}`,
    source: sessionId,
    target: todoId,
    type: 'HAS_TODO',
    color: EDGE_COLORS.HAS_TODO,
  });

  return { nodes, edges };
}
