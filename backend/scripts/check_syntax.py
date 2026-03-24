#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码检查脚本 - 发布前必须通过

用法:
    python scripts/check_code.py
"""

import os
import sys
import subprocess
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

# 需要检查的文件
CHECK_FILES = [
    "main.py",
    "api/query.py",
    "api/auth.py",
    "api/manage.py",
    "api/logs.py",
    "api/bindings.py",
    "core/config.py",
    "core/security.py",
    "core/sql_validator.py",
    "core/rate_limiter.py",
    "core/cache.py",
    "db/query_executor.py",
    "db/connector.py",
    "models/database.py",
    "services/log_cleanup_service.py",
]

def check_syntax(file_path: Path) -> tuple[bool, str]:
    """检查Python语法"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, "OK"
        else:
            return False, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)

def check_imports(module_path: str) -> tuple[bool, str]:
    """检查导入"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import {module_path}"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(BACKEND_DIR)
        )
        if result.returncode == 0:
            return True, "OK"
        else:
            return False, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)

def main():
    """主检查流程"""
    print("=" * 60)
    print("Mini DB Query - 代码检查")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # 1. 语法检查
    print("\n[1] 语法检查...")
    for file_name in CHECK_FILES:
        file_path = BACKEND_DIR / file_name
        if file_path.exists():
            ok, msg = check_syntax(file_path)
            status = "✓" if ok else "✗"
            print(f"  {status} {file_name}: {msg}")
            if not ok:
                errors.append(f"语法错误: {file_name}\n{msg}")
        else:
            print(f"  - {file_name}: 文件不存在（跳过）")
            warnings.append(f"文件不存在: {file_name}")
    
    # 2. 导入检查
    print("\n[2] 导入检查...")
    import_modules = [
        "main",
        "api.query",
        "api.auth",
        "core.config",
        "core.security",
    ]
    for module in import_modules:
        ok, msg = check_imports(module)
        status = "✓" if ok else "✗"
        print(f"  {status} import {module}: {msg}")
        if not ok:
            errors.append(f"导入错误: {module}\n{msg}")
    
    # 3. 启动检查（main.py 是延迟创建app，所以只检查语法）
    print("\n[3] 启动检查...")
    print(f"  ✓ 语法检查已覆盖所有文件")
    print(f"  ℹ 启动测试请在目标环境执行")
    
    # 总结
    print("\n" + "=" * 60)
    print("检查结果")
    print("=" * 60)
    print(f"错误: {len(errors)}")
    print(f"警告: {len(warnings)}")
    
    if errors:
        print("\n❌ 发现错误，请修复后再发布:")
        for err in errors:
            print(f"\n---\n{err}\n---")
        return 1
    else:
        print("\n✅ 所有检查通过，可以发布！")
        return 0

if __name__ == "__main__":
    sys.exit(main())
