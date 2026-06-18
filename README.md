# Storefront Project

目录结构：
- frontend：前台商城 Vue 3 项目
- storefront-backend：前台商城 Flask 后端

项目归属：
- 商城会话数据：storefront-backend\data
- 商城后端依赖：storefront-backend\_vendor
- 商城后端通过接口连接后台后端，不再使用 shared-data

环境变量：
- SMAWELL_ADMIN_API_BASE_URL=http://127.0.0.1:5302
- SMAWELL_SERVICE_TOKEN=smawell-service-token

启动：
1. cd storefront-backend
2. python app.py
3. cd ..\frontend
4. npm install
5. npm run dev

## GitHub 自动部署

当前仓库已内置 GitHub Actions：
- `.github/workflows/deploy.yml`
- `scripts/deploy-storefront.sh`

推送到 `main` 后，会通过 SSH 登录服务器并执行：
- `git fetch`
- `git reset --hard origin/main`
- `docker compose build store-web store-api`
- `docker compose up -d store-web store-api`

GitHub 仓库需要配置以下 Secrets：
- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_PASSWORD`

服务器预期目录：
- `/opt/smawell/shopify`
- `/opt/smawell/deploy`
