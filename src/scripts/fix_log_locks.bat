@echo off
chcp 65001 >nul
echo ========================================
echo 日志文件占用问题解决工具
echo ========================================
echo.

cd /d "%~dp0.."

echo 正在检查日志文件占用情况...
python scripts/check_log_locks.py

echo.
echo 如果问题仍然存在，请尝试以下步骤：
echo 1. 关闭所有相关的Python进程
echo 2. 重启应用程序
echo 3. 检查是否有其他程序正在使用日志文件
echo.
pause 