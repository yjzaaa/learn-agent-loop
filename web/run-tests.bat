@echo off
chcp 65001
cls

echo ==========================================
echo AgentCore E2E Test Runner
echo ==========================================
echo.

:: 检查依赖
echo [1/4] Checking dependencies...
call npx playwright --version >nul 2>&1
if errorlevel 1 (
    echo Installing Playwright...
    call npm install --save-dev @playwright/test
)

:: 安装浏览器
echo.
echo [2/4] Installing browsers...
call npx playwright install chromium

:: 运行测试
echo.
echo [3/4] Running tests...
call npx playwright test --project=chromium

:: 显示报告
echo.
echo [4/4] Opening test report...
if exist test-results (
    echo Test completed! Opening report...
    call npx playwright show-report
) else (
    echo No test results found.
)

echo.
echo ==========================================
echo Test run completed!
echo ==========================================
pause
