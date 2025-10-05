@echo off
title 打开机顶盒展示页面
echo ========================================
echo    ExchangeOK 机顶盒展示页面
echo ========================================
echo.
echo 正在启动后端服务器...
echo.

REM 检查后端服务器是否已运行
netstat -an | findstr :5001 >nul
if %errorlevel% == 0 (
    echo ✅ 后端服务器已运行在端口5001
) else (
    echo ⚠️  后端服务器未运行，正在启动...
    start "ExchangeOK Backend" cmd /k "cd src && python main.py"
    echo 等待5秒让服务器启动...
    timeout /t 5 /nobreak >nul
)

echo.
echo 正在打开机顶盒展示页面...
echo 访问地址: http://192.168.13.56:5001/static/Show.html?branch=A005
echo.

REM 使用默认浏览器打开页面
start "" "http://192.168.13.56:5001/static/Show.html?branch=A005"

echo ✅ 页面已在浏览器中打开
echo.
echo 如果页面无法正常显示，请检查：
echo 1. 后端服务器是否正常运行
echo 2. 是否已发布面值汇率到机顶盒
echo 3. 网络连接是否正常
echo.
pause
