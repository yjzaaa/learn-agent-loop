#!/usr/bin/env python3
"""
AgentCore 输入框测试脚本
测试选择会话后在输入框输入内容
"""

import time
from playwright.sync_api import sync_playwright

TEST_URL = "http://localhost:3000/agentcore"

print("=" * 60)
print("AgentCore 输入框测试")
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
    time.sleep(3)
    
    # 截图 - 初始状态
    print("[4] 初始状态截图...")
    page.screenshot(path='test1_initial.png')
    
    # 点击 Session 1
    print("[5] 点击 'Session 1' 选择会话...")
    try:
        session_btn = page.locator('text=Session 1').first
        if session_btn.is_visible():
            session_btn.click()
            print("    ✓ 已点击 Session 1")
            time.sleep(2)
        else:
            print("    ✗ 未找到 Session 1")
    except Exception as e:
        print(f"    ✗ 点击失败: {e}")
    
    # 截图 - 选择会话后
    print("[6] 选择会话后截图...")
    page.screenshot(path='test2_after_select.png')
    
    # 尝试在输入框输入
    print("[7] 尝试在输入框输入...")
    try:
        # 查找输入框
        input_box = page.locator('input[placeholder*="query" i]').first
        
        if input_box.is_visible():
            # 检查是否禁用
            is_disabled = input_box.is_disabled()
            print(f"    输入框是否禁用: {is_disabled}")
            
            if not is_disabled:
                input_box.click()
                input_box.fill("List all files in current directory")
                print("    ✓ 已输入: List all files in current directory")
                time.sleep(1)
            else:
                print("    ✗ 输入框被禁用，无法输入")
        else:
            print("    ✗ 未找到输入框")
            
            # 尝试其他选择器
            input_box2 = page.locator('header input[type="text"]').first
            if input_box2.is_visible():
                print("    找到备选输入框")
                input_box2.click()
                input_box2.fill("Test query")
                print("    ✓ 已输入测试内容")
    except Exception as e:
        print(f"    ✗ 输入失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 截图 - 输入后
    print("[8] 输入后截图...")
    page.screenshot(path='test3_after_input.png')
    
    # 尝试点击 Run
    print("[9] 尝试点击 Run 按钮...")
    try:
        run_btn = page.locator('button:has-text("Run")').first
        if run_btn.is_visible() and run_btn.is_enabled():
            run_btn.click()
            print("    ✓ 已点击 Run")
            time.sleep(3)
        else:
            print(f"    ✗ Run 按钮不可点击 (visible: {run_btn.is_visible()}, enabled: {run_btn.is_enabled()})")
    except Exception as e:
        print(f"    ✗ 点击 Run 失败: {e}")
    
    # 最终截图
    print("[10] 最终状态截图...")
    page.screenshot(path='test4_final.png', full_page=True)
    
    print("\n[11] 保持浏览器打开 5 秒...")
    time.sleep(5)
    
    browser.close()
    print("\n[12] 浏览器已关闭")

print("=" * 60)
print("测试完成！查看截图:")
print("  - test1_initial.png (初始状态)")
print("  - test2_after_select.png (选择会话后)")
print("  - test3_after_input.png (输入后)")
print("  - test4_final.png (最终状态)")
print("=" * 60)
