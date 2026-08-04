@echo off
chcp 65001 > nul
title AI Creator Studio - 前端服务
echo ========================================
echo  AI Creator Studio 前端服务
echo ========================================
echo.
echo 启动中...
cd /d "%~dp0"
python -m http.server 8000
