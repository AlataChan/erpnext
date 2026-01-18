# ERPNext Docker 部署

> 德川/裕霖业务管理系统 - 容器化部署

## 快速开始

### 1. 配置环境变量

```bash
cp env.example .env
vim .env
```

### 2. 一键部署

```bash
./scripts/init.sh
```

### 3. 访问系统

- 地址: `https://your-domain.com`
- 账号: `Administrator`
- 密码: 您在 `.env` 中配置的 `ADMIN_PASSWORD`

## 文件说明

| 文件 | 说明 |
|------|------|
| `docker-compose.yml` | 开发环境配置 |
| `docker-compose.prod.yml` | 生产环境配置 |
| `Dockerfile` | 自定义ERPNext镜像 |
| `env.example` | 环境变量模板 |
| `nginx/nginx.conf` | Nginx反向代理配置 |
| `scripts/init.sh` | 初始化脚本 |
| `scripts/backup.sh` | 备份脚本 |
| `scripts/restore.sh` | 恢复脚本 |

## 常用命令

```bash
# 启动服务
docker compose -f docker-compose.prod.yml up -d

# 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 停止服务
docker compose -f docker-compose.prod.yml down

# 备份
./scripts/backup.sh full

# 恢复
./scripts/restore.sh /path/to/backup
```

## 完整文档

请查阅 [Docker部署指南](../docs/DOCKER_DEPLOYMENT_GUIDE.md)
