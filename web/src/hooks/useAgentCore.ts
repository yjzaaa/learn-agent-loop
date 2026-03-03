"use client";

/**
 * useAgentCore Hook
 * 
 * AgentCore 状态管理 Hook
 */

import { useState, useCallback, useEffect, useRef } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface Session {
  id: string;
  name: string;
  workdir: string;
  model: string;
  status: string;
  started_at: string;
  total_steps: number;
}

export interface ExecutionStep {
  step_number: number;
  type: string;
  status: string;
  started_at: string;
  duration_ms?: number;
  token_count?: number;
  finish_reason?: string;
  tool_count: number;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: string;
  output?: string;
  status: string;
  duration_ms?: number;
}

export function useAgentCore() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [steps, setSteps] = useState<ExecutionStep[]>([]);
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  // 获取会话列表
  const fetchSessions = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/agentcore/sessions`);
      if (!response.ok) throw new Error("Failed to fetch sessions");
      const data = await response.json();
      setSessions(data.sessions || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  }, []);

  // 获取会话详情
  const fetchSessionDetails = useCallback(async (sessionId: string) => {
    setIsLoading(true);
    try {
      // 并行获取时间线和图谱
      const [timelineRes, graphRes] = await Promise.all([
        fetch(`${API_BASE_URL}/agentcore/sessions/${sessionId}/timeline`),
        fetch(`${API_BASE_URL}/agentcore/sessions/${sessionId}/graph`),
      ]);

      if (timelineRes.ok) {
        const timelineData = await timelineRes.json();
        setSteps(timelineData.timeline || []);
      }

      if (graphRes.ok) {
        const graphData = await graphRes.json();
        setToolCalls(graphData.tool_calls || []);
      }

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 创建会话
  const createSession = useCallback(async (name: string, workdir: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/agentcore/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, workdir }),
      });

      if (!response.ok) throw new Error("Failed to create session");
      
      const data = await response.json();
      await fetchSessions();
      
      // 自动选中新会话
      const newSession: Session = {
        id: data.session_id,
        name: data.name,
        workdir: data.workdir,
        model: "gpt-4",
        status: "active",
        started_at: data.created_at,
        total_steps: 0,
      };
      
      setCurrentSession(newSession);
      connectWebSocket(data.session_id);
      return data.session_id;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      return null;
    }
  }, [fetchSessions]);

  // 运行 Agent
  const runAgent = useCallback(async (query: string) => {
    if (!currentSession) return;

    setIsLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/agentcore/sessions/${currentSession.id}/run`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query }),
        }
      );

      if (!response.ok) throw new Error("Failed to run agent");
      
      // 刷新数据
      await fetchSessionDetails(currentSession.id);
      await fetchSessions();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [currentSession, fetchSessionDetails, fetchSessions]);

  // 连接 WebSocket
  const connectWebSocket = useCallback((sessionId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }

    const wsUrl = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://');
    const ws = new WebSocket(`${wsUrl}/agentcore/ws/sessions/${sessionId}`);
    
    ws.onopen = () => {
      console.log("[WebSocket] Connected");
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("[WebSocket] Message:", data);
      
      // 处理实时事件
      if (data.type === "step_start" || data.type === "step_end") {
        // 刷新会话详情
        fetchSessionDetails(sessionId);
      }
    };

    ws.onclose = () => {
      console.log("[WebSocket] Disconnected");
      setIsConnected(false);
      
      // 重连
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket(sessionId);
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error("[WebSocket] Error:", error);
    };

    wsRef.current = ws;
  }, [fetchSessionDetails]);

  // 断开 WebSocket
  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // 选择会话
  const selectSession = useCallback((session: Session) => {
    setCurrentSession(session);
    connectWebSocket(session.id);
    fetchSessionDetails(session.id);
  }, [connectWebSocket, fetchSessionDetails]);

  // 初始加载
  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // 清理
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, [disconnectWebSocket]);

  return {
    sessions,
    currentSession,
    steps,
    toolCalls,
    isLoading,
    error,
    isConnected,
    fetchSessions,
    fetchSessionDetails,
    createSession,
    runAgent,
    selectSession,
    disconnectWebSocket,
  };
}
