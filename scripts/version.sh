#!/bin/bash
# 版本管理脚本 - 确保本地和远程版本一致
# 用法: ./scripts/version.sh <new_version> [commit_message]

set -e

VERSION_FILE="backend/version.py"
REMOTE="gitee"
BRANCH="main"

# 检查是否有未提交的更改
check_clean() {
    if ! git diff --quiet; then
        echo "⚠️  有未提交的更改，请先处理："
        git status --short
        exit 1
    fi
}

# 拉取最新代码
sync_remote() {
    echo "📥 同步远程代码..."
    git fetch $REMOTE
    LOCAL=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse $REMOTE/$BRANCH)
    
    if [ "$LOCAL" != "$REMOTE_COMMIT" ]; then
        echo "⚠️  本地和远程不同步，正在拉取..."
        git pull $REMOTE $BRANCH
    else
        echo "✅ 本地和远程已同步"
    fi
}

# 更新版本号
update_version() {
    local new_version=$1
    echo "📝 更新版本号到 $new_version ..."
    echo "$new_version" > $VERSION_FILE
}

# 提交并推送
commit_and_push() {
    local version=$1
    local message=$2
    
    if [ -z "$message" ]; then
        message="chore: 版本更新到 v$version"
    fi
    
    git add $VERSION_FILE
    git commit -m "$message"
    git push $REMOTE $BRANCH
    
    echo "✅ 已推送到远程: $(git log -1 --oneline)"
}

# 显示当前版本
show_version() {
    echo "📌 当前版本: $(cat $VERSION_FILE)"
    echo "📌 Git 提交: $(git log -1 --oneline)"
}

# 主流程
main() {
    cd /root/projects/mini-db-query
    
    echo "================================"
    echo "  版本管理工具"
    echo "================================"
    
    if [ -z "$1" ]; then
        echo ""
        echo "用法:"
        echo "  $0 <version>           # 更新版本并推送"
        echo "  $0 <version> <message> # 更新版本并推送（自定义提交信息）"
        echo "  $0 status              # 查看当前状态"
        echo ""
        show_version
        exit 0
    fi
    
    if [ "$1" = "status" ]; then
        show_version
        git status --short
        exit 0
    fi
    
    NEW_VERSION=$1
    COMMIT_MSG=$2
    
    # 执行流程
    check_clean
    sync_remote
    update_version $NEW_VERSION
    commit_and_push $NEW_VERSION "$COMMIT_MSG"
    
    echo ""
    echo "✅ 完成！版本已更新到 v$NEW_VERSION"
}

main "$@"
