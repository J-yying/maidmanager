#!/usr/bin/env bash
set -euo pipefail

# 部署脚本：拉取 main、安装依赖、构建前端、同步静态文件、重启服务
# 在服务器上以 root 运行：/root/np/scripts/deploy.sh

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_ROOT"

log() { printf "[deploy] %s\n" "$*"; }

ensure_clean() {
  if ! git diff --quiet || ! git diff --cached --quiet; then
    log "工作区不干净，请先提交或清理后再运行。"
    exit 1
  fi
}

ensure_clean

log "1/6 更新代码 (git pull --ff-only origin main)"
git pull --ff-only origin main

log "2/6 准备 Python 环境与依赖"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

log "3/6 确保后端路径在 PYTHONPATH 中"
export PYTHONPATH="$APP_ROOT/src"

log "4/6 构建前端"
cd "$APP_ROOT/frontend"
npm ci
npm run build

log "5/6 同步前端静态资源到 /var/www/maidmanager-frontend"
rsync -a --delete "$APP_ROOT/frontend/dist/" /var/www/maidmanager-frontend/

log "6/6 重启/刷新服务"
systemctl restart maidmanager
systemctl reload nginx

log "部署完成"
