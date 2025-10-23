@echo off
chcp 65001 > nul
echo ======================================================================
echo ExchangeOK Environment Configuration Tool
echo ======================================================================
echo.

python setup_environment.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo Configuration completed successfully!
    echo ======================================================================
    echo.
    echo Next steps:
    echo 1. Start backend: python src\main.py
    echo 2. Start frontend: npm run serve
    echo.
) else (
    echo.
    echo ======================================================================
    echo Configuration failed - please check the error messages above
    echo ======================================================================
)

pause