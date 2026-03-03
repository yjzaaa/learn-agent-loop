import { test, expect } from '@playwright/test';

/**
 * AgentCore E2E Tests
 * 
 * 自动化测试 AgentCore 功能
 */

test.describe('AgentCore Dashboard', () => {
  
  test.beforeEach(async ({ page }) => {
    // 访问 AgentCore 页面
    await page.goto('/agentcore');
    
    // 等待页面加载完成
    await page.waitForSelector('text=AgentCore', { timeout: 10000 });
  });

  test('should display dashboard layout', async ({ page }) => {
    // 验证页面标题
    await expect(page.locator('text=AgentCore').first()).toBeVisible();
    
    // 验证左侧边栏
    await expect(page.locator('text=Sessions')).toBeVisible();
    
    // 验证状态栏
    await expect(page.locator('text=AgentCore v0.1.0')).toBeVisible();
    
    // 验证连接状态
    await expect(page.locator('text=Offline').or(page.locator('text=Live'))).toBeVisible();
  });

  test('should create new session', async ({ page }) => {
    // 点击 New Session 按钮
    const sessionSelector = page.locator('button', { hasText: /Select Session|New Session/ }).first();
    await sessionSelector.click();
    
    // 点击 New Session
    await page.click('text=New Session');
    
    // 等待弹窗出现
    await expect(page.locator('text=Create Session').first()).toBeVisible();
    
    // 输入会话名称
    await page.fill('input[placeholder="Session name"]', 'Test Session');
    
    // 点击 Create 按钮
    await page.click('button:has-text("Create")');
    
    // 验证会话已创建
    await expect(page.locator('text=Test Session').first()).toBeVisible({ timeout: 5000 });
  });

  test('should display execution steps', async ({ page }) => {
    // 验证执行步骤区域存在
    await expect(page.locator('text=Execution Steps').or(page.locator('text=Welcome to AgentCore'))).toBeVisible();
  });

  test('should switch between tabs', async ({ page }) => {
    // 创建会话后切换到 Details 标签
    await expect(page.locator('button:has-text("Details")')).toBeVisible();
    
    // 点击 Tools 标签
    await page.click('button:has-text("Tools")');
    await expect(page.locator('text=No tool calls yet')).toBeVisible();
    
    // 点击 Chat 标签
    await page.click('button:has-text("Chat")');
    await expect(page.locator('text=Chat functionality coming soon')).toBeVisible();
  });

  test('should show connection status', async ({ page }) => {
    // 验证连接状态指示器
    const statusIndicator = page.locator('[class*="rounded-full"]').filter({ hasText: '' }).first();
    await expect(statusIndicator).toBeVisible();
  });

  test('should have query input', async ({ page }) => {
    // 验证查询输入框
    const queryInput = page.locator('input[placeholder="Enter your query..."]');
    await expect(queryInput).toBeVisible();
    
    // 验证 Run 按钮
    const runButton = page.locator('button:has-text("Run")');
    await expect(runButton).toBeVisible();
    await expect(runButton).toBeDisabled();
  });
});

test.describe('AgentCore Sessions', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/agentcore');
    await page.waitForSelector('text=AgentCore', { timeout: 10000 });
  });

  test('should list existing sessions', async ({ page }) => {
    // 打开会话下拉菜单
    const sessionSelector = page.locator('button', { hasText: /Select Session|Session/ }).first();
    await sessionSelector.click();
    
    // 验证会话列表区域存在
    await expect(page.locator('text=Sessions').first()).toBeVisible();
  });

  test('should create multiple sessions', async ({ page }) => {
    // 创建第一个会话
    await page.click('button', { hasText: /Select Session|Session/ });
    await page.click('text=New Session');
    await page.fill('input[placeholder="Session name"]', 'Session 1');
    await page.click('button:has-text("Create")');
    
    // 等待弹窗关闭
    await page.waitForTimeout(500);
    
    // 创建第二个会话
    await page.click('button', { hasText: /Session 1|Select Session/ });
    await page.click('text=New Session');
    await page.fill('input[placeholder="Session name"]', 'Session 2');
    await page.click('button:has-text("Create")');
    
    // 验证两个会话都存在
    await page.click('button', { hasText: /Session 2/ });
    await expect(page.locator('text=Session 1')).toBeVisible();
    await expect(page.locator('text=Session 2')).toBeVisible();
  });
});

test.describe('AgentCore Graph Visualization', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/agentcore');
    await page.waitForSelector('text=AgentCore', { timeout: 10000 });
  });

  test('should display welcome message when no session', async ({ page }) => {
    // 验证欢迎消息
    await expect(page.locator('text=Welcome to AgentCore')).toBeVisible();
    await expect(page.locator('text=Create a new session to start')).toBeVisible();
  });

  test('should show graph controls', async ({ page }) => {
    // 验证缩放控制按钮
    await expect(page.locator('button').filter({ has: page.locator('[data-lucide="zoom-in"]') })).toBeVisible();
    await expect(page.locator('button').filter({ has: page.locator('[data-lucide="zoom-out"]') })).toBeVisible();
    await expect(page.locator('button').filter({ has: page.locator('[data-lucide="maximize-2"]') })).toBeVisible();
  });
});

test.describe('AgentCore Responsive Design', () => {
  
  test('should adapt to mobile viewport', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/agentcore');
    
    // 验证页面仍然可以访问
    await expect(page.locator('text=AgentCore').first()).toBeVisible();
  });

  test('should adapt to tablet viewport', async ({ page }) => {
    // 设置平板视口
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/agentcore');
    
    // 验证页面布局
    await expect(page.locator('text=AgentCore').first()).toBeVisible();
    await expect(page.locator('text=Sessions').or(page.locator('text=Offline'))).toBeVisible();
  });
});
