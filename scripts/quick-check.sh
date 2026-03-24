#!/bin/bash
# 快速检查脚本 - 本地开发使用
# 用法: bash scripts/quick-check.sh

set -e

echo "========================================"
echo "  mini-db-query 快速检查"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        exit 1
    fi
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. 检查Python语法
echo ">>> 检查后端Python语法..."
cd backend
python -m py_compile api/*.py core/*.py db/*.py models/*.py services/*.py 2>/dev/null || true
cd ..
check "Python语法检查通过"

# 2. 检查JSON语法
echo ""
echo ">>> 检查JSON文件..."
cd miniapp
for file in $(find . -name "*.json"); do
    python -m json.tool "$file" > /dev/null 2>&1 || { echo "Invalid JSON: $file"; exit 1; }
done
check "JSON文件检查通过"

# 3. 检查项目结构
echo ""
echo ">>> 检查项目结构..."
[ -d "backend/api" ] || { echo "Missing backend/api"; exit 1; }
[ -d "miniapp/pages" ] || { echo "Missing miniapp/pages"; exit 1; }
[ -d "scripts" ] || { echo "Missing scripts"; exit 1; }
check "项目结构完整"

# 4. 检查版本文件
echo ""
echo ">>> 检查版本信息..."
[ -f "backend/version.py" ] || { echo "Missing version.py"; exit 1; }
VERSION=$(grep VERSION backend/version.py | cut -d'"' -f2)
check "版本: $VERSION"

# 5. Git状态
echo ""
echo ">>> 检查Git状态..."
if [ -n "$(git status --porcelain)" ]; then
    warn "有未提交的更改:"
    git status --short
else
    echo -e "${GREEN}✓${NC} 工作区干净"
fi

# 6. 检查远程更新
echo ""
echo ">>> 检查远程更新..."
git fetch origin --quiet
if git log HEAD..origin/main --oneline | grep -q .; then
    warn "有远程更新需要拉取:"
    git log HEAD..origin/main --oneline
else
    echo -e "${GREEN}✓${NC} 无需拉取远程更新"
fi

echo ""
echo "========================================"
echo -e "${GREEN} 检查完成!${NC}"
echo "========================================"
