@echo off
chcp 65001 >nul
echo ========================================
echo   机场收集仓库批量克隆脚本
echo   时间: %date% %time%
echo ========================================
echo.

set CLONE_DIR=%~dp0collected_repos
if not exist "%CLONE_DIR%" mkdir "%CLONE_DIR%"
cd /d "%CLONE_DIR%"

echo [1/6] SIQILZ/Free-VPN - 免费机场公益收集
git clone https://github.com/SIQILZ/Free-VPN.git 2>nul && echo   OK || echo   已有/失败

echo [2/6] maomao533/jc-tizi-tj - 2026机场推荐
git clone https://github.com/maomao533/jc-tizi-tj.git 2>nul && echo   OK || echo   已有/失败

echo [3/6] Vikutorika/Airports - 免费订阅推荐
git clone https://github.com/Vikutorika/Airports.git 2>nul && echo   OK || echo   已有/失败

echo [4/6] xiaoji235/airport-free - 每3小时自动更新
git clone https://github.com/xiaoji235/airport-free.git 2>nul && echo   OK || echo   已有/失败

echo [5/6] ggborr/FREEE-VPN - 免费VPN节点
git clone https://github.com/ggborr/FREEE-VPN.git 2>nul && echo   OK || echo   已有/失败

echo [6/6] dimensionconnex GitHub Pages - 海量免费机场
git clone https://github.com/dimensionconnex/dimensionconnex.github.io.git 2>nul && echo   OK || echo   已有/失败

echo.
echo ========================================
echo   克隆完成!
echo   目录: %CLONE_DIR%
echo ========================================
dir /b "%CLONE_DIR%"
echo.
pause
