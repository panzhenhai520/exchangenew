@echo off
chcp 65001 >nul
echo 🔍 ExchangeOK 日志模式切换工具
echo.

if "%1"=="debug" (
    echo 🔍 切换到调试模式...
    set LOG_MODE=debug
    echo 📝 日志级别: DEBUG
    echo 💻 控制台级别: INFO  
    echo 📄 文件级别: DEBUG
    echo.
    echo ✅ 调试模式已启用，请重启服务以生效
    goto :end
)

if "%1"=="production" (
    echo 🚀 切换到生产模式...
    set LOG_MODE=production
    echo 📝 日志级别: INFO
    echo 💻 控制台级别: WARNING
    echo 📄 文件级别: INFO
    echo.
    echo ✅ 生产模式已启用，请重启服务以生效
    goto :end
)

if "%1"=="status" (
    echo 📊 当前日志模式: %LOG_MODE%
    if "%LOG_MODE%"=="" echo 📊 当前日志模式: DEBUG (默认)
    goto :end
)

echo 使用方法:
echo   switch_log_mode.bat debug      # 切换到调试模式
echo   switch_log_mode.bat production # 切换到生产模式  
echo   switch_log_mode.bat status     # 显示当前模式
echo.
echo 注意: 切换模式后需要重启服务才能生效

:end
pause 