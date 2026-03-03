import { 
  KnowledgeGraph, 
  GraphNode, 
  GraphEdge, 
  NODE_COLORS, 
  EDGE_COLORS 
} from "@/components/agentcore/graph-types";
import { SigmaNodeAttributes, SigmaEdgeAttributes } from "@/hooks/useAgentGraph";

// 动态导入 Graphology
async function loadGraphology() {
  const { default: Graph } = await import("graphology");
  return Graph;
}

/**
 * 将知识图谱转换为 Graphology 图（用于 Sigma.js 渲染）
 */
export async function knowledgeGraphToGraphology(
  knowledgeGraph: KnowledgeGraph
): Promise<import("graphology").default<SigmaNodeAttributes, SigmaEdgeAttributes>> {
  const Graph = await loadGraphology();
  const graph = new Graph<SigmaNodeAttributes, SigmaEdgeAttributes>();
  const nodeCount = knowledgeGraph.nodes.length;
  
  // 节点基础大小
  const getNodeSize = (type: string): number => {
    switch (type) {
      case "AgentSession": return 20;
      case "ExecutionStep": return 15;
      case "ToolCall": return 12;
      case "Task": return 14;
      case "Teammate": return 13;
      default: return 10;
    }
  };

  // 节点质量（用于力导向布局）
  const getNodeMass = (type: string): number => {
    switch (type) {
      case "AgentSession": return 10;
      case "ExecutionStep": return 5;
      case "Task": return 4;
      default: return 2;
    }
  };

  // 使用简单的径向布局初始化节点位置
  const spread = Math.sqrt(nodeCount) * 30;
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));

  // 首先添加所有节点
  knowledgeGraph.nodes.forEach((node, index) => {
    const angle = index * goldenAngle;
    const radius = spread * Math.sqrt((index + 1) / Math.max(nodeCount, 1));
    
    // 添加一些随机扰动
    const jitter = spread * 0.1;
    const x = radius * Math.cos(angle) + (Math.random() - 0.5) * jitter;
    const y = radius * Math.sin(angle) + (Math.random() - 0.5) * jitter;

    const baseSize = getNodeSize(node.type);
    const color = node.color || NODE_COLORS[node.type] || "#6b7280";

    graph.addNode(node.id, {
      x,
      y,
      size: baseSize,
      color,
      label: node.label,
      nodeType: node.type,
      hidden: false,
      mass: getNodeMass(node.type),
    });
  });

  // 添加边
  const edgeBaseSize = nodeCount > 100 ? 0.5 : 1;
  
  knowledgeGraph.edges.forEach((edge) => {
    if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
      if (!graph.hasEdge(edge.source, edge.target)) {
        const color = edge.color || EDGE_COLORS[edge.type] || "#4a4a5a";
        
        graph.addEdge(edge.source, edge.target, {
          size: edgeBaseSize,
          color,
          relationType: edge.type,
          type: "line",
        });
      }
    }
  });

  return graph;
}

/**
 * 根据执行状态生成动态知识图谱
 */
export function generateExecutionGraph(
  sessionId: string,
  steps: Array<{
    step_number: number;
    type: string;
    status: string;
    tool_count: number;
  }>,
  toolCalls: Array<{
    id: string;
    name: string;
    status: string;
  }>
): KnowledgeGraph {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];

  // Session 节点
  nodes.push({
    id: sessionId,
    type: "AgentSession",
    label: "Session",
    size: 20,
    color: NODE_COLORS.AgentSession,
    data: { id: sessionId },
  });

  // 执行步骤节点
  steps.forEach((step, index) => {
    const stepId = `${sessionId}:step_${step.step_number}`;
    
    // 根据状态调整颜色
    let color = NODE_COLORS.ExecutionStep;
    if (step.status === "running") color = "#f59e0b"; // 琥珀色
    else if (step.status === "error") color = "#ef4444"; // 红色
    else if (step.status === "completed") color = "#10b981"; // 绿色

    nodes.push({
      id: stepId,
      type: "ExecutionStep",
      label: `Step ${step.step_number}`,
      size: 15,
      color,
      data: step,
    });

    // HAS_STEP 关系
    edges.push({
      id: `${sessionId}-has-${stepId}`,
      source: sessionId,
      target: stepId,
      type: "HAS_STEP",
      color: EDGE_COLORS.HAS_STEP,
    });

    // NEXT_STEP 关系
    if (index > 0) {
      const prevStepId = `${sessionId}:step_${steps[index - 1].step_number}`;
      edges.push({
        id: `${prevStepId}-next-${stepId}`,
        source: prevStepId,
        target: stepId,
        type: "NEXT_STEP",
        color: EDGE_COLORS.NEXT_STEP,
      });
    }
  });

  // 工具调用节点
  toolCalls.forEach((tool) => {
    const toolId = `${sessionId}:tool_${tool.id}`;
    
    let color = NODE_COLORS.ToolCall;
    if (tool.status === "running") color = "#f59e0b";
    else if (tool.status === "error") color = "#ef4444";
    else if (tool.status === "completed") color = "#10b981";

    nodes.push({
      id: toolId,
      type: "ToolCall",
      label: tool.name,
      size: 12,
      color,
      data: tool,
    });

    // 连接到最新的执行步骤
    if (steps.length > 0) {
      const lastStepId = `${sessionId}:step_${steps[steps.length - 1].step_number}`;
      edges.push({
        id: `${lastStepId}-calls-${toolId}`,
        source: lastStepId,
        target: toolId,
        type: "CALLS_TOOL",
        color: EDGE_COLORS.CALLS_TOOL,
      });
    }
  });

  return { nodes, edges };
}
