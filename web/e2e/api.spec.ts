import { test, expect } from '@playwright/test';

/**
 * AgentCore API E2E Tests
 * 
 * 测试后端 API 接口
 */

const API_BASE = 'http://localhost:8000/api/v1/agentcore';

test.describe('AgentCore API', () => {
  
  test('should get sessions list', async ({ request }) => {
    const response = await request.get(`${API_BASE}/sessions`);
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('sessions');
    expect(Array.isArray(data.sessions)).toBeTruthy();
  });

  test('should create and retrieve session', async ({ request }) => {
    // 创建会话
    const createResponse = await request.post(`${API_BASE}/sessions`, {
      data: {
        name: 'API Test Session',
        workdir: './test_workspace'
      }
    });
    
    expect(createResponse.ok()).toBeTruthy();
    
    const createData = await createResponse.json();
    expect(createData).toHaveProperty('session_id');
    expect(createData).toHaveProperty('name', 'API Test Session');
    
    const sessionId = createData.session_id;
    
    // 获取会话详情
    const getResponse = await request.get(`${API_BASE}/sessions/${sessionId}`);
    expect(getResponse.ok()).toBeTruthy();
    
    const getData = await getResponse.json();
    expect(getData).toHaveProperty('exists', true);
    expect(getData).toHaveProperty('session');
  });

  test('should return 404 for non-existent session', async ({ request }) => {
    const response = await request.get(`${API_BASE}/sessions/non-existent-id`);
    
    expect(response.status()).toBe(404);
  });

  test('should get session timeline', async ({ request }) => {
    // 先创建会话
    const createResponse = await request.post(`${API_BASE}/sessions`, {
      data: {
        name: 'Timeline Test',
        workdir: './test_workspace'
      }
    });
    
    const { session_id } = await createResponse.json();
    
    // 获取时间线
    const timelineResponse = await request.get(`${API_BASE}/sessions/${session_id}/timeline`);
    
    expect(timelineResponse.ok()).toBeTruthy();
    
    const data = await timelineResponse.json();
    expect(data).toHaveProperty('session_id', session_id);
    expect(data).toHaveProperty('timeline');
    expect(Array.isArray(data.timeline)).toBeTruthy();
  });

  test('should get session graph', async ({ request }) => {
    // 先创建会话
    const createResponse = await request.post(`${API_BASE}/sessions`, {
      data: {
        name: 'Graph Test',
        workdir: './test_workspace'
      }
    });
    
    const { session_id } = await createResponse.json();
    
    // 获取图谱
    const graphResponse = await request.get(`${API_BASE}/sessions/${session_id}/graph`);
    
    expect(graphResponse.ok()).toBeTruthy();
    
    const data = await graphResponse.json();
    expect(data).toHaveProperty('session');
    expect(data).toHaveProperty('steps');
    expect(data).toHaveProperty('tool_calls');
  });
});
