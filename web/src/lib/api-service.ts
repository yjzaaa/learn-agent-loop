/**
 * API 服务层
 * 
 * 封装具体的后端 API 调用
 */

import { get, post } from "./api";

// ==================== 类型定义 ====================

export interface AgentVersion {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  layer: string;
  prev_version: string | null;
  next_version: string | null;
  loc: number;
  filename: string;
  source: string;
  tools: string[];
  classes: string[];
  functions: string[];
}

export interface VersionDiff {
  from_version: string;
  to_version: string;
  loc_delta: number;
  new_tools: string[];
  new_classes: string[];
  new_functions: string[];
}

export interface ScenarioStep {
  step: number;
  title: string;
  description: string;
  code?: string;
  note?: string;
}

export interface Scenario {
  id: string;
  version_id: string;
  title: string;
  description: string;
  steps: ScenarioStep[];
}

export interface VisualizationNode {
  id: string;
  type: string;
  label: string;
  x: number;
  y: number;
  data?: Record<string, unknown>;
}

export interface VisualizationEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated: boolean;
}

export interface VisualizationState {
  step: number;
  title: string;
  description: string;
  active_nodes: string[];
  highlighted_edges: string[];
}

export interface VisualizationData {
  id: string;
  version_id: string;
  title: string;
  description: string;
  nodes: VisualizationNode[];
  edges: VisualizationEdge[];
  states: VisualizationState[];
}

export interface DocItem {
  id: string;
  version_id: string;
  title: string;
  content: string;
  category: string;
  order: number;
}

export interface HealthStatus {
  status: string;
  version: string;
  timestamp: string;
  uptime: number;
  environment: string;
}

// API 响应包装
interface ApiResponse<T> {
  status: "success" | "error";
  message: string;
  data?: T;
  request_id?: string;
}

// ==================== 版本 API ====================

/**
 * 获取所有版本列表
 */
export async function getVersions(layer?: string): Promise<AgentVersion[]> {
  const response = await get<ApiResponse<{ versions: AgentVersion[]; total: number }>>("/versions", {
    params: layer ? { layer } : undefined,
  });
  return response.versions || [];
}

/**
 * 获取版本时间线
 */
export async function getTimeline(): Promise<AgentVersion[]> {
  const response = await get<ApiResponse<{ versions: AgentVersion[]; total: number }>>("/versions/timeline");
  return response.versions || [];
}

/**
 * 获取单个版本详情
 */
export async function getVersion(versionId: string): Promise<AgentVersion | null> {
  try {
    const response = await get<ApiResponse<AgentVersion>>(`/versions/${versionId}`);
    return response.data || null;
  } catch {
    return null;
  }
}

/**
 * 获取版本源代码
 */
export async function getVersionSource(versionId: string): Promise<{ filename: string; source: string; loc: number } | null> {
  try {
    const response = await get<ApiResponse<{ version_id: string; filename: string; source: string; loc: number }>>(`/versions/${versionId}/source`);
    return response.data ? {
      filename: response.data.filename,
      source: response.data.source,
      loc: response.data.loc,
    } : null;
  } catch {
    return null;
  }
}

/**
 * 获取版本与上一版本的差异
 */
export async function getVersionDiff(versionId: string): Promise<VersionDiff | null> {
  try {
    const response = await get<ApiResponse<VersionDiff>>(`/versions/${versionId}/diff`);
    return response.data || null;
  } catch {
    return null;
  }
}

/**
 * 对比两个版本
 */
export async function compareVersions(fromVersion: string, toVersion: string): Promise<VersionDiff | null> {
  try {
    const response = await post<ApiResponse<VersionDiff>>("/versions/compare", null, {
      params: { from_version: fromVersion, to_version: toVersion },
    });
    return response.data || null;
  } catch {
    return null;
  }
}

/**
 * 获取相关版本（前一版本和后一版本）
 */
export async function getRelatedVersions(versionId: string): Promise<{
  current: AgentVersion | null;
  previous: AgentVersion | null;
  next: AgentVersion | null;
}> {
  try {
    const response = await get<ApiResponse<{
      current: AgentVersion;
      previous: AgentVersion | null;
      next: AgentVersion | null;
    }>>(`/versions/${versionId}/related`);
    return {
      current: response.data?.current || null,
      previous: response.data?.previous || null,
      next: response.data?.next || null,
    };
  } catch {
    return { current: null, previous: null, next: null };
  }
}

// ==================== 场景 API ====================

/**
 * 获取场景列表
 */
export async function getScenarios(versionId?: string): Promise<Scenario[]> {
  const response = await get<ApiResponse<{ scenarios: Scenario[]; total: number }>>("/scenarios", {
    params: versionId ? { version_id: versionId } : undefined,
  });
  return response.scenarios || [];
}

/**
 * 获取单个场景
 */
export async function getScenario(scenarioId: string): Promise<Scenario | null> {
  try {
    const response = await get<ApiResponse<Scenario>>(`/scenarios/${scenarioId}`);
    return response.data || null;
  } catch {
    return null;
  }
}

/**
 * 根据版本获取场景
 */
export async function getScenarioByVersion(versionId: string): Promise<Scenario | null> {
  try {
    const response = await get<ApiResponse<Scenario>>(`/scenarios/by-version/${versionId}`);
    return response.data || null;
  } catch {
    return null;
  }
}

// ==================== 可视化 API ====================

/**
 * 获取可视化数据
 */
export async function getVisualization(versionId: string): Promise<VisualizationData | null> {
  try {
    const response = await get<ApiResponse<VisualizationData>>(`/visualizations/${versionId}`);
    return response.data || null;
  } catch {
    return null;
  }
}

/**
 * 获取指定步骤的可视化状态
 */
export async function getVisualizationState(versionId: string, step: number): Promise<{
  step: number;
  state: VisualizationState;
  total_steps: number;
} | null> {
  try {
    const response = await get<ApiResponse<{
      step: number;
      state: VisualizationState;
      total_steps: number;
    }>>(`/visualizations/${versionId}/state/${step}`);
    return response.data || null;
  } catch {
    return null;
  }
}

// ==================== 文档 API ====================

/**
 * 获取文档列表
 */
export async function getDocs(versionId?: string, category?: string): Promise<DocItem[]> {
  const response = await get<ApiResponse<{ docs: DocItem[]; total: number }>>("/docs", {
    params: {
      ...(versionId && { version_id: versionId }),
      ...(category && { category }),
    },
  });
  return response.docs || [];
}

/**
 * 获取单个文档
 */
export async function getDoc(docId: string): Promise<DocItem | null> {
  try {
    const response = await get<ApiResponse<DocItem>>(`/docs/${docId}`);
    return response.data || null;
  } catch {
    return null;
  }
}

// ==================== 系统 API ====================

/**
 * 健康检查
 */
export async function checkHealth(): Promise<HealthStatus | null> {
  try {
    const response = await get<ApiResponse<HealthStatus>>("/system/health");
    return response.data || null;
  } catch {
    return null;
  }
}

/**
 * 获取系统信息
 */
export async function getSystemInfo(): Promise<{
  app_name: string;
  version: string;
  environment: string;
  debug: boolean;
} | null> {
  try {
    const response = await get<ApiResponse<{
      app_name: string;
      version: string;
      environment: string;
      debug: boolean;
    }>>("/system/info");
    return response.data || null;
  } catch {
    return null;
  }
}

/**
 * 获取系统统计
 */
export async function getSystemStats(): Promise<{
  versions: { total: number; by_layer: Record<string, number> };
  scenarios: { total: number };
  docs: { total: number };
  uptime_seconds: number;
} | null> {
  try {
    const response = await get<ApiResponse<{
      versions: { total: number; by_layer: Record<string, number> };
      scenarios: { total: number };
      docs: { total: number };
      uptime_seconds: number;
    }>>("/system/stats");
    return response.data || null;
  } catch {
    return null;
  }
}
