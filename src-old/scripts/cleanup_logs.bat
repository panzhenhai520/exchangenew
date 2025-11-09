@echo off
REM ExchangeOK 日志清理批处理脚本
REM 可以手动运行或配置为Windows定时任务

echo ================================
echo ExchangeOK 日志清理工具
echo ================================
echo.

REM 切换到脚本所在目录的上级目录（src目录）
cd /d "%~dp0\.."

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    echo 请确保Python已安装并添加到PATH环境变量中
    pause
    exit /b 1
)

REM 运行日志清理脚本
echo 正在运行日志清理...
python scripts/log_cleanup.py

REM 检查执行结果
if errorlevel 1 (
    echo.
    echo 日志清理失败，请检查错误信息
    pause
    exit /b 1
) else (
    echo.
    echo 日志清理完成
)

REM 显示当前日志状态
echo.
echo 当前日志状态:
python utils/log_manager.py --stats

echo.
echo 按任意键退出...
pause >nul 