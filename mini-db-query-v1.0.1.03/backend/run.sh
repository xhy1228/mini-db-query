#!/bin/bash
# 多源数据查询小程序 - 启动脚本

cd "$(dirname "$0")"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
pip3 install -r requirements.txt -q

# 创建必要目录
mkdir -p data logs exports

# 检查数据库是否已初始化
if [ ! -f "data/mini_db_query.db" ]; then
    echo "📊 初始化数据库..."
    python3 init_sample_data.py
fi

# 启动服务
echo "🚀 启动服务..."
echo "   访问地址: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo "   默认账号: admin / 123456"
echo ""

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
