#!/bin/bash
# 增量升级包生成脚本
# 用法: ./scripts/upgrade.sh <from_version> [to_version]

set -e

REMOTE="gitee"
BRANCH="main"
CURRENT_VERSION=$(cat backend/version.py)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 获取版本对应的 commit
get_version_commit() {
    local version=$1
    # 尝试在 CHANGELOG 或 tag 中查找
    git log --oneline --all | grep -i "$version" | head -1 | awk '{print $1}'
}

# 获取两个 commit 之间的差异文件
get_changed_files() {
    local from_commit=$1
    local to_commit=$2
    
    if [ -z "$from_commit" ]; then
        # 没有起始版本，完整打包
        echo "FULL"
        return
    fi
    
    git diff --name-only "$from_commit".."$to_commit" 2>/dev/null || git diff --name-only "$from_commit" "$to_commit"
}

# 打包增量升级包
package_incremental() {
    local from_version=$1
    local to_version=${2:-$CURRENT_VERSION}
    
    log_info "生成增量升级包: $from_version -> $to_version"
    
    # 获取 commit
    local from_commit=$(git log --oneline --all | grep -i "$from_version" | head -1 | awk '{print $1}')
    local to_commit=$(git rev-parse HEAD)
    
    if [ -z "$from_commit" ]; then
        log_warn "未找到版本 $from_version 的提交，使用完整打包"
        package_full "$to_version"
        return
    fi
    
    log_info "从 commit: $from_commit"
    log_info "到 commit: $to_commit"
    
    # 获取变更文件
    local changed_files=$(get_changed_files "$from_commit" "$to_commit")
    
    if [ "$changed_files" = "FULL" ]; then
        log_warn "无法确定差异，执行完整打包"
        package_full "$to_version"
        return
    fi
    
    # 统计变更
    local file_count=$(echo "$changed_files" | wc -l)
    log_info "变更文件数: $file_count"
    
    if [ "$file_count" -eq 0 ]; then
        log_warn "没有变更文件"
        return
    fi
    
    # 创建输出目录
    local output_dir="upgrade_${from_version}_to_${to_version}"
    mkdir -p "$output_dir"
    
    # 复制变更文件
    echo "$changed_files" | while read -r file; do
        if [ -f "$file" ]; then
            local dir=$(dirname "$file")
            mkdir -p "$output_dir/$dir"
            cp -r "$file" "$output_dir/$dir/"
            echo "  + $file"
        fi
    done
    
    # 打包
    local zip_name="upgrade_${from_version}_to_${to_version}.zip"
    zip -r "$zip_name" "$output_dir/"
    
    # 生成升级说明
    cat > "${output_dir}/UPGRADE.md" << EOF
# 升级说明

## 从 $from_version 升级到 $to_version

### 变更文件
\`\`\`
$changed_files
\`\`\"

### 升级步骤
1. 解压此升级包
2. 覆盖到对应目录
3. 重启服务（如有必要）
4. 执行数据库升级（如有必要）

### 数据库升级
如有数据库变更，请执行 \`backend/migrations/\` 目录下的 SQL 文件
EOF
    
    log_info "✅ 增量升级包生成完成: ${zip_name}"
    log_info "📁 包含文件:"
    echo "$changed_files" | head -20 | while read -r file; do
        echo "   - $file"
    done
    
    if [ "$file_count" -gt 20 ]; then
        echo "   ... 还有 $((file_count - 20)) 个文件"
    fi
    
    # 清理临时目录
    rm -rf "$output_dir"
    
    echo ""
    log_info "输出文件: ${zip_name}"
}

# 打包完整升级包
package_full() {
    local version=${1:-$CURRENT_VERSION}
    local zip_name="mini-db-query-upgrade-${version}.zip"
    
    log_info "生成完整升级包: $version"
    
    # 清理旧包
    rm -f "$zip_name"
    
    # 打包后端
    zip -r "$zip_name" backend/ -x "*.pyc" -x "__pycache__/*" -x "*.log"
    
    # 打包迁移脚本
    zip -r "$zip_name" backend/migrations/
    
    log_info "✅ 完整升级包: $zip_name"
}

# 显示版本列表
show_versions() {
    log_info "可用版本:"
    git log --oneline --all | head -20 | while read -r line; do
        echo "  $line"
    done
}

# 主流程
main() {
    cd /root/projects/mini-db-query
    
    echo "================================"
    echo "  增量升级包生成工具"
    echo "================================"
    echo ""
    
    # 同步代码
    log_info "同步远程代码..."
    git fetch $REMOTE
    git pull $REMOTE $BRANCH 2>/dev/null || true
    
    local current=$(cat backend/version.py)
    log_info "当前版本: $current"
    echo ""
    
    case "$1" in
        -h|--help)
            echo "用法:"
            echo "  $0                          # 完整打包当前版本"
            echo "  $0 v1.2.2.01                # 从 v1.2.2.01 打包增量到最新"
            echo "  $0 v1.2.2.01 v1.2.2.12     # 从 v1.2.2.01 打包到 v1.2.2.12"
            echo "  $0 versions                 # 显示可用版本"
            exit 0
            ;;
        versions|list)
            show_versions
            exit 0
            ;;
        "")
            package_full "$current"
            ;;
        *)
            package_incremental "$1" "$2"
            ;;
    esac
}

main "$@"
