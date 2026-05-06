#!/bin/bash

# OpenOracle 日志轮转脚本
# 每天凌晨执行，保留最近30天的日志

set -e

# 配置
LOG_DIR="./logs"
BACKUP_DIR="./logs/backup"
RETENTION_DAYS=30
COMPRESS_DAYS=7

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建备份目录
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log "创建备份目录: $BACKUP_DIR"
    fi
}

# 轮转日志文件
rotate_logs() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    
    for logfile in "$LOG_DIR"/*.log; do
        if [ -f "$logfile" ]; then
            local basename=$(basename "$logfile" .log)
            local backup_file="$BACKUP_DIR/${basename}_${timestamp}.log"
            
            # 移动日志文件
            if mv "$logfile" "$backup_file"; then
                log "轮转日志: $logfile -> $backup_file"
                
                # 重新创建日志文件
                touch "$logfile"
                chmod 644 "$logfile"
                
                # 发送信号重新打开日志文件
                restart_services "$basename"
            else
                error "无法轮转日志: $logfile"
            fi
        fi
    done
}

# 重启服务以重新打开日志文件
restart_services() {
    local service_name=$1
    
    # 查找服务PID
    local pidfile="./pids/${service_name}.pid"
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        
        # 发送USR1信号（许多日志库用此信号重新打开日志）
        if kill -USR1 "$pid" 2>/dev/null; then
            log "已发送信号给服务: $service_name (PID: $pid)"
        else
            log "服务 $service_name 未运行或无法发送信号"
        fi
    fi
}

# 压缩旧日志
compress_old_logs() {
    log "压缩 $COMPRESS_DAYS 天前的日志..."
    
    find "$BACKUP_DIR" -name "*.log" -mtime +$COMPRESS_DAYS ! -name "*.gz" | while read -r file; do
        if gzip "$file"; then
            log "压缩完成: $file.gz"
        fi
    done
}

# 清理旧日志
cleanup_old_logs() {
    log "清理 $RETENTION_DAYS 天前的日志..."
    
    # 删除旧日志文件
    find "$BACKUP_DIR" -name "*.log" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete
    
    # 删除空目录
    find "$BACKUP_DIR" -type d -empty -delete
    
    log "旧日志清理完成"
}

# 生成报告
generate_report() {
    local report_file="$BACKUP_DIR/log_rotate_report_$(date '+%Y%m%d').txt"
    
    {
        echo "=== OpenOracle 日志轮转报告 ==="
        echo "时间: $(date)"
        echo "日志目录: $LOG_DIR"
        echo "备份目录: $BACKUP_DIR"
        echo ""
        echo "=== 磁盘使用情况 ==="
        du -sh "$LOG_DIR"
        du -sh "$BACKUP_DIR"
        echo ""
        echo "=== 文件统计 ==="
        echo "日志文件数: $(find "$LOG_DIR" -name "*.log" | wc -l)"
        echo "备份文件数: $(find "$BACKUP_DIR" -name "*.log" | wc -l)"
        echo "压缩文件数: $(find "$BACKUP_DIR" -name "*.gz" | wc -l)"
        echo ""
        echo "=== 操作日志 ==="
    } > "$report_file"
    
    # 添加今天的操作日志
    if [ -f "/tmp/oracle_rotate.log" ]; then
        cat "/tmp/oracle_rotate.log" >> "$report_file"
    fi
    
    log "报告已生成: $report_file"
}

# 监控磁盘空间
check_disk_space() {
    local threshold=90
    local usage=$(df "$LOG_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt "$threshold" ]; then
        error "磁盘使用率过高: ${usage}% (阈值: ${threshold}%)"
        
        # 发送告警
        send_alert "磁盘空间告警" "日志目录磁盘使用率: ${usage}%"
        
        # 紧急清理
        emergency_cleanup
    else
        log "磁盘使用率正常: ${usage}%"
    fi
}

# 紧急清理
emergency_cleanup() {
    log "执行紧急清理..."
    
    # 保留最近7天的日志
    find "$BACKUP_DIR" -name "*.log" -mtime +7 -delete
    find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
    
    # 压缩3天前的日志
    find "$BACKUP_DIR" -name "*.log" -mtime +3 ! -name "*.gz" -exec gzip {} \;
    
    log "紧急清理完成"
}

# 发送告警
send_alert() {
    local subject=$1
    local message=$2
    
    # 这里可以实现邮件、Slack、Webhook等告警方式
    # 示例: 发送到系统日志
    logger -t OpenOracle "ALERT: $subject - $message"
    
    # 示例: 发送邮件
    # echo "$message" | mail -s "$subject" admin@example.com
}

# 主函数
main() {
    log "开始日志轮转..."
    
    # 检查日志目录
    if [ ! -d "$LOG_DIR" ]; then
        error "日志目录不存在: $LOG_DIR"
        exit 1
    fi
    
    # 执行步骤
    create_backup_dir
    check_disk_space
    rotate_logs
    compress_old_logs
    cleanup_old_logs
    generate_report
    
    success "日志轮转完成"
}

# 执行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # 重定向输出到日志文件
    exec > /tmp/oracle_rotate.log 2>&1
    
    main "$@"
    
    # 退出代码
    exit 0
fi