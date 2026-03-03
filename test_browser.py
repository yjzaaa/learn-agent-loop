#!/usr/bin/env python3
"""
AgentCore 浏览器测试脚本
使用本地已安装的 Chrome
"""

import time
from playwright.sync_api import sync_playwright

TEST_URL = "http://localhost:3000/agentcore"

print("=" * 60)
print("AgentCore 浏览器自动化测试")
print("=" * 60)

with sync_playwright() as p:
    print("\n[1] 启动 Chrome...")
    browser = p.chromium.launch(
        channel='chrome',
        headless=False,
        args=['--disable-blink-features=AutomationControlled']
    )
    
    print("[2] 创建新页面...")
    page = browser.new_page(viewport={'width': 1400, 'height': 900})
    
    print(f"[3] 访问 {TEST_URL}...")
    page.goto(TEST_URL)
    
    # 等待页面加载
    print("[4] 等待页面加载...")
    time.sleep(3)
    
    # 截图
    print("[5] 截图保存...")
    page.screenshot(path='agentcore_initial.png', full_page=True)
    
    # 检查页面元素
    print("[6] 检查页面元素...")
    
    # 尝试创建会话
    try:
        # 查找创建会话按钮
        create_btn = page.locator('button:has-text("New")')
        if create_btn.is_visible():
            print("    找到 'New Session' 按钮")
            create_btn.click()
            time.sleep(1)
            
            # 填写会话名称
            name_input = page.locator('input[placeholder*="name" i]')
            if name_input.is_visible():
                name_input.fill("Test Session")
                print("    填写会话名称: Test Session")
            
            # 确认创建
            confirm_btn = page.locator('button:has-text("Create")')
            if confirm_btn.is_visible():
                confirm_btn.click()
                print("    点击创建按钮")
                time.sleep(2)
    except Exception as e:
        print(f"    创建会话出错: {e}")
    
    # 最终截图
    print("[7] 最终状态截图...")
    page.screenshot(path='agentcore_final.png', full_page=True)
    
    print("\n[8] 测试完成！截图已保存:")
    print("    - agentcore_initial.png (初始页面)")
    print("    - agentcore_final.png (最终状态)")
    
    # 保持浏览器打开 10 秒供查看
    print("\n[9] 保持浏览器打开 10 秒...")
    time.sleep(10)
    
    browser.close()
    print("\n[10] 浏览器已关闭")

print("=" * 60)
print("测试结束")
print("=" * 60)
