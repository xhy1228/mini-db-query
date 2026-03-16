#!/bin/bash
# ============================================
# 多源数据查询小程序版 - 一键安装脚本
# 版本: v1.0.0
# 支持: Ubuntu 20.04+, Debian 11+, CentOS 8+
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
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        OS="centos"
    else
        OS=$(uname -s)
    fi
    log_info "检测到操作系统: $OS $OS_VERSION"
}

# 检查root权限
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root权限运行此脚本"
        log_info "使用: sudo bash $0"
        exit 1
    fi
}

# 安装系统依赖
install_system_deps() {
    log_step "步骤1: 安装系统依赖"
    
    case $OS in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y -qq \
                python3 python3-pip python3-venv \
                mysql-server mysql-client \
                nginx \
                curl wget git \
                build-essential \
                libmysqlclient-dev \
                > /dev/null
            ;;
        centos|rhel|rocky|almalinux)
            yum install -y -q \
                python3 python3-pip \
                mysql-server mysql \
                nginx \
                curl wget git \
                gcc gcc-c++ make \
                mysql-devel \
                > /dev/null || \
            dnf install -y -q \
                python3 python3-pip \
                mysql-server mysql \
                nginx \
                curl wget git \
                gcc gcc-c++ make \
                mysql-devel \
                > /dev/null
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
    
    log_info "系统依赖安装完成"
}

# 配置MySQL
configure_mysql() {
    log_step "步骤2: 配置MySQL 8.0"
    
    # 检查MySQL服务
    if ! command -v mysql &> /dev/null; then
        log_error "MySQL未安装"
        exit 1
    fi
    
    # 启动MySQL服务
    case $OS in
        ubuntu|debian)
            systemctl start mysql
            systemctl enable mysql
            ;;
        centos|rhel|rocky|almalinux)
            systemctl start mysqld
            systemctl enable mysqld
            ;;
    esac
    
    log_info "MySQL服务已启动"
    
    # 创建数据库和用户
    log_info "创建数据库和用户..."
    
    # 生成随机密码
    DB_PASSWORD=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9' | head -c 16)
    
    # MySQL配置
    MYSQL_CMD="mysql -u root"
    
    # 检查是否需要密码
    if [ -f /etc/mysql/debian.cnf ]; then
        MYSQL_CMD="mysql --defaults-file=/etc/mysql/debian.cnf"
    fi
    
    # 创建数据库和用户
    $MYSQL_CMD <<EOF
-- 创建数据库
CREATE DATABASE IF NOT EXISTS mini_db_query 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER IF NOT EXISTS 'mini_query'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
CREATE USER IF NOT EXISTS 'mini_query'@'%' IDENTIFIED BY '${DB_PASSWORD}';

-- 授权
GRANT ALL PRIVILEGES ON mini_db_query.* TO 'mini_query'@'localhost';
GRANT ALL PRIVILEGES ON mini_db_query.* TO 'mini_query'@'%';
FLUSH PRIVILEGES;
EOF

    log_info "MySQL配置完成"
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}MySQL 配置信息 (请妥善保管)${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo -e "  数据库: ${YELLOW}mini_db_query${NC}"
    echo -e "  用户名: ${YELLOW}mini_query${NC}"
    echo -e "  密码:   ${YELLOW}${DB_PASSWORD}${NC}"
    echo -e "  主机:   ${YELLOW}localhost${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    
    # 保存配置
    echo "MYSQL_DATABASE=mini_db_query" > /etc/mini-query-db.conf
    echo "MYSQL_USER=mini_query" >> /etc/mini-query-db.conf
    echo "MYSQL_PASSWORD=${DB_PASSWORD}" >> /etc/mini-query-db.conf
    chmod 600 /etc/mini-query-db.conf
    
    log_warn "数据库密码已保存到 /etc/mini-query-db.conf"
}

# 安装Python依赖
install_python_deps() {
    log_step "步骤3: 安装Python依赖"
    
    # 获取脚本目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    BACKEND_DIR="$PROJECT_DIR/backend"
    
    if [ ! -d "$BACKEND_DIR" ]; then
        log_error "未找到backend目录: $BACKEND_DIR"
        exit 1
    fi
    
    cd "$BACKEND_DIR"
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip -q
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        log_info "安装Python依赖包..."
        pip install -r requirements.txt -q
    fi
    
    # 安装额外的MySQL依赖
    pip install pymysql cryptography -q
    
    log_info "Python依赖安装完成"
    
    # 创建必要的目录
    mkdir -p data logs exports uploads
    
    deactivate
}

# 初始化数据库
init_database() {
    log_step "步骤4: 初始化数据库"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    BACKEND_DIR="$PROJECT_DIR/backend"
    
    # 读取MySQL配置
    if [ -f /etc/mini-query-db.conf ]; then
        source /etc/mini-query-db.conf
    else
        log_error "未找到MySQL配置文件"
        exit 1
    fi
    
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    # 设置管理员密码
    ADMIN_PASSWORD="admin123"
    
    # 执行初始化脚本
    log_info "执行数据库初始化..."
    python init_mysql_db.py \
        --host localhost \
        --port 3306 \
        --user "$MYSQL_USER" \
        --password "$MYSQL_PASSWORD" \
        --database "$MYSQL_DATABASE" \
        --admin-password "$ADMIN_PASSWORD"
    
    log_info "数据库初始化完成"
    
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}管理员账号信息${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo -e "  用户名(手机号): ${YELLOW}admin${NC}"
    echo -e "  密码:           ${YELLOW}${ADMIN_PASSWORD}${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    
    # 创建.env文件
    cat > .env <<EOF
# 数据库配置
DATABASE_URL=mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@localhost:3306/${MYSQL_DATABASE}?charset=utf8mb4

# 微信小程序配置 (请修改为实际值)
WECHAT_APPID=your_wechat_appid
WECHAT_SECRET=your_wechat_secret

# JWT配置
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_EXPIRE_MINUTES=10080

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=False
EOF
    
    log_info ".env配置文件已创建"
    
    deactivate
}

# 配置系统服务
setup_systemd_service() {
    log_step "步骤5: 配置系统服务"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    BACKEND_DIR="$PROJECT_DIR/backend"
    
    # 创建systemd服务文件
    cat > /etc/systemd/system/mini-query.service <<EOF
[Unit]
Description=Multi-Source Database Query Service
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=${BACKEND_DIR}
Environment="PATH=${BACKEND_DIR}/venv/bin"
ExecStart=${BACKEND_DIR}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    # 重载systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable mini-query
    
    log_info "系统服务配置完成"
}

# 配置Nginx
configure_nginx() {
    log_step "步骤6: 配置Nginx反向代理"
    
    # 创建Nginx配置
    cat > /etc/nginx/sites-available/mini-query <<'EOF'
server {
    listen 80;
    server_name _;

    # 日志
    access_log /var/log/nginx/mini-query.access.log;
    error_log /var/log/nginx/mini-query.error.log;

    # API代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # 文件上传限制
        client_max_body_size 50M;
    }
}
EOF
    
    # 启用配置
    ln -sf /etc/nginx/sites-available/mini-query /etc/nginx/sites-enabled/
    
    # 删除默认配置
    rm -f /etc/nginx/sites-enabled/default
    
    # 测试并重载Nginx
    nginx -t && systemctl reload nginx
    
    log_info "Nginx配置完成"
}

# 启动服务
start_service() {
    log_step "步骤7: 启动服务"
    
    systemctl start mini-query
    
    sleep 3
    
    if systemctl is-active --quiet mini-query; then
        log_info "服务启动成功"
    else
        log_error "服务启动失败"
        journalctl -u mini-query --no-pager -n 20
        exit 1
    fi
}

# 显示安装结果
show_result() {
    log_step "安装完成"
    
    # 获取服务器IP
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
    
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}    多源数据查询小程序版 安装完成!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "服务地址:"
    echo -e "  API:  ${YELLOW}http://${SERVER_IP}/api${NC}"
    echo -e "  文档: ${YELLOW}http://${SERVER_IP}/docs${NC}"
    echo ""
    echo -e "管理命令:"
    echo -e "  启动服务: ${YELLOW}systemctl start mini-query${NC}"
    echo -e "  停止服务: ${YELLOW}systemctl stop mini-query${NC}"
    echo -e "  重启服务: ${YELLOW}systemctl restart mini-query${NC}"
    echo -e "  查看日志: ${YELLOW}journalctl -u mini-query -f${NC}"
    echo ""
    echo -e "配置文件:"
    echo -e "  项目配置: ${YELLOW}$(dirname $(dirname $(readlink -f "$0")))/backend/.env${NC}"
    echo -e "  数据库配置: ${YELLOW}/etc/mini-query-db.conf${NC}"
    echo ""
    echo -e "${YELLOW}重要提示:${NC}"
    echo -e "  1. 请修改backend/.env中的微信小程序配置"
    echo -e "  2. 请妥善保管数据库密码和管理员密码"
    echo -e "  3. 建议配置HTTPS证书"
    echo ""
}

# 主函数
main() {
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}   多源数据查询小程序版 - 一键安装脚本${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    
    # 检查root权限
    check_root
    
    # 检测操作系统
    detect_os
    
    # 执行安装步骤
    install_system_deps
    configure_mysql
    install_python_deps
    init_database
    setup_systemd_service
    configure_nginx
    start_service
    show_result
}

# 运行主函数
main "$@"
