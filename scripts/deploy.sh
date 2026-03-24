#!/bin/bash
# 部署脚本 - 服务器端使用
# 用法: bash scripts/deploy.sh [version]

set -e

# 配置
PROJECT_DIR="/root/projects/mini-db-query"
BACKUP_DIR="/root/backups/mini-db-query"
LOG_FILE="/root/logs/deploy-$(date +%Y%m%d).log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 创建备份
create_backup() {
    log "创建备份..."
    mkdir -p "$BACKUP_DIR"
    BACKUP_NAME="backup-$(date +%Y%m%d_%H%M%S)"
    
    if [ -d "$PROJECT_DIR" ]; then
        cp -r "$PROJECT_DIR" "$BACKUP_DIR/$BACKUP_NAME"
        log "备份已创建: $BACKUP_DIR/$BACKUP_NAME"
    fi
}

# 拉取代码
pull_code() {
    log "拉取最新代码..."
    cd "$PROJECT_DIR"
    
    # 保存本地更改
    if [ -n "$(git status --porcelain)" ]; then
        log "保存本地更改..."
        git stash
    fi
    
    git pull origin main
    
    # 恢复本地更改
    if git stash list | grep -q .; then
        log "恢复本地更改..."
        git stash pop || true
    fi
}

# 更新依赖
update_dependencies() {
    log "更新后端依赖..."
    cd "$PROJECT_DIR/backend"
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
}

# 重启服务
restart_service() {
    log "重启后端服务..."
    
    # 停止旧进程
    pkill -f "uvicorn main:app" || true
    
    # 启动新进程
    cd "$PROJECT_DIR/backend"
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 >> "$LOG_FILE" 2>&1 &
    
    log "服务已重启"
}

# 健康检查
health_check() {
    log "执行健康检查..."
    
    sleep 3
    
    if curl -s http://localhost:8000/health > /dev/null; then
        log "✓ 服务健康检查通过"
    else
        log "✗ 服务健康检查失败"
        exit 1
    fi
}

# 主流程
main() {
    log "========== 开始部署 =========="
    
    mkdir -p "$(dirname "$LOG_FILE")"
    
    create_backup
    pull_code
    update_dependencies
    restart_service
    health_check
    
    log "========== 部署完成 =========="
}

# 执行
main "$@"
