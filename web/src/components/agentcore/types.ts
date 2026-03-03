/**
 * Type Definitions
 */

export interface Session {
  id: string;
  name: string;
  workdir: string;
  model: string;
  status: string;
  started_at: string;
  ended_at?: string;
  total_steps: number;
  total_tool_calls: number;
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

export interface TimelineItem {
  step_number: number;
  type: string;
  status: string;
  started_at: string;
  duration_ms?: number;
  token_count?: number;
  finish_reason?: string;
  tool_count: number;
}
