<<<<<<< HEAD
# MaidManager

店铺管理系统，可应用于多数上钟型的店铺进行人员、排班、成本管理。FastAPI 后端与 Vite 前端的女仆店内部管理系统（MVP）。

## 环境要求
- Python 3.10+
- Node.js 18+ 与 npm

## 后端（API）
1) 安装依赖
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2) 运行本地开发服务（默认会创建/使用本地 SQLite 数据库 `maid_system.db`）
```bash
PYTHONPATH=src uvicorn maidmanager.main:app --host 0.0.0.0 --port 8000 --reload
```
3) 访问 API 文档：`http://localhost:8000/docs`

## 前端（Web）
```bash
cd frontend
npm install
npm run dev   # 本地开发
npm run build # 生成生产环境静态文件
```
构建产物位于 `frontend/dist`，可由 Nginx 等静态服务托管；本部署中 `/api` 反代到后端 `http://127.0.0.1:8000`。

## 部署提示
- 生产环境建议使用 `systemd` 或进程管理器（如 uvicorn + Nginx 反代）。
- 将 SSH 访问与应用服务端口分开，并使用防火墙/安全组限制。

## 服务器一键部署脚本
在服务器（/root/np）已配置 SSH Key 且 Nginx/systemd 现有配置不变的情况下，可直接运行：
```bash
cd /root/np
./scripts/deploy.sh
```
脚本会执行：`git pull --ff-only origin main` → 创建/使用 `.venv` 并安装依赖 → 构建前端 (`npm ci && npm run build`) → 同步静态到 `/var/www/maidmanager-frontend` → `systemctl restart maidmanager` 与 `systemctl reload nginx`。运行前请确保工作区干净（脚本会检测）。
=======
# maidmanager
店铺管理系统，可应用于多数上钟型的店铺进行人员，排班，成本管理
>>>>>>> origin/main
