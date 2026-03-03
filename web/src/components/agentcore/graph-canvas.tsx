"use client";

import { useEffect, useCallback, useState } from "react";
import { ZoomIn, ZoomOut, Maximize2, Play, Pause, RotateCcw } from "lucide-react";
import { Session, ExecutionStep, ToolCall } from "./types";
import { useAgentGraph } from "@/hooks/useAgentGraph";
import { 
  knowledgeGraphToGraphology, 
  generateExecutionGraph 
} from "@/lib/agent-graph-adapter";
import { generateMockGraph, GraphNode } from "./graph-types";

interface GraphCanvasProps {
  session: Session | null;
  steps: ExecutionStep[];
  toolCalls: ToolCall[];
  selectedStep: ExecutionStep | null;
  onStepSelect: (step: ExecutionStep) => void;
  isLoading: boolean;
}

export function GraphCanvas({
  session,
  steps,
  toolCalls,
  selectedStep,
  onStepSelect,
  isLoading,
}: GraphCanvasProps) {
  const [isInitializing, setIsInitializing] = useState(true);

  const handleNodeClick = useCallback((nodeId: string, nodeData: GraphNode) => {
    // 如果点击的是执行步骤节点，触发选择
    if (nodeData.type === "ExecutionStep" && nodeData.data) {
      const stepData = nodeData.data as ExecutionStep;
      onStepSelect(stepData);
    }
  }, [onStepSelect]);

  const {
    containerRef,
    setGraph,
    zoomIn,
    zoomOut,
    resetZoom,
    focusNode,
    isLayoutRunning,
    startLayout,
    stopLayout,
    selectedNode,
    setSelectedNode,
    isReady,
  } = useAgentGraph({
    onNodeClick: handleNodeClick,
    onStageClick: () => setSelectedNode(null),
  });

  // 当数据变化时更新图谱
  useEffect(() => {
    if (!session || !isReady) return;

    async function updateGraph() {
      // 生成知识图谱数据
      const knowledgeGraph = generateExecutionGraph(
        session!.id,
        steps.map(s => ({
          step_number: s.step_number,
          type: s.type,
          status: s.status,
          tool_count: s.tool_count,
        })),
        toolCalls.map(t => ({
          id: t.id,
          name: t.name,
          status: t.status,
        }))
      );

      // 如果没有实际数据，使用模拟数据
      if (knowledgeGraph.nodes.length <= 1) {
        const mockGraph = generateMockGraph(session!.id);
        const sigmaGraph = await knowledgeGraphToGraphology(mockGraph);
        setGraph(sigmaGraph);
      } else {
        const sigmaGraph = await knowledgeGraphToGraphology(knowledgeGraph);
        setGraph(sigmaGraph);
      }
      setIsInitializing(false);
    }

    updateGraph();
  }, [session, steps, toolCalls, setGraph, isReady]);

  // 当选中步骤变化时，聚焦到对应节点
  useEffect(() => {
    if (selectedStep && session) {
      const stepId = `${session.id}:step_${selectedStep.step_number}`;
      focusNode(stepId);
    }
  }, [selectedStep, session, focusNode]);

  return (
    <div className="relative w-full h-full bg-void">
      {/* 背景渐变 */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute inset-0"
          style={{
            background: `
              radial-gradient(circle at 50% 50%, rgba(124, 58, 237, 0.03) 0%, transparent 70%),
              linear-gradient(to bottom, #06060a, #0a0a10)
            `,
          }}
        />
      </div>

      {/* Sigma 容器 */}
      <div
        ref={containerRef}
        className="sigma-container w-full h-full cursor-grab active:cursor-grabbing"
      />

      {/* 空状态提示 */}
      {!session && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <div className="text-4xl mb-4">🤖</div>
            <h2 className="text-xl font-semibold text-primary mb-2">
              Welcome to AgentCore
            </h2>
            <p className="text-sm text-muted max-w-md">
              Create a new session to start exploring the knowledge graph-based
              agent execution.
            </p>
          </div>
        </div>
      )}

      {/* 初始化中提示 */}
      {(isInitializing || !isReady) && session && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-muted">Initializing graph...</span>
          </div>
        </div>
      )}

      {/* 选中节点信息栏 */}
      {selectedNode && session && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 bg-accent/20 border border-accent/30 rounded-xl backdrop-blur-sm z-20 animate-fade-in">
          <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
          <span className="font-mono text-sm text-text-primary">
            {selectedNode}
          </span>
          <button
            onClick={() => setSelectedNode(null)}
            className="ml-2 px-2 py-0.5 text-xs text-text-secondary hover:text-text-primary hover:bg-white/10 rounded transition-colors"
          >
            Clear
          </button>
        </div>
      )}

      {/* 图控制按钮 - 右下角 */}
      <div className="absolute bottom-4 right-4 flex flex-col gap-1 z-10">
        <button
          onClick={zoomIn}
          className="w-9 h-9 flex items-center justify-center bg-elevated border border-border-subtle rounded-md text-text-secondary hover:bg-hover hover:text-text-primary transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={zoomOut}
          className="w-9 h-9 flex items-center justify-center bg-elevated border border-border-subtle rounded-md text-text-secondary hover:bg-hover hover:text-text-primary transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={resetZoom}
          className="w-9 h-9 flex items-center justify-center bg-elevated border border-border-subtle rounded-md text-text-secondary hover:bg-hover hover:text-text-primary transition-colors"
          title="Fit to Screen"
        >
          <Maximize2 className="w-4 h-4" />
        </button>

        {/* 分隔线 */}
        <div className="h-px bg-border-subtle my-1" />

        {/* 清除选择 */}
        {selectedNode && (
          <button
            onClick={() => setSelectedNode(null)}
            className="w-9 h-9 flex items-center justify-center bg-elevated border border-border-subtle rounded-md text-text-secondary hover:bg-hover hover:text-text-primary transition-colors"
            title="Clear Selection"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        )}

        {/* 分隔线 */}
        <div className="h-px bg-border-subtle my-1" />

        {/* 布局控制 */}
        <button
          onClick={isLayoutRunning ? stopLayout : startLayout}
          disabled={!isReady}
          className={`
            w-9 h-9 flex items-center justify-center border rounded-md transition-all
            ${isLayoutRunning
              ? "bg-accent border-accent text-white shadow-glow animate-pulse"
              : "bg-elevated border-border-subtle text-text-secondary hover:bg-hover hover:text-text-primary"
            }
            ${!isReady ? "opacity-50 cursor-not-allowed" : ""}
          `}
          title={isLayoutRunning ? "Stop Layout" : "Run Layout"}
        >
          {isLayoutRunning ? (
            <Pause className="w-4 h-4" />
          ) : (
            <Play className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* 布局运行指示器 */}
      {isLayoutRunning && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 px-3 py-1.5 bg-emerald-500/20 border border-emerald-500/30 rounded-full backdrop-blur-sm z-10 animate-fade-in">
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-ping" />
          <span className="text-xs text-emerald-400 font-medium">Layout optimizing...</span>
        </div>
      )}

      {/* 加载状态 */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-void/50 backdrop-blur-sm z-20">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-muted">Loading...</span>
          </div>
        </div>
      )}
    </div>
  );
}
