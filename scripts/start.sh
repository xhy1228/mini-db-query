#!/bin/bash
# ============================================
# 多源数据查询小程序版 - 启动脚本
# ============================================

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 获取项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"

cd "$BACKEND_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}未找到虚拟环境，正在创建...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt -q
else
    source venv/bin/activate
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}未找到.env配置文件，使用默认配置${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
    fi
fi

# 显示启动信息
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  多源数据查询小程序版 服务启动${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "项目目录: ${YELLOW}$BACKEND_DIR${NC}"
echo -e "启动模式: ${YELLOW}开发模式${NC}"
echo ""

# 启动服务
python main.py
