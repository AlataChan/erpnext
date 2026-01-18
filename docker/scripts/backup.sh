#!/bin/bash
# ============================================
# ERPNext Docker 备份脚本
# 德川/裕霖业务管理系统
# ============================================
# 用途: 定期备份ERPNext数据（数据库+文件）
# 使用方法: ./backup.sh [full|db|files]
# 建议添加到crontab定时执行
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

# 备份配置
BACKUP_BASE_PATH="${BACKUP_PATH:-/var/backups/erpnext}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_BASE_PATH/$TIMESTAMP"

# 创建备份目录
create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    log_info "备份目录: $BACKUP_DIR"
}

# 备份数据库
backup_database() {
    log_info "开始备份数据库..."
    
    local db_backup_file="$BACKUP_DIR/database_$TIMESTAMP.sql.gz"
    
    # 使用docker exec执行mysqldump
    docker compose -f docker-compose.prod.yml exec -T mariadb \
        mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" \
        --single-transaction \
        --quick \
        --lock-tables=false \
        --all-databases | gzip > "$db_backup_file"
    
    if [ -f "$db_backup_file" ]; then
        local size=$(du -h "$db_backup_file" | cut -f1)
        log_success "数据库备份完成: $db_backup_file ($size)"
    else
        log_error "数据库备份失败！"
        return 1
    fi
}

# 备份站点文件
backup_sites() {
    log_info "开始备份站点文件..."
    
    local sites_backup_file="$BACKUP_DIR/sites_$TIMESTAMP.tar.gz"
    
    # 备份sites目录
    docker compose -f docker-compose.prod.yml exec -T erpnext-web \
        tar -czf - -C /home/frappe/frappe-bench sites \
        > "$sites_backup_file"
    
    if [ -f "$sites_backup_file" ]; then
        local size=$(du -h "$sites_backup_file" | cut -f1)
        log_success "站点文件备份完成: $sites_backup_file ($size)"
    else
        log_error "站点文件备份失败！"
        return 1
    fi
}

# 使用bench命令备份（推荐方式）
backup_with_bench() {
    log_info "使用bench命令备份站点: $SITE_NAME"
    
    # 执行bench备份
    docker compose -f docker-compose.prod.yml exec -T erpnext-web \
        bench --site "$SITE_NAME" backup --with-files
    
    # 复制备份文件到主机
    local bench_backup_dir="/home/frappe/frappe-bench/sites/$SITE_NAME/private/backups"
    
    docker compose -f docker-compose.prod.yml exec -T erpnext-web \
        tar -czf - -C "$bench_backup_dir" . \
        > "$BACKUP_DIR/bench_backup_$TIMESTAMP.tar.gz"
    
    log_success "Bench备份完成"
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理 $BACKUP_RETENTION_DAYS 天前的旧备份..."
    
    find "$BACKUP_BASE_PATH" -maxdepth 1 -type d -mtime +$BACKUP_RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
    
    # 统计剩余备份
    local backup_count=$(find "$BACKUP_BASE_PATH" -maxdepth 1 -type d | wc -l)
    log_info "当前保留备份数量: $((backup_count - 1))"
}

# 生成备份报告
generate_report() {
    local report_file="$BACKUP_DIR/backup_report.txt"
    
    cat > "$report_file" << EOF
============================================
ERPNext 备份报告
德川/裕霖业务管理系统
============================================
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
站点名称: $SITE_NAME
备份目录: $BACKUP_DIR

备份文件列表:
$(ls -lh "$BACKUP_DIR")

磁盘使用情况:
$(df -h "$BACKUP_BASE_PATH")

============================================
EOF

    log_info "备份报告已生成: $report_file"
}

# 发送通知（可选：配置企业微信/邮件通知）
send_notification() {
    if [ -n "$WECHAT_CORP_ID" ] && [ -n "$WECHAT_CORP_SECRET" ]; then
        log_info "发送企业微信通知..."
        # TODO: 实现企业微信通知逻辑
    fi
}

# 完整备份
full_backup() {
    log_info "========== 开始完整备份 =========="
    
    create_backup_dir
    backup_with_bench
    backup_database
    cleanup_old_backups
    generate_report
    send_notification
    
    log_success "========== 完整备份完成 =========="
}

# 仅数据库备份
db_only_backup() {
    log_info "========== 开始数据库备份 =========="
    
    create_backup_dir
    backup_database
    cleanup_old_backups
    
    log_success "========== 数据库备份完成 =========="
}

# 仅文件备份
files_only_backup() {
    log_info "========== 开始文件备份 =========="
    
    create_backup_dir
    backup_sites
    cleanup_old_backups
    
    log_success "========== 文件备份完成 =========="
}

# 显示帮助
show_help() {
    cat << EOF
ERPNext Docker 备份脚本

用法: $0 [命令]

命令:
  full    完整备份（数据库+文件，推荐）
  db      仅备份数据库
  files   仅备份文件
  help    显示帮助信息

示例:
  $0 full     # 执行完整备份
  $0 db       # 仅备份数据库

定时任务示例 (crontab -e):
  # 每天凌晨2点执行完整备份
  0 2 * * * /path/to/backup.sh full >> /var/log/erpnext-backup.log 2>&1
  
  # 每6小时执行数据库备份
  0 */6 * * * /path/to/backup.sh db >> /var/log/erpnext-backup.log 2>&1
EOF
}

# 主函数
main() {
    local command="${1:-full}"
    
    case "$command" in
        full)
            full_backup
            ;;
        db)
            db_only_backup
            ;;
        files)
            files_only_backup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
