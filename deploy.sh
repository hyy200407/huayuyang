#!/bin/bash
# GitHub Pages 部署脚本 - 个人作品集
# 用户名: Kelly0905
# 仓库: Kelly0905.github.io

echo "========================================"
echo "  GitHub Pages 部署脚本"
echo "  用户名: Kelly0905"
echo "  仓库: Kelly0905.github.io"
echo "========================================"
echo ""

# 切换到作品集目录
cd "/g/Desktop/5.3(开阳)课程资料/day24个人作品集搭建+简历优化/02课程代码/01个人作品集部署/个人作品集"

echo "[1/4] 初始化 Git 仓库..."
git init
git checkout -b main

echo ""
echo "[2/4] 添加所有文件并提交..."
git add .
git commit -m "Initial commit: 个人作品集"

echo ""
echo "[3/4] 配置远程仓库..."
git remote remove origin 2>/dev/null
git remote add origin https://github.com/Kelly0905/Kelly0905.github.io.git

echo ""
echo "[4/4] 推送到 GitHub..."
echo ""
echo "如果提示认证，请使用："
echo "  用户名: Kelly0905"
echo "  密码: GitHub Personal Access Token"
echo ""
echo "获取 Token: https://github.com/settings/tokens"
echo ""
git push -u origin main

echo ""
echo "========================================"
echo "  推送完成！"
echo "  访问地址: https://Kelly0905.github.io"
echo "  （等待 1-5 分钟后生效）"
echo "========================================"