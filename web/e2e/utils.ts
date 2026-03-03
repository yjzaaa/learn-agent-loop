import { Page } from '@playwright/test';

/**
 * Test Utilities
 * 
 * 测试工具函数
 */

/**
 * 创建新会话
 */
export async function createSession(page: Page, name: string, workdir: string = './workspace') {
  // 打开会话选择器
  await page.click('button', { hasText: /Select Session|Session/ });
  
  // 点击 New Session
  await page.click('text=New Session');
  
  // 等待弹窗
  await page.waitForSelector('text=Create Session');
  
  // 填写表单
  await page.fill('input[placeholder="Session name"]', name);
  await page.fill('input[placeholder*="workdir"]', workdir);
  
  // 提交
  await page.click('button:has-text("Create")');
  
  // 等待弹窗关闭
  await page.waitForTimeout(500);
}

/**
 * 运行 Agent 查询
 */
export async function runAgentQuery(page: Page, query: string) {
  // 输入查询
  await page.fill('input[placeholder="Enter your query..."]', query);
  
  // 点击 Run
  await page.click('button:has-text("Run")');
  
  // 等待执行完成
  await page.waitForTimeout(2000);
}

/**
 * 获取当前会话名称
 */
export async function getCurrentSessionName(page: Page): Promise<string | null> {
  const sessionButton = page.locator('button[class*="Session"], button:has-text("Session")').first();
  const text = await sessionButton.textContent();
  return text;
}

/**
 * 等待步骤执行
 */
export async function waitForStep(page: Page, stepNumber: number, timeout: number = 10000) {
  await page.waitForSelector(`text=Step ${stepNumber}`, { timeout });
}

/**
 * 截图并保存
 */
export async function takeScreenshot(page: Page, name: string) {
  await page.screenshot({ 
    path: `./test-results/screenshots/${name}.png`,
    fullPage: true 
  });
}
