#!/usr/bin/env bash
# 一键关联并推送到 GitHub（本地仓库 → 远程）
# 用法:  bash push_to_github.sh https://github.com/<用户名>/<仓库名>.git
set -e
cd "$(dirname "$0")"

URL="$1"
if [ -z "$URL" ]; then
  echo "用法: bash push_to_github.sh <仓库URL>"
  echo "示例: bash push_to_github.sh https://github.com/yikeqingsongguo/HW-supply-chain-management.git"
  exit 1
fi

echo "→ 分支: $(git branch --show-current)（应为 main，与 deploy.yml 的触发分支一致）"
git remote remove origin 2>/dev/null || true
git remote add origin "$URL"
echo "→ 已设置 origin = $(git remote get-url origin)"
echo "→ 开始推送…（首次会要求登录/凭据）"
git push -u origin main

echo ""
echo "✅ 推送完成。接下来到 GitHub 仓库页面："
echo "   Settings → Pages → Build and deployment → Source 选「GitHub Actions」"
echo "   然后在 Actions 页签看 Deploy Supply-Chain Dashboard 是否 success"
