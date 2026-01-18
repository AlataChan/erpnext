#!/bin/bash
# ============================================
# ERPNext Docker 恢复脚本
# 德川/裕霖业务管理系统
# ============================================
# 用途: 从备份恢复ERPNext数据
# 使用方法: ./restore.sh <备份目录>
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# 切换到脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"
cd "$DOCKER_DIR"

# 加载环境变量
if [ -f ".env" ]; then
    source .env
else
    log_error ".env 文件不存在！"
    exit 1
fi

# 检查参数
if [ -z "$1" ]; then
    echo "用法: $0 <备份目录>"
    echo "示例: $0 /var/backups/erpnext/20250116_020000"
    exit 1
fi

RESTORE_DIR="$1"

if [ ! -d "$RESTORE_DIR" ]; then
    log_error "备份目录不存在: $RESTORE_DIR"
    exit 1
fi

# 确认恢复操作
confirm_restore() {
    log_warning "=========================================="
    log_warning "警告：此操作将覆盖现有数据！"
    log_warning "备份目录: $RESTORE_DIR"
    log_warning "=========================================="
    
    read -p "确认要继续恢复操作吗？(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "恢复操作已取消"
        exit 0
    fi
}

# 停止服务
stop_services() {
    log_info "停止ERPNext服务..."
    
    docker compose -f docker-compose.prod.yml stop \
        erpnext-web \
        erpnext-socketio \
        erpnext-worker-short \
        erpnext-worker-long \
        erpnext-worker-default \
        erpnext-scheduler
    
    log_success "服务已停止"
}

# 恢复数据库
restore_database() {
    log_info "开始恢复数据库..."
    
    local db_backup=$(find "$RESTORE_DIR" -name "database_*.sql.gz" | head -1)
    
    if [ -z "$db_backup" ]; then
        log_warning "未找到数据库备份文件，跳过数据库恢复"
        return
    fi
    
    log_info "恢复数据库: $db_backup"
    
    # 解压并恢复
    gunzip -c "$db_backup" | docker compose -f docker-compose.prod.yml exec -T mariadb \
        mysql -u root -p"$MYSQL_ROOT_PASSWORD"
    
    log_success "数据库恢复完成"
}

# 恢复bench备份
restore_bench_backup() {
    log_info "开始恢复bench备份..."
    
    local bench_backup=$(find "$RESTORE_DIR" -name "bench_backup_*.tar.gz" | head -1)
    
    if [ -z "$bench_backup" ]; then
        log_warning "未找到bench备份文件，跳过bench恢复"
        return
    fi
    
    log_info "解压备份文件: $bench_backup"
    
    # 创建临时目录
    local temp_dir=$(mktemp -d)
    tar -xzf "$bench_backup" -C "$temp_dir"
    
    # 查找最新的备份文件
    local sql_file=$(find "$temp_dir" -name "*.sql.gz" | head -1)
    local files_backup=$(find "$temp_dir" -name "*-files.tar" | head -1)
    local private_backup=$(find "$temp_dir" -name "*-private-files.tar" | head -1)
    
    if [ -n "$sql_file" ]; then
        log_info "恢复数据库..."
        docker compose -f docker-compose.prod.yml exec -T erpnext-web \
            bench --site "$SITE_NAME" restore "$sql_file"
    fi
    
    # 清理临时目录
    rm -rf "$temp_dir"
    
    log_success "Bench备份恢复完成"
}

# 恢复站点文件
restore_sites() {
    log_info "开始恢复站点文件..."
    
    local sites_backup=$(find "$RESTORE_DIR" -name "sites_*.tar.gz" | head -1)
    
    if [ -z "$sites_backup" ]; then
        log_warning "未找到站点文件备份，跳过文件恢复"
        return
    fi
    
    log_info "恢复站点文件: $sites_backup"
    
    # 恢复到容器
    cat "$sites_backup" | docker compose -f docker-compose.prod.yml exec -T erpnext-web \
        tar -xzf - -C /home/frappe/frappe-bench
    
    log_success "站点文件恢复完成"
}

# 运行迁移
run_migrate() {
    log_info "运行数据库迁移..."
    
    docker compose -f docker-compose.prod.yml exec -T erpnext-web \
        bench --site "$SITE_NAME" migrate
    
    log_success "数据库迁移完成"
}

# 重建前端资源
rebuild_assets() {
    log_info "重建前端资源..."
    
    docker compose -f docker-compose.prod.yml exec -T erpnext-web \
        bench build --production
    
    log_success "前端资源重建完成"
}

# 启动服务
start_services() {
    log_info "启动ERPNext服务..."
    
    docker compose -f docker-compose.prod.yml up -d
    
    log_success "服务已启动"
}

# 清理缓存
clear_cache() {
    log_info "清理缓存..."
    
    docker compose -f docker-compose.prod.yml exec -T erpnext-web \
        bench --site "$SITE_NAME" clear-cache
    
    log_success "缓存清理完成"
}

# 主函数
main() {
    echo "============================================"
    echo "  ERPNext Docker 恢复脚本"
    echo "  德川/裕霖业务管理系统"
    echo "============================================"
    echo ""
    
    confirm_restore
    stop_services
    restore_database
    restore_bench_backup
    restore_sites
    start_services
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    run_migrate
    rebuild_assets
    clear_cache
    
    log_success "=========================================="
    log_success "恢复完成！"
    log_success "=========================================="
    echo ""
    echo "访问地址: https://${SITE_NAME}"
    echo ""
}

# 执行主函数
main "$@"
