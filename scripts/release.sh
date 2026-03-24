#!/bin/bash
# 打包发布脚本 - 自动打包并发布到 Gitee Releases
# 用法: ./scripts/release.sh [version]

set -e

REMOTE="gitee"
BRANCH="main"
VERSION_FILE="backend/version.py"

# 检查并同步代码
sync_code() {
    echo "📥 同步远程代码..."
    git fetch $REMOTE
    LOCAL=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse $REMOTE/$BRANCH)
    
    if [ "$LOCAL" != "$REMOTE_COMMIT" ]; then
        echo "⚠️  本地和远程不同步，正在拉取..."
        git pull $REMOTE $BRANCH
    fi
}

# 获取版本号
get_version() {
    cat $VERSION_FILE
}

# 打包后端
package_backend() {
    local version=$1
    local output="mini-db-query-backend-v${version}.zip"
    echo "📦 打包后端: $output"
    
    cd /root/projects/mini-db-query
    zip -r "$output" backend/ -x "*.pyc" -x "__pycache__/*" -x "*.log"
    echo "✅ 后端打包完成: $output"
    echo "$output"
}

# 打包前端
package_frontend() {
    local version=$1
    local output="mini-db-query-miniapp-v${version}.zip"
    echo "📦 打包小程序: $output"
    
    cd /root/projects/mini-db-query
    zip -r "$output" miniapp/ -x "*.pyc" -x "__pycache__/*" -x "*.log"
    echo "✅ 小程序打包完成: $output"
    echo "$output"
}

# 打包数据库脚本
package_scripts() {
    local version=$1
    local output="mini-db-query-scripts-v${version}.zip"
    echo "📦 打包脚本: $output"
    
    cd /root/projects/mini-db-query
    zip -r "$output" scripts/ backend/migrations/ -x "*.pyc" -x "__pycache__/*"
    echo "✅ 脚本打包完成: $output"
    echo "$output"
}

# 创建 Release 并上传
create_release() {
    local version=$1
    local tag="v$version"
    
    echo "🏷️  创建 Gitee Tag: $tag"
    
    cd /root/projects/mini-db-query
    git tag -a "$tag" -m "Release v$version"
    git push $REMOTE "$tag"
    
    echo "✅ Tag 已推送，请访问 Gitee 创建 Release："
    echo "   https://gitee.com/xhy1230/mini-db-query/releases/new?tag=$tag"
}

# 完整打包流程
full_release() {
    cd /root/projects/mini-db-query
    
    echo "================================"
    echo "  自动打包发布工具"
    echo "================================"
    
    # 同步代码
    sync_code
    
    # 获取版本号
    VERSION=$(get_version)
    echo "📌 当前版本: $VERSION"
    
    # 清理旧包
    rm -f mini-db-query-*.zip
    
    # 打包
    BACKEND_PKG=$(package_backend $VERSION)
    FRONTEND_PKG=$(package_frontend $VERSION)
    SCRIPTS_PKG=$(package_scripts $VERSION)
    
    echo ""
    echo "================================"
    echo "  打包完成！"
    echo "================================"
    echo ""
    echo "📦 生成的文件："
    echo "   $BACKEND_PKG"
    echo "   $FRONTEND_PKG"
    echo "   $SCRIPTS_PKG"
    echo ""
    
    # 创建 Tag
    create_release $VERSION
    
    echo ""
    echo "📝 下一步："
    echo "   1. 访问 Gitee 创建 Release"
    echo "   2. 上传以上 zip 文件"
    echo "   3. 下载部署到服务器"
}

# 主流程
main() {
    cd /root/projects/mini-db-query
    
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        echo "用法:"
        echo "  $0              # 完整打包发布流程"
        echo "  $0 backend      # 仅打包后端"
        echo "  $0 frontend     # 仅打包小程序"
        echo "  $0 scripts      # 仅打包脚本"
        echo "  $0 tag          # 仅创建 Tag"
        exit 0
    fi
    
    case "$1" in
        backend)
            sync_code
            package_backend $(get_version)
            ;;
        frontend)
            sync_code
            package_frontend $(get_version)
            ;;
        scripts)
            sync_code
            package_scripts $(get_version)
            ;;
        tag)
            sync_code
            create_release $(get_version)
            ;;
        *)
            full_release
            ;;
    esac
}

main "$@"
