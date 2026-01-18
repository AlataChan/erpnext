#!/bin/bash
# ============================================
# ERPNext Docker 入口脚本
# 德川/裕霖业务管理系统
# ============================================
# 用途: 初始化配置、创建站点并启动服务
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 工作目录
cd /home/frappe/frappe-bench

# 确保 sites 目录存在
mkdir -p sites

# ==================== 配置 Redis 连接 ====================
log_info "配置 Redis 连接..."

# 解析 Redis 配置
REDIS_CACHE_HOST="${REDIS_CACHE%%:*}"
REDIS_CACHE_PORT="${REDIS_CACHE##*:}"
REDIS_QUEUE_HOST="${REDIS_QUEUE%%:*}"
REDIS_QUEUE_PORT="${REDIS_QUEUE##*:}"

# 默认值
REDIS_CACHE_HOST="${REDIS_CACHE_HOST:-redis-cache}"
REDIS_CACHE_PORT="${REDIS_CACHE_PORT:-6379}"
REDIS_QUEUE_HOST="${REDIS_QUEUE_HOST:-redis-queue}"
REDIS_QUEUE_PORT="${REDIS_QUEUE_PORT:-6379}"
SITE_NAME="${SITE_NAME:-erp.localhost}"

# 创建或更新 common_site_config.json
CONFIG_FILE="sites/common_site_config.json"

log_info "创建站点配置文件..."
cat > "$CONFIG_FILE" << EOF
{
  "db_host": "${MYSQL_HOST:-mariadb}",
  "db_port": ${MYSQL_PORT:-3306},
  "redis_cache": "redis://${REDIS_CACHE_HOST}:${REDIS_CACHE_PORT}",
  "redis_queue": "redis://${REDIS_QUEUE_HOST}:${REDIS_QUEUE_PORT}",
  "redis_socketio": "redis://${REDIS_QUEUE_HOST}:${REDIS_QUEUE_PORT}",
  "socketio_port": 9000,
  "webserver_port": 8000,
  "serve_default_site": true,
  "default_site": "${SITE_NAME}"
}
EOF

log_success "站点配置完成"
cat "$CONFIG_FILE"

# ==================== 确保 ERPNext 模块已安装 ====================
log_info "检查 ERPNext 模块安装..."

if ! /home/frappe/frappe-bench/env/bin/python -c "import erpnext" 2>/dev/null; then
    log_warning "ERPNext 模块未安装，正在安装..."
    if [ -f "apps/erpnext/pyproject.toml" ]; then
        /home/frappe/frappe-bench/env/bin/pip install -e apps/erpnext --quiet
        log_success "ERPNext 模块安装完成"
    else
        log_error "未找到 apps/erpnext/pyproject.toml"
    fi
else
    log_success "ERPNext 模块已安装"
fi

# ==================== 等待依赖服务 ====================
log_info "等待依赖服务..."

wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=60
    local attempt=0

    log_info "等待 $service_name ($host:$port)..."
    
    while ! nc -z "$host" "$port" 2>/dev/null; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            log_error "$service_name 连接超时！"
            return 1
        fi
        sleep 2
    done
    log_success "$service_name 已就绪"
    return 0
}

wait_for_service "${MYSQL_HOST:-mariadb}" "${MYSQL_PORT:-3306}" "MariaDB"
wait_for_service "$REDIS_CACHE_HOST" "$REDIS_CACHE_PORT" "Redis Cache"
wait_for_service "$REDIS_QUEUE_HOST" "$REDIS_QUEUE_PORT" "Redis Queue"

# ==================== 检查并创建站点 ====================
log_info "检查站点: $SITE_NAME"

SITE_DIR="sites/${SITE_NAME}"

# 检查站点目录和配置文件是否存在
if [ -d "$SITE_DIR" ] && [ -f "$SITE_DIR/site_config.json" ]; then
    log_success "站点 $SITE_NAME 已存在"
    # 确保是默认站点
    echo "$SITE_NAME" > sites/currentsite.txt
else
    log_warning "站点 $SITE_NAME 不存在，开始创建..."
    
    # 设置默认密码
    DB_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-root123}"
    SITE_ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"
    
    log_info "创建新站点... (DB密码: ${DB_ROOT_PASSWORD:0:3}***, 管理员密码: ${SITE_ADMIN_PASSWORD:0:3}***)"
    
    # 创建站点
    if bench new-site "$SITE_NAME" \
        --db-root-password "$DB_ROOT_PASSWORD" \
        --admin-password "$SITE_ADMIN_PASSWORD" \
        --no-mariadb-socket \
        --verbose; then
        log_success "站点创建成功"
    else
        log_error "站点创建失败！"
        log_info "尝试查看错误详情..."
        exit 1
    fi
    
    # 安装 ERPNext 应用
    log_info "安装 ERPNext 应用到站点..."
    if bench --site "$SITE_NAME" install-app erpnext; then
        log_success "ERPNext 安装成功"
    else
        log_warning "ERPNext 安装失败，可能已安装或应用不可用"
    fi
    
    # 设置为默认站点
    bench use "$SITE_NAME"
    echo "$SITE_NAME" > sites/currentsite.txt
    
    log_success "站点初始化完成"
fi

# 显示站点目录状态
log_info "站点目录状态:"
ls -la sites/ 2>/dev/null || log_warning "无法列出 sites 目录"

# ==================== 安装前端依赖（开发模式）====================
if [ "${DEVELOPER_MODE:-0}" = "1" ]; then
    log_info "开发模式：检查前端依赖..."
    
    # 检查 frappe 的 node_modules
    if [ ! -d "apps/frappe/node_modules" ]; then
        log_info "安装 Frappe 前端依赖..."
        cd apps/frappe && yarn install --frozen-lockfile 2>/dev/null || yarn install
        cd /home/frappe/frappe-bench
    fi
    
    # 检查 erpnext 的 node_modules
    if [ -d "apps/erpnext" ] && [ ! -d "apps/erpnext/node_modules" ]; then
        if [ -f "apps/erpnext/package.json" ]; then
            log_info "安装 ERPNext 前端依赖..."
            cd apps/erpnext && yarn install --frozen-lockfile 2>/dev/null || yarn install
            cd /home/frappe/frappe-bench
        fi
    fi
fi

# ==================== 运行迁移 ====================
log_info "运行数据库迁移..."
bench --site "$SITE_NAME" migrate --skip-failing 2>/dev/null || log_warning "迁移跳过（可能是首次运行）"

# ==================== 构建前端资源（如果需要）====================
if [ ! -d "sites/assets" ] || [ -z "$(ls -A sites/assets 2>/dev/null)" ]; then
    log_info "构建前端资源..."
    bench build --production 2>/dev/null || log_warning "前端构建跳过"
fi

# ==================== 启动服务 ====================
log_info "启动 ERPNext 服务..."
echo ""
echo "=========================================="
echo "  站点: $SITE_NAME"
echo "  管理员: Administrator"
echo "  访问: http://localhost:8000"
echo "=========================================="
echo ""

# 执行传入的命令
exec "$@"
