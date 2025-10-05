@echo off
title ExchangeOK 开发环境
echo ========================================
echo    ExchangeOK 外汇兑换系统开发环境
echo ========================================
echo.
echo 前端服务器: http://192.168.0.18:8080/
echo 后端API:   http://192.168.0.18:5001/
echo 本地访问:  http://localhost:8080/
echo.
echo 注意: 虽然控制台显示"Network: unavailable"
echo      但服务器实际工作正常，可以正常访问！
echo.
echo ========================================
echo 按任意键启动前端开发服务器...
pause >nul
echo.
echo 启动前端服务器...
start "ExchangeOK Frontend" cmd /k "npm run serve"
echo.
echo 等待3秒后启动后端服务器...
timeout /t 3 /nobreak >nul
echo.
echo 启动后端服务器...
start "ExchangeOK Backend" cmd /k "cd src ; python main.py"
echo.
echo ========================================
echo 开发环境启动完成！
echo.
echo 访问地址:
echo - 管理界面: http://192.168.0.18:8080/
echo - API接口:  http://192.168.0.18:5001/api
echo - 机顶盒:   http://192.168.0.18:5001/static/Show.html
echo ========================================
pause        
