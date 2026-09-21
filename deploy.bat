@echo off
chcp 65001 >nul
echo ========================================
echo   GitHub Pages 部署脚本
echo   用户名: Kelly0905
echo   仓库名: Kelly0905.github.io
echo ========================================
echo.

REM 检查 Git 是否可用
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Git，请先安装 Git for Windows
    echo 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [1/4] 正在初始化 Git 仓库...
git init
git checkout -b main

echo.
echo [2/4] 添加所有文件...
git add .
git commit -m "Initial commit: 个人作品集"

echo.
echo [3/4] 添加远程仓库...
git remote remove origin 2>nul
git remote add origin https://github.com/Kelly0905/Kelly0905.github.io.git

echo.
echo [4/4] 推送到 GitHub...
echo.
echo 如果提示输入用户名和密码：
echo   用户名: Kelly0905
echo   密码: 使用 GitHub Personal Access Token（不是登录密码）
echo.
echo 如未配置 Token，请先在 GitHub -^> Settings -^> Developer settings -^> Personal access tokens 生成
echo.
pause
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo [提示] 如果推送失败，可能是因为：
    echo   1. 仓库 Kelly0905.github.io 还未创建
    echo   2. 认证信息不正确
    echo.
    echo 请先访问 https://github.com/new 创建仓库:
    echo   Repository name: Kelly0905.github.io
    echo   选择: Public
    echo   然后回来重新运行此脚本
)

echo.
echo ========================================
echo   部署完成！
echo   访问地址: https://Kelly0905.github.io
echo   （等待 1-5 分钟后生效）
echo ========================================
pause