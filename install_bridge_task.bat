@echo off
REM BiliNote Bridge - 定时任务安装脚本
REM 以管理员身份运行此脚本

echo ========================================
echo  BiliNote Bridge 定时任务安装
echo ========================================
echo.

REM 设置 Python 路径和脚本路径
set PYTHON_PATH=D:\PYTHON\Project\BiliNote\backend\conda_env\python.exe
set SCRIPT_PATH=E:\Github_projet\BiliNote\bilinote_bridge.py

REM 检查 Python
if not exist "%PYTHON_PATH%" (
    echo [!] 未找到 Python: %PYTHON_PATH%
    echo     请修改本脚本中的 PYTHON_PATH 为你的实际路径
    echo     或用 where python 查找
    set /p PYTHON_PATH="请输入 Python 路径: "
)

REM 检查脚本
if not exist "%SCRIPT_PATH%" (
    echo [x] 未找到脚本: %SCRIPT_PATH%
    echo     请将 bilinote_bridge.py 复制到 E:\Github_projet\BiliNote\
    pause
    exit /b 1
)

echo [*] 创建定时任务...
schtasks /create ^
    /tn "BiliNote Bridge" ^
    /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
    /sc hourly ^
    /mo 1 ^
    /st 09:00 ^
    /du 24:00 ^
    /f

if %ERRORLEVEL% equ 0 (
    echo [✓] 定时任务创建成功！
    echo     每小时运行一次，扫描新链接并生成笔记
) else (
    echo [x] 创建失败，请以管理员身份运行
)

echo.
echo ========================================
echo  使用说明：
echo   1. 将 bilinote_bridge.py 复制到 E:\Github_projet\BiliNote\
echo   2. 在 E:\Github_projet\BiliNote\ 创建 pending_links.txt
echo   3. 从工作台复制链接，粘贴到 pending_links.txt
echo   4. 定时任务自动处理
echo ========================================
pause