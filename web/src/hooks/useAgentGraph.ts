"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import { KnowledgeGraph, GraphNode, NODE_COLORS, EDGE_COLORS } from "@/components/agentcore/graph-types";

// 动态导入 Sigma 相关库
let Sigma: typeof import("sigma").default;
let Graph: typeof import("graphology").default;
let FA2Layout: typeof import("graphology-layout-forceatlas2/worker").default;
let forceAtlas2: typeof import("graphology-layout-forceatlas2").default;
let noverlap: typeof import("graphology-layout-noverlap").default;

// 异步加载 Sigma 库
async function loadSigmaLibraries() {
  if (typeof window === "undefined") return false;
  
  if (!Sigma) {
    const sigmaModule = await import("sigma");
    const graphologyModule = await import("graphology");
    const fa2Module = await import("graphology-layout-forceatlas2/worker");
    const fa2SettingsModule = await import("graphology-layout-forceatlas2");
    const noverlapModule = await import("graphology-layout-noverlap");
    
    Sigma = sigmaModule.default;
    Graph = graphologyModule.default;
    FA2Layout = fa2Module.default;
    forceAtlas2 = fa2SettingsModule.default;
    noverlap = noverlapModule.default;
  }
  return true;
}

// Sigma 节点属性接口
export interface SigmaNodeAttributes {
  x: number;
  y: number;
  size: number;
  color: string;
  label: string;
  nodeType: string;
  hidden?: boolean;
  zIndex?: number;
  highlighted?: boolean;
  mass?: number;
}

// Sigma 边属性接口
export interface SigmaEdgeAttributes {
  size: number;
  color: string;
  relationType: string;
  type?: string;
  curvature?: number;
  zIndex?: number;
}

interface UseAgentGraphOptions {
  onNodeClick?: (nodeId: string, nodeData: GraphNode) => void;
  onStageClick?: () => void;
}

interface UseAgentGraphReturn {
  containerRef: React.RefObject<HTMLDivElement | null>;
  setGraph: (graph: import("graphology").default<SigmaNodeAttributes, SigmaEdgeAttributes>) => void;
  zoomIn: () => void;
  zoomOut: () => void;
  resetZoom: () => void;
  focusNode: (nodeId: string) => void;
  isLayoutRunning: boolean;
  startLayout: () => void;
  stopLayout: () => void;
  selectedNode: string | null;
  setSelectedNode: (nodeId: string | null) => void;
  isReady: boolean;
}

// ForceAtlas2 设置
const getFA2Settings = (nodeCount: number) => {
  const isSmall = nodeCount < 50;
  const isMedium = nodeCount >= 50 && nodeCount < 200;
  
  return {
    gravity: isSmall ? 0.5 : isMedium ? 0.3 : 0.2,
    scalingRatio: isSmall ? 10 : isMedium ? 20 : 40,
    slowDown: isSmall ? 1 : isMedium ? 2 : 3,
    barnesHutOptimize: nodeCount > 100,
    barnesHutTheta: 0.8,
    strongGravityMode: false,
    outboundAttractionDistribution: true,
    linLogMode: false,
    adjustSizes: true,
    edgeWeightInfluence: 1,
  };
};

// 布局持续时间
const getLayoutDuration = (nodeCount: number): number => {
  if (nodeCount > 500) return 30000;
  if (nodeCount > 200) return 25000;
  if (nodeCount > 100) return 20000;
  return 15000;
};

// Noverlap 设置
const NOVERLAP_SETTINGS = {
  maxIterations: 20,
  ratio: 1.1,
  margin: 10,
  expansion: 1.05,
};

export function useAgentGraph(options: UseAgentGraphOptions = {}): UseAgentGraphReturn {
  const containerRef = useRef<HTMLDivElement>(null);
  const sigmaRef = useRef<import("sigma").default | null>(null);
  const graphRef = useRef<import("graphology").default<SigmaNodeAttributes, SigmaEdgeAttributes> | null>(null);
  const layoutRef = useRef<import("graphology-layout-forceatlas2/worker").default | null>(null);
  const selectedNodeRef = useRef<string | null>(null);
  const layoutTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isLayoutRunning, setIsLayoutRunning] = useState(false);
  const [selectedNode, setSelectedNodeState] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  const setSelectedNode = useCallback((nodeId: string | null) => {
    selectedNodeRef.current = nodeId;
    setSelectedNodeState(nodeId);
    
    const sigma = sigmaRef.current;
    if (!sigma) return;
    
    const camera = sigma.getCamera();
    const currentRatio = camera.ratio;
    camera.animate(
      { ratio: currentRatio * 1.0001 },
      { duration: 50 }
    );
    
    sigma.refresh();
  }, []);

  // 初始化 Sigma
  useEffect(() => {
    let isMounted = true;
    
    async function initSigma() {
      const loaded = await loadSigmaLibraries();
      if (!loaded || !isMounted || !containerRef.current) return;

      const graph = new Graph<SigmaNodeAttributes, SigmaEdgeAttributes>();
      graphRef.current = graph;

      const sigma = new Sigma(graph, containerRef.current, {
        renderLabels: true,
        labelFont: "JetBrains Mono, monospace",
        labelSize: 11,
        labelWeight: "500",
        labelColor: { color: "#e4e4ed" },
        labelRenderedSizeThreshold: 8,
        labelDensity: 0.1,
        labelGridCellSize: 70,
        
        defaultNodeColor: "#6b7280",
        defaultEdgeColor: "#2a2a3a",
        
        defaultEdgeType: "line",
        
        minCameraRatio: 0.002,
        maxCameraRatio: 50,
        hideEdgesOnMove: true,
        zIndex: true,
        
        nodeReducer: (node, data) => {
          const res = { ...data };
          
          if (data.hidden) {
            res.hidden = true;
            return res;
          }
          
          const currentSelected = selectedNodeRef.current;
          
          if (currentSelected) {
            const graph = graphRef.current;
            if (graph) {
              const isSelected = node === currentSelected;
              const isNeighbor = graph.hasEdge(node, currentSelected) || graph.hasEdge(currentSelected, node);
              
              if (isSelected) {
                res.color = data.color;
                res.size = (data.size || 8) * 1.5;
                res.zIndex = 2;
                res.highlighted = true;
              } else if (isNeighbor) {
                res.color = data.color;
                res.size = (data.size || 8) * 1.2;
                res.zIndex = 1;
              } else {
                res.color = dimColor(data.color, 0.3);
                res.size = (data.size || 8) * 0.7;
                res.zIndex = 0;
              }
            }
          }
          
          return res;
        },
        
        edgeReducer: (edge, data) => {
          const res = { ...data };
          
          const currentSelected = selectedNodeRef.current;
          
          if (currentSelected) {
            const graph = graphRef.current;
            if (graph) {
              const [source, target] = graph.extremities(edge);
              const isConnected = source === currentSelected || target === currentSelected;
              
              if (isConnected) {
                res.size = Math.max(2, (data.size || 1) * 2);
                res.zIndex = 2;
              } else {
                res.color = dimColor(data.color, 0.2);
                res.size = 0.5;
                res.zIndex = 0;
              }
            }
          }
          
          return res;
        },
      });

      sigmaRef.current = sigma;

      sigma.on("clickNode", ({ node }) => {
        setSelectedNode(node);
        const graph = graphRef.current;
        if (graph && options.onNodeClick) {
          const nodeData = graph.getNodeAttributes(node) as unknown as GraphNode;
          options.onNodeClick(node, nodeData);
        }
      });

      sigma.on("clickStage", () => {
        setSelectedNode(null);
        options.onStageClick?.();
      });

      sigma.on("enterNode", () => {
        if (containerRef.current) {
          containerRef.current.style.cursor = "pointer";
        }
      });

      sigma.on("leaveNode", () => {
        if (containerRef.current) {
          containerRef.current.style.cursor = "grab";
        }
      });

      setIsReady(true);
    }

    initSigma();

    return () => {
      isMounted = false;
      if (layoutTimeoutRef.current) {
        clearTimeout(layoutTimeoutRef.current);
      }
      layoutRef.current?.kill();
      sigmaRef.current?.kill();
      sigmaRef.current = null;
      graphRef.current = null;
    };
  }, []);

  // 运行布局
  const runLayout = useCallback((graph: import("graphology").default<SigmaNodeAttributes, SigmaEdgeAttributes>) => {
    const nodeCount = graph.order;
    if (nodeCount === 0) return;

    if (layoutRef.current) {
      layoutRef.current.kill();
      layoutRef.current = null;
    }
    if (layoutTimeoutRef.current) {
      clearTimeout(layoutTimeoutRef.current);
      layoutTimeoutRef.current = null;
    }

    const inferredSettings = forceAtlas2.inferSettings(graph);
    const customSettings = getFA2Settings(nodeCount);
    const settings = { ...inferredSettings, ...customSettings };
    
    const layout = new FA2Layout(graph, { settings });
    
    layoutRef.current = layout;
    layout.start();
    setIsLayoutRunning(true);

    const duration = getLayoutDuration(nodeCount);
    
    layoutTimeoutRef.current = setTimeout(() => {
      if (layoutRef.current) {
        layoutRef.current.stop();
        layoutRef.current = null;
        
        noverlap.assign(graph, NOVERLAP_SETTINGS);
        sigmaRef.current?.refresh();
        
        setIsLayoutRunning(false);
      }
    }, duration);
  }, []);

  const setGraph = useCallback((newGraph: import("graphology").default<SigmaNodeAttributes, SigmaEdgeAttributes>) => {
    const sigma = sigmaRef.current;
    if (!sigma) return;

    if (layoutRef.current) {
      layoutRef.current.kill();
      layoutRef.current = null;
    }
    if (layoutTimeoutRef.current) {
      clearTimeout(layoutTimeoutRef.current);
      layoutTimeoutRef.current = null;
    }

    graphRef.current = newGraph;
    sigma.setGraph(newGraph);
    setSelectedNode(null);

    runLayout(newGraph);
    sigma.getCamera().animatedReset({ duration: 500 });
  }, [runLayout, setSelectedNode]);

  const focusNode = useCallback((nodeId: string) => {
    const sigma = sigmaRef.current;
    const graph = graphRef.current;
    if (!sigma || !graph || !graph.hasNode(nodeId)) return;

    const alreadySelected = selectedNodeRef.current === nodeId;
    selectedNodeRef.current = nodeId;
    setSelectedNodeState(nodeId);
    
    if (!alreadySelected) {
      const nodeAttrs = graph.getNodeAttributes(nodeId);
      sigma.getCamera().animate(
        { x: nodeAttrs.x, y: nodeAttrs.y, ratio: 0.5 },
        { duration: 400 }
      );
    }
    
    sigma.refresh();
  }, []);

  const zoomIn = useCallback(() => {
    sigmaRef.current?.getCamera().animatedZoom({ duration: 200 });
  }, []);

  const zoomOut = useCallback(() => {
    sigmaRef.current?.getCamera().animatedUnzoom({ duration: 200 });
  }, []);

  const resetZoom = useCallback(() => {
    sigmaRef.current?.getCamera().animatedReset({ duration: 300 });
    setSelectedNode(null);
  }, [setSelectedNode]);

  const startLayout = useCallback(() => {
    const graph = graphRef.current;
    if (!graph || graph.order === 0) return;
    runLayout(graph);
  }, [runLayout]);

  const stopLayout = useCallback(() => {
    if (layoutTimeoutRef.current) {
      clearTimeout(layoutTimeoutRef.current);
      layoutTimeoutRef.current = null;
    }
    if (layoutRef.current) {
      layoutRef.current.stop();
      layoutRef.current = null;
      
      const graph = graphRef.current;
      if (graph) {
        noverlap.assign(graph, NOVERLAP_SETTINGS);
        sigmaRef.current?.refresh();
      }
      
      setIsLayoutRunning(false);
    }
  }, []);

  return {
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
  };
}

// 辅助函数：变暗颜色
function dimColor(hex: string, amount: number): string {
  const rgb = hexToRgb(hex);
  const darkBg = { r: 18, g: 18, b: 28 };
  return rgbToHex(
    Math.round(darkBg.r + (rgb.r - darkBg.r) * amount),
    Math.round(darkBg.g + (rgb.g - darkBg.g) * amount),
    Math.round(darkBg.b + (rgb.b - darkBg.b) * amount)
  );
}

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : { r: 100, g: 100, b: 100 };
}

function rgbToHex(r: number, g: number, b: number): string {
  return "#" + [r, g, b].map(x => {
    const hex = Math.max(0, Math.min(255, Math.round(x))).toString(16);
    return hex.length === 1 ? "0" + hex : hex;
  }).join("");
}
