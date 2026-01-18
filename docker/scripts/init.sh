#!/bin/bash
# ============================================
# ERPNext Docker 初始化脚本
# 德川/裕霖业务管理系统
# ============================================
# 用途: 首次部署时初始化ERPNext站点
# 使用方法: ./init.sh
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 切换到脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"
cd "$DOCKER_DIR"

# 检查环境变量文件
if [ ! -f ".env" ]; then
    log_error ".env 文件不存在！请先复制 env.example 并配置："
    echo "  cp env.example .env"
    echo "  vim .env"
    exit 1
fi

# 加载环境变量
source .env

# 检查必要的环境变量
check_required_vars() {
    local required_vars=(
        "SITE_NAME"
        "MYSQL_ROOT_PASSWORD"
        "MYSQL_PASSWORD"
        "ADMIN_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "必需的环境变量 $var 未设置！"
            exit 1
        fi
    done
    log_success "环境变量检查通过"
}

# 创建数据目录
create_directories() {
    log_info "创建数据目录..."
    
    BACKUP_PATH="${BACKUP_PATH:-/var/lib/erpnext}"
    
    sudo mkdir -p "$BACKUP_PATH/mariadb"
    sudo mkdir -p "$BACKUP_PATH/sites"
    sudo mkdir -p "$BACKUP_PATH/logs"
    sudo mkdir -p "$BACKUP_PATH/backups"
    
    # 设置权限
    sudo chown -R 1000:1000 "$BACKUP_PATH/sites"
    sudo chown -R 1000:1000 "$BACKUP_PATH/logs"
    sudo chown -R 999:999 "$BACKUP_PATH/mariadb"
    
    log_success "数据目录创建完成"
}

# 生成自签名SSL证书（开发/测试用）
generate_ssl_cert() {
    log_info "检查SSL证书..."
    
    if [ -f "nginx/ssl/fullchain.pem" ] && [ -f "nginx/ssl/privkey.pem" ]; then
        log_info "SSL证书已存在，跳过生成"
        return
    fi
    
    log_warning "生成自签名SSL证书（仅供测试使用）..."
    
    mkdir -p nginx/ssl
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/privkey.pem \
        -out nginx/ssl/fullchain.pem \
        -subj "/C=CN/ST=Shanghai/L=Shanghai/O=Dechuan/OU=IT/CN=${SITE_NAME}"
    
    log_success "自签名SSL证书生成完成"
    log_warning "生产环境请使用正式SSL证书！"
}

# 构建Docker镜像
build_images() {
    log_info "构建Docker镜像..."
    
    docker compose -f docker-compose.prod.yml build --no-cache
    
    log_success "Docker镜像构建完成"
}

# 启动基础服务
start_services() {
    log_info "启动基础服务 (MariaDB, Redis)..."
    
    docker compose -f docker-compose.prod.yml up -d mariadb redis-cache redis-queue
    
    # 等待数据库就绪
    log_info "等待数据库就绪..."
    sleep 30
    
    # 检查数据库连接
    max_attempts=30
    attempt=0
    while ! docker compose -f docker-compose.prod.yml exec mariadb \
        mysqladmin ping -h localhost -u root -p"$MYSQL_ROOT_PASSWORD" --silent 2>/dev/null; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            log_error "数据库连接超时！"
            exit 1
        fi
        log_info "等待数据库启动... ($attempt/$max_attempts)"
        sleep 5
    done
    
    log_success "基础服务启动完成"
}

# 初始化ERPNext站点
init_site() {
    log_info "初始化ERPNext站点: $SITE_NAME"
    
    # 启动web服务（用于初始化）
    docker compose -f docker-compose.prod.yml up -d erpnext-web
    
    # 等待服务就绪
    sleep 30
    
    # 创建站点
    log_info "创建新站点..."
    docker compose -f docker-compose.prod.yml exec erpnext-web \
        bench new-site "$SITE_NAME" \
        --db-root-password "$MYSQL_ROOT_PASSWORD" \
        --admin-password "$ADMIN_PASSWORD" \
        --no-mariadb-socket
    
    # 安装ERPNext应用
    log_info "安装ERPNext应用..."
    docker compose -f docker-compose.prod.yml exec erpnext-web \
        bench --site "$SITE_NAME" install-app erpnext
    
    # 设置为默认站点
    docker compose -f docker-compose.prod.yml exec erpnext-web \
        bench use "$SITE_NAME"
    
    # 运行数据库迁移
    log_info "运行数据库迁移..."
    docker compose -f docker-compose.prod.yml exec erpnext-web \
        bench --site "$SITE_NAME" migrate
    
    # 构建前端资源
    log_info "构建前端资源..."
    docker compose -f docker-compose.prod.yml exec erpnext-web \
        bench build --production
    
    log_success "ERPNext站点初始化完成"
}

# 启动所有服务
start_all_services() {
    log_info "启动所有服务..."
    
    docker compose -f docker-compose.prod.yml up -d
    
    log_success "所有服务启动完成"
}

# 显示服务状态
show_status() {
    log_info "服务状态："
    docker compose -f docker-compose.prod.yml ps
    
    echo ""
    log_success "=========================================="
    log_success "ERPNext 部署完成！"
    log_success "=========================================="
    echo ""
    echo "访问地址: https://${SITE_NAME}"
    echo "管理员账号: Administrator"
    echo "管理员密码: （您在.env中配置的ADMIN_PASSWORD）"
    echo ""
    log_warning "请确保您的域名 ${SITE_NAME} 已正确解析到服务器IP"
    log_warning "首次访问可能需要等待1-2分钟"
    echo ""
}

# 主函数
main() {
    echo "============================================"
    echo "  ERPNext Docker 初始化脚本"
    echo "  德川/裕霖业务管理系统"
    echo "============================================"
    echo ""
    
    check_required_vars
    create_directories
    generate_ssl_cert
    build_images
    start_services
    init_site
    start_all_services
    show_status
}

# 执行主函数
main "$@"
