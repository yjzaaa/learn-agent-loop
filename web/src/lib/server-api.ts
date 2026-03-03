/**
 * 服务端 API 调用
 * 
 * 用于 Next.js Server Components 中直接调用后端 API
 */

import { API_BASE_URL } from "./api";
import type {
  AgentVersion,
  VersionDiff,
  Scenario,
  VisualizationData,
  DocItem,
  HealthStatus,
} from "./api-service";

// 服务端基础 URL（使用容器名或直接 localhost）
const SERVER_API_URL = process.env.API_URL || "http://localhost:8000/api/v1";

interface ApiResponse<T> {
  status: "success" | "error";
  message: string;
  data?: T;
  request_id?: string;
}

/**
 * 服务端 GET 请求
 */
async function serverGet<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T | null> {
  try {
    const url = new URL(`${SERVER_API_URL}${path.startsWith("/") ? path : `/${path}`}`);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    
    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      // 禁用缓存以获取最新数据
      cache: "no-store",
    });
    
    if (!response.ok) {
      console.error(`API error: ${response.status} ${response.statusText}`);
      return null;
    }
    
    const result = await response.json() as ApiResponse<T>;
    return result.data || null;
  } catch (error) {
    console.error(`Failed to fetch ${path}:`, error);
    return null;
  }
}

/**
 * 服务端 POST 请求
 */
async function serverPost<T>(path: string, data?: unknown, params?: Record<string, string | number | boolean | undefined>): Promise<T | null> {
  try {
    const url = new URL(`${SERVER_API_URL}${path.startsWith("/") ? path : `/${path}`}`);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    
    const response = await fetch(url.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: data ? JSON.stringify(data) : undefined,
      cache: "no-store",
    });
    
    if (!response.ok) {
      console.error(`API error: ${response.status} ${response.statusText}`);
      return null;
    }
    
    const result = await response.json() as ApiResponse<T>;
    return result.data || null;
  } catch (error) {
    console.error(`Failed to post ${path}:`, error);
    return null;
  }
}

// ==================== 版本 API ====================

export async function getVersionsServer(layer?: string): Promise<AgentVersion[]> {
  try {
    const response = await fetch(`${SERVER_API_URL}/versions${layer ? `?layer=${layer}` : ""}`, {
      cache: "no-store",
    });
    if (!response.ok) return [];
    const result = await response.json() as ApiResponse<{ versions: AgentVersion[]; total: number }>;
    return result.versions || [];
  } catch {
    return [];
  }
}

export async function getVersionServer(versionId: string): Promise<AgentVersion | null> {
  return serverGet<AgentVersion>(`/versions/${versionId}`);
}

export async function getVersionSourceServer(versionId: string): Promise<{ filename: string; source: string; loc: number } | null> {
  return serverGet<{ filename: string; source: string; loc: number }>(`/versions/${versionId}/source`);
}

export async function getVersionDiffServer(versionId: string): Promise<VersionDiff | null> {
  return serverGet<VersionDiff>(`/versions/${versionId}/diff`);
}

export async function compareVersionsServer(fromVersion: string, toVersion: string): Promise<VersionDiff | null> {
  return serverPost<VersionDiff>("/versions/compare", null, { from_version: fromVersion, to_version: toVersion });
}

export async function getRelatedVersionsServer(versionId: string): Promise<{
  current: AgentVersion | null;
  previous: AgentVersion | null;
  next: AgentVersion | null;
}> {
  const result = await serverGet<{
    current: AgentVersion;
    previous: AgentVersion | null;
    next: AgentVersion | null;
  }>(`/versions/${versionId}/related`);
  
  return result || { current: null, previous: null, next: null };
}

// ==================== 场景 API ====================

export async function getScenarioByVersionServer(versionId: string): Promise<Scenario | null> {
  return serverGet<Scenario>(`/scenarios/by-version/${versionId}`);
}

// ==================== 可视化 API ====================

export async function getVisualizationServer(versionId: string): Promise<VisualizationData | null> {
  return serverGet<VisualizationData>(`/visualizations/${versionId}`);
}

// ==================== 文档 API ====================

export async function getDocsServer(versionId?: string): Promise<DocItem[]> {
  try {
    const response = await fetch(`${SERVER_API_URL}/docs${versionId ? `?version_id=${versionId}` : ""}`, {
      cache: "no-store",
    });
    if (!response.ok) return [];
    const result = await response.json() as ApiResponse<{ docs: DocItem[]; total: number }>;
    return result.docs || [];
  } catch {
    return [];
  }
}

// ==================== 健康检查 ====================

export async function checkHealthServer(): Promise<HealthStatus | null> {
  return serverGet<HealthStatus>("/system/health");
}
