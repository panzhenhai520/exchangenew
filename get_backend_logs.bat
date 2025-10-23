@echo off
echo ======================================
echo 请在后端终端窗口执行以下步骤:
echo ======================================
echo.
echo 1. 打开运行 python src/main.py 的终端窗口
echo.
echo 2. 在浏览器中点击 "测试汇率API" 按钮
echo.
echo 3. 立即查看后端终端，应该会出现类似这样的日志:
echo.
echo    ========== [token_required] 收到请求 ==========
echo    [token_required] 请求路径: /api/rates/available_currencies
echo    [token_required] 请求方法: GET
echo    [token_required] 请求头: Authorization = Bearer eyJ0...
echo    ...更多日志...
echo.
echo 4. 复制从 "========== [token_required]" 开始
echo    到结束的所有内容
echo.
echo 5. 粘贴给我查看
echo.
echo ======================================
echo.
echo 如果后端窗口 **没有显示任何 [token_required] 日志**:
echo.
echo 可能原因:
echo   - 后端服务实际上没有重启
echo   - 请求没有到达后端
echo   - auth_service.py 文件加载失败
echo.
echo 请告诉我后端窗口的最后 20 行内容!
echo.
echo ======================================
pause
