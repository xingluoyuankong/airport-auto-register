@echo off
chcp 65001 >nul
title 机场自动收集与注册系统

echo.
echo ╔══════════════════════════════════════════╗
echo ║     机场自动收集与批量注册系统          ║
echo ║     v1.0 - 2026-06-27                   ║
echo ╚══════════════════════════════════════════╝
echo.
echo 请选择操作:
echo   [1] 安装依赖 (requests + ddddocr + playwright)
echo   [2] 克隆新发现的GitHub仓库
echo   [3] 发现可注册机场
echo   [4] 批量API注册 (V2Board)
echo   [5] 浏览器注册 (带Turnstile的机场)
echo   [6] 完整流程 (发现→注册)
echo   [7] 安装Turnstile绕过工具
echo   [8] 从Outlook获取验证码
echo   [Q] 退出
echo.
set /p choice="请输入选项: "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto clone
if "%choice%"=="3" goto discover
if "%choice%"=="4" goto register
if "%choice%"=="5" goto browser
if "%choice%"=="6" goto full
if "%choice%"=="7" goto turnstile
if "%choice%"=="8" goto outlook
if /i "%choice%"=="Q" goto end

echo 无效选项!
pause
goto end

:install
echo.
echo [安装依赖...]
pip install requests ddddocr playwright playwright-stealth -q
playwright install chromium
echo ✅ 完成!
pause
goto end

:clone
echo.
echo [克隆新仓库...]
call "%~dp0clone_new_repos.bat"
goto end

:discover
echo.
echo [发现可注册机场...]
python "%~dp0airport_register_main.py" --mode discover
pause
goto end

:register
echo.
echo [批量API注册...]
python "%~dp0airport_register_main.py" --mode register --threads 3
pause
goto end

:browser
echo.
echo [浏览器注册]
echo 支持的机场: FSCloud, 奈云v2ny, Speedy, 雨燕云, 逗猫
echo.
set /p airport_name="请输入机场名称: "
python "%~dp0browser_register.py" --airport %airport_name%
pause
goto end

:full
echo.
echo [完整流程...]
python "%~dp0airport_register_main.py" --mode full --threads 3
pause
goto end

:turnstile
echo.
echo [安装Turnstile绕过工具...]
python "%~dp0setup_turnstile.py" --all
pause
goto end

:outlook
echo.
echo [从Outlook获取验证码]
echo 可用邮箱:
echo   1. sanchezquinncu3w1kkhtuc74@outlook.com
echo   2. hendricktamm95v80awzaxli@outlook.com
echo   3. parker738403dcp34kfdl6j@outlook.com
echo.
set /p outlook_email="请输入邮箱: "
set /p outlook_pass="请输入密码: "
python "%~dp0outlook_skill.py" --email %outlook_email% --password %outlook_pass% --timeout 120
pause
goto end

:end
echo.
echo 再见!
exit /b
