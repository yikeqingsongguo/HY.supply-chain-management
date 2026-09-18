#!/usr/bin/env bash
# 推送到 GitHub（本机网络下 HTTPS 被重置，故走 SSH）
# 用法: bash push_to_github.sh
set -e
cd "$(dirname "$0")"

REPO="git@github.com:yikeqingsongguo/HY.supply-chain-management.git"
PAGE="https://yikeqingsongguo.github.io/HY.supply-chain-management/"

echo "=== 1/4 分支检查 ==="
BR="$(git branch --show-current)"
echo "    当前分支: $BR（需为 main，与 deploy.yml 触发分支一致）"
[ "$BR" = "main" ] || { echo "    ✖ 分支不是 main，请先 git branch -m $BR main"; exit 1; }

echo "=== 2/4 SSH 认证预检 ==="
if ! ssh -T -o BatchMode=yes -o ConnectTimeout=15 git@github.com 2>&1 | grep -q "successfully authenticated"; then
  echo "    ✖ SSH 未认证。请先到 GitHub → Settings → SSH and GPG keys → New SSH key 粘贴公钥："
  echo "      $(cat ~/.ssh/id_ed25519.pub)"
  exit 1
fi
echo "    ✔ SSH 认证通过"

echo "=== 3/4 关联远程 ==="
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO"
echo "    origin = $(git remote get-url origin)"

echo "=== 4/4 推送 ==="
git push -u origin main

echo ""
echo "✅ 推送完成。接下来（只需做一次）："
echo "   GitHub 仓库 → Settings → Pages → Source 选「GitHub Actions」"
echo "   再到 Actions 页签确认 Deploy Supply-Chain Dashboard 为绿色 ✅"
echo "   上线地址：$PAGE"
