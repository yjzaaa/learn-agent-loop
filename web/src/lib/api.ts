/**
 * API 客户端配置
 * 
 * 用于与后端 FastAPI 服务通信
 */

// API 基础 URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// 请求配置接口
interface RequestConfig extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

/**
 * 构建完整 URL
 */
function buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
  // 确保路径以 / 开头
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${API_BASE_URL}${normalizedPath}`);
  
  // 添加查询参数
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });
  }
  
  return url.toString();
}

/**
 * 处理 API 响应
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({
      message: `HTTP error! status: ${response.status}`,
    }));
    throw new Error(error.message || `HTTP error! status: ${response.status}`);
  }
  
  // 检查 Content-Type
  const contentType = response.headers.get("content-type");
  if (contentType?.includes("application/json")) {
    return response.json() as Promise<T>;
  }
  
  return response.text() as Promise<T>;
}

/**
 * GET 请求
 */
export async function get<T>(path: string, config: RequestConfig = {}): Promise<T> {
  const url = buildUrl(path, config.params);
  
  const response = await fetch(url, {
    ...config,
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...config.headers,
    },
  });
  
  return handleResponse<T>(response);
}

/**
 * POST 请求
 */
export async function post<T>(path: string, data?: unknown, config: RequestConfig = {}): Promise<T> {
  const url = buildUrl(path, config.params);
  
  const response = await fetch(url, {
    ...config,
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...config.headers,
    },
    body: data ? JSON.stringify(data) : undefined,
  });
  
  return handleResponse<T>(response);
}

/**
 * PUT 请求
 */
export async function put<T>(path: string, data?: unknown, config: RequestConfig = {}): Promise<T> {
  const url = buildUrl(path, config.params);
  
  const response = await fetch(url, {
    ...config,
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...config.headers,
    },
    body: data ? JSON.stringify(data) : undefined,
  });
  
  return handleResponse<T>(response);
}

/**
 * DELETE 请求
 */
export async function del<T>(path: string, config: RequestConfig = {}): Promise<T> {
  const url = buildUrl(path, config.params);
  
  const response = await fetch(url, {
    ...config,
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      ...config.headers,
    },
  });
  
  return handleResponse<T>(response);
}

// 导出 API 基础 URL 供其他模块使用
export { API_BASE_URL };
