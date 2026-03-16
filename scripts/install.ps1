# ============================================
# 多源数据查询小程序版 - PowerShell安装脚本
# 版本: v1.0.0
# 用法: powershell -ExecutionPolicy Bypass -File install.ps1
# ============================================

param(
    [string]$MysqlHost = "localhost",
    [int]$MysqlPort = 3306,
    [string]$MysqlUser = "root",
    [string]$MysqlPassword = "",
    [string]$Database = "mini_db_query",
    [string]$AdminPassword = "admin123",
    [switch]$SkipMysql,
    [switch]$Quiet
)

# 配置
$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectDir "backend"
$DatabaseDir = Join-Path $ProjectDir "database"

# 日志函数
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Green }
function Write-Warn { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Err { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Write-Step { 
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $args -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

# 检查管理员权限
function Test-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 安装Python
function Install-Python {
    Write-Step "安装Python环境"
    
    # 检查Python
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        $version = & python --version 2>&1
        Write-Info "已安装 $version"
        return $true
    }
    
    Write-Warn "未检测到Python，准备安装..."
    
    # 下载Python安装程序
    $pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
    $installerPath = Join-Path $env:TEMP "python-installer.exe"
    
    try {
        Write-Info "下载Python 3.12..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -UseBasicParsing
        
        Write-Info "安装Python..."
        Start-Process -FilePath $installerPath -ArgumentList @(
            "/quiet",
            "InstallAllUsers=0",
            "PrependPath=1",
            "Include_test=0",
            "Include_pip=1"
        ) -Wait
        
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + 
                    [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        
        Write-Info "Python安装完成"
        return $true
    }
    catch {
        Write-Err "Python安装失败: $_"
        Write-Warn "请手动安装Python 3.10+: https://www.python.org/downloads/"
        return $false
    }
}

# 创建虚拟环境
function New-VirtualEnv {
    Write-Step "创建Python虚拟环境"
    
    Push-Location $BackendDir
    
    $venvPath = Join-Path $BackendDir "venv"
    
    if (Test-Path $venvPath) {
        Write-Warn "虚拟环境已存在，跳过创建"
    }
    else {
        Write-Info "创建虚拟环境..."
        & python -m venv venv
        Write-Info "虚拟环境创建完成"
    }
    
    # 激活
    & "$venvPath\Scripts\Activate.ps1"
    
    # 升级pip
    & python -m pip install --upgrade pip --quiet
    
    Pop-Location
}

# 安装依赖
function Install-Dependencies {
    Write-Step "安装Python依赖"
    
    Push-Location $BackendDir
    
    $requirementsPath = Join-Path $BackendDir "requirements.txt"
    
    if (Test-Path $requirementsPath) {
        Write-Info "安装依赖包..."
        & pip install -r requirements.txt --quiet
        Write-Info "依赖包安装完成"
    }
    else {
        throw "未找到 requirements.txt"
    }
    
    # 安装额外依赖
    & pip install pymysql cryptography --quiet
    
    Pop-Location
}

# 配置MySQL
function Initialize-MySQL {
    Write-Step "配置MySQL数据库"
    
    # 检查MySQL服务
    $mysqlService = Get-Service -Name "MySQL*" -ErrorAction SilentlyContinue | 
                    Where-Object { $_.Status -eq "Running" } | 
                    Select-Object -First 1
    
    if (-not $mysqlService) {
        Write-Warn "未检测到运行中的MySQL服务"
        Write-Warn "请确保已安装MySQL 8.0.2+并启动服务"
        
        if (-not $SkipMysql) {
            $continue = Read-Host "是否已完成MySQL安装并继续? (Y/N)"
            if ($continue -ne "Y") {
                Write-Warn "安装已暂停"
                exit 0
            }
        }
    }
    else {
        Write-Info "检测到MySQL服务: $($mysqlService.Name)"
    }
    
    # 获取MySQL密码
    if (-not $MysqlPassword) {
        $MysqlPassword = Read-Host "请输入MySQL root密码"
    }
    
    # 创建数据库初始化SQL
    $initSql = @"
CREATE DATABASE IF NOT EXISTS `$Database` DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'mini_query'@'localhost' IDENTIFIED BY 'MiniQuery@2026';
CREATE USER IF NOT EXISTS 'mini_query'@'%' IDENTIFIED BY 'MiniQuery@2026';
GRANT ALL PRIVILEGES ON `$Database`.* TO 'mini_query'@'localhost';
GRANT ALL PRIVILEGES ON `$Database`.* TO 'mini_query'@'%';
FLUSH PRIVILEGES;
"@
    
    $initSqlPath = Join-Path $env:TEMP "init_db.sql"
    $initSql | Out-File -FilePath $initSqlPath -Encoding UTF8
    
    # 执行SQL
    $mysqlExe = Get-Command mysql -ErrorAction SilentlyContinue
    if ($mysqlExe) {
        Write-Info "创建数据库..."
        & mysql -h$MysqlHost -P$MysqlPort -u$MysqlUser -p$MysqlPassword < $initSqlPath 2>$null
        Write-Info "数据库创建完成"
        
        # 创建表结构
        $schemaPath = Join-Path $DatabaseDir "mysql_schema.sql"
        if (Test-Path $schemaPath) {
            Write-Info "创建数据表..."
            & mysql -h$MysqlHost -P$MysqlPort -u$MysqlUser -p$MysqlPassword $Database < $schemaPath 2>$null
            Write-Info "数据表创建完成"
        }
    }
    else {
        Write-Warn "未找到mysql命令，请手动执行SQL"
        Write-Host $initSql
    }
}

# 创建配置文件
function New-Config {
    Write-Step "创建配置文件"
    
    # 生成JWT密钥
    $jwtSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object { [char]$_ })
    
    $envContent = @"
# 多源数据查询小程序版 - 配置文件
# 自动生成于 $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# 数据库配置
DATABASE_URL=mysql+pymysql://mini_query:MiniQuery@2026@$MysqlHost`:$MysqlPort/$Database?charset=utf8mb4

# 微信小程序配置 (请修改为实际值)
WECHAT_APPID=your_wechat_appid
WECHAT_SECRET=your_wechat_secret

# JWT配置
JWT_SECRET_KEY=$jwtSecret
JWT_EXPIRE_MINUTES=10080

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=False

# 查询配置
QUERY_TIMEOUT=30
MAX_EXPORT_ROWS=10000
"@
    
    $envPath = Join-Path $BackendDir ".env"
    $envContent | Out-File -FilePath $envPath -Encoding UTF8
    
    Write-Info "配置文件创建完成: $envPath"
}

# 创建快捷方式
function New-Shortcuts {
    Write-Step "创建快捷方式"
    
    $WshShell = New-Object -ComObject WScript.Shell
    
    # 桌面快捷方式
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktopPath "查询小程序服务.lnk"
    
    $shortcut = $WshShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = Join-Path $BackendDir "venv\Scripts\python.exe"
    $shortcut.Arguments = "main.py"
    $shortcut.WorkingDirectory = $BackendDir
    $shortcut.Description = "多源数据查询小程序服务"
    $shortcut.Save()
    
    Write-Info "桌面快捷方式创建完成"
    
    # 启动脚本
    $startBat = @"
@echo off
chcp 65001 >nul
cd /d "$BackendDir"
call venv\Scripts\activate.bat
echo 启动服务中...
python main.py
pause
"@
    $startBat | Out-File -FilePath (Join-Path $PSScriptRoot "start-service.bat") -Encoding UTF8
    
    # 停止脚本
    $stopBat = @"
@echo off
echo 正在停止服务...
taskkill /f /im python.exe 2>nul
echo 服务已停止
timeout /t 3
"@
    $stopBat | Out-File -FilePath (Join-Path $PSScriptRoot "stop-service.bat") -Encoding UTF8
    
    Write-Info "启动/停止脚本创建完成"
}

# 创建Windows服务
function New-WindowsService {
    param(
        [string]$ServiceName = "MiniDbQuery",
        [string]$DisplayName = "多源数据查询小程序",
        [string]$Description = "提供多源数据库查询API服务"
    )
    
    Write-Step "创建Windows服务"
    
    # 检查是否以管理员运行
    if (-not (Test-Admin)) {
        Write-Warn "需要管理员权限创建Windows服务"
        Write-Warn "请以管理员身份重新运行PowerShell"
        return
    }
    
    # 检查服务是否存在
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Warn "服务已存在: $ServiceName"
        return
    }
    
    # 使用NSSM或sc创建服务
    $nssmPath = Join-Path $PSScriptRoot "nssm.exe"
    
    if (Test-Path $nssmPath) {
        # 使用NSSM
        & $nssmPath install $ServiceName (Join-Path $BackendDir "venv\Scripts\python.exe") "main.py"
        & $nssmPath set $ServiceName AppDirectory $BackendDir
        & $nssmPath set $ServiceName DisplayName $DisplayName
        & $nssmPath set $ServiceName Description $Description
        & $nssmPath set $ServiceName Start SERVICE_AUTO_START
    }
    else {
        # 使用sc
        $binPath = "`"$([Environment]::SystemDirectory)\cmd.exe`" /c `"cd /d $BackendDir && venv\Scripts\python.exe main.py`""
        & sc.exe create $ServiceName binPath= $binPath DisplayName= $DisplayName start= auto
    }
    
    Write-Info "Windows服务创建完成: $ServiceName"
}

# 主函数
function Main {
    Write-Host "`n============================================" -ForegroundColor Green
    Write-Host "   多源数据查询小程序版 - 安装向导" -ForegroundColor Green
    Write-Host "============================================`n" -ForegroundColor Green
    
    try {
        # 执行安装步骤
        Install-Python
        New-VirtualEnv
        Install-Dependencies
        
        if (-not $SkipMysql) {
            Initialize-MySQL
        }
        
        New-Config
        New-Shortcuts
        
        # 创建服务选项
        if (-not $Quiet) {
            $createService = Read-Host "是否创建Windows服务? (Y/N)"
            if ($createService -eq "Y") {
                New-WindowsService
            }
        }
        
        # 完成
        Write-Host "`n============================================" -ForegroundColor Green
        Write-Host "   安装完成!" -ForegroundColor Green
        Write-Host "============================================`n" -ForegroundColor Green
        
        Write-Host "数据库信息:"
        Write-Host "  数据库: $Database" -ForegroundColor Yellow
        Write-Host "  用户名: mini_query" -ForegroundColor Yellow
        Write-Host "  密码:   MiniQuery@2026" -ForegroundColor Yellow
        
        Write-Host "`n管理员账号:"
        Write-Host "  用户名: admin" -ForegroundColor Yellow
        Write-Host "  密码:   $AdminPassword" -ForegroundColor Yellow
        
        Write-Host "`n启动方式:"
        Write-Host "  1. 双击桌面快捷方式" -ForegroundColor Cyan
        Write-Host "  2. 运行 scripts\start-service.bat" -ForegroundColor Cyan
        Write-Host "  3. 启动Windows服务: net start MiniDbQuery" -ForegroundColor Cyan
        
        Write-Host "`n访问地址:"
        Write-Host "  API: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "  文档: http://localhost:8000/docs" -ForegroundColor Cyan
        
        Write-Host "`n" -NoNewline
        
        # 打开配置文件
        if (-not $Quiet) {
            $openConfig = Read-Host "是否打开配置文件进行编辑? (Y/N)"
            if ($openConfig -eq "Y") {
                notepad (Join-Path $BackendDir ".env")
            }
        }
    }
    catch {
        Write-Err "安装失败: $_"
        Write-Err $_.ScriptStackTrace
        exit 1
    }
}

# 运行
Main
