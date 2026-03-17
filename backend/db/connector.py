# -*- coding: utf-8 -*-

"""
多源数据查询助手 —— 数据库连接器模块

Author: 飞书百万（AI助手）
"""

import logging
from typing import Dict, Any, Optional, List

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    SQLAlchemyError = Exception

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

# 设置模块日志（必须在使用logger之前定义）
logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

# Oracle驱动检查（支持新版oracledb和旧版cx_Oracle）
ORACLE_DRIVER = None
ORACLE_AVAILABLE = False
ORACLE_THICK_MODE = False

try:
    import oracledb
    # 显式使用thin模式（不需要Oracle Client）
    # oracledb默认就是thin模式，无需调用init_oracle_client()
    ORACLE_DRIVER = "oracledb"
    ORACLE_AVAILABLE = True
    ORACLE_THICK_MODE = False
    logger.info("Oracle驱动已加载: oracledb (thin模式，无需Oracle Client)")
except ImportError:
    try:
        import cx_Oracle
        ORACLE_DRIVER = "cx_oracle"
        ORACLE_AVAILABLE = True
        ORACLE_THICK_MODE = True
        logger.warning("Oracle驱动已加载: cx_Oracle (需要Oracle Instant Client)")
    except ImportError:
        ORACLE_DRIVER = None
        ORACLE_AVAILABLE = False
        ORACLE_THICK_MODE = False


def parse_connection_error(error: Exception, db_type: str, config: Dict[str, Any]) -> Dict[str, str]:
    """
    解析连接错误，返回详细的错误信息
    
    Returns:
        Dict with keys: error_type, error_title, error_message, suggestion
    """
    error_str = str(error)
    error_type = "unknown"
    host = config.get('host', 'unknown')
    port = config.get('port', 'unknown')
    database = config.get('db_name', 'unknown')
    username = config.get('username', 'unknown')
    
    # 网络相关错误
    network_keywords = [
        'Connection refused', 'Network is unreachable', 'No route to host',
        'timed out', 'timeout', 'Connection reset', 'Software caused connection abort',
        'Can\'t connect', 'Failed to connect', 'connection could not be established',
        'GnuTLS', 'TLS', 'SSL', 'socket', 'hostname'
    ]
    
    # 认证相关错误
    auth_keywords = [
        'Access denied', 'authentication failed', 'Authentication failed',
        'invalid username', 'invalid password', 'login failed', 'ORA-01017',
        'ORA-1017', 'invalid credentials', 'user name or password'
    ]
    
    # 数据库不存在错误
    db_not_found_keywords = [
        'Unknown database', 'database does not exist', 'ORA-12514',
        'ORA-12505', 'service name', 'SID', '无法解析指定的连接标识符'
    ]
    
    # 驱动/客户端错误
    driver_keywords = [
        'DPI-1047', 'Cannot locate', 'Oracle Client', 'client library',
        'driver not found', 'module not found', 'No module named'
    ]
    
    # 配置错误
    config_keywords = [
        'invalid port', 'invalid host', 'invalid connection',
        'ORA-12541', 'TNS:no listener', 'ORA-12560'
    ]
    
    # 判断错误类型
    for kw in network_keywords:
        if kw.lower() in error_str.lower():
            error_type = "network"
            break
    
    if error_type == "unknown":
        for kw in auth_keywords:
            if kw.lower() in error_str.lower():
                error_type = "auth"
                break
    
    if error_type == "unknown":
        for kw in db_not_found_keywords:
            if kw.lower() in error_str.lower():
                error_type = "database_not_found"
                break
    
    if error_type == "unknown":
        for kw in driver_keywords:
            if kw.lower() in error_str.lower():
                error_type = "driver"
                break
    
    if error_type == "unknown":
        for kw in config_keywords:
            if kw.lower() in error_str.lower():
                error_type = "config"
                break
    
    # 构建详细错误信息
    result = {
        'error_type': error_type,
        'error_title': '',
        'error_message': '',
        'suggestion': '',
        'connection_info': f"数据源: {db_type}\n主机: {host}:{port}\n数据库: {database}\n用户: {username}"
    }
    
    if error_type == "network":
        result['error_title'] = "🌐 网络连接错误"
        result['error_message'] = f"无法连接到服务器 {host}:{port}"
        result['suggestion'] = """请检查：
1. 服务器地址是否正确
2. 端口号是否正确（MySQL默认3306，Oracle默认1521，SQL Server默认1433）
3. 服务器是否开机且数据库服务正在运行
4. 防火墙是否允许该端口访问
5. 网络是否通畅（可尝试ping测试）"""
        
    elif error_type == "auth":
        result['error_title'] = "🔐 认证失败"
        result['error_message'] = f"用户名或密码错误"
        result['suggestion'] = """请检查：
1. 用户名是否正确
2. 密码是否正确（注意大小写）
3. 该用户是否有访问该数据库的权限
4. 数据库用户是否被锁定"""
        
    elif error_type == "database_not_found":
        result['error_title'] = "📁 数据库不存在"
        result['error_message'] = f"数据库/服务 '{database}' 不存在或无法访问"
        result['suggestion'] = """请检查：
1. 数据库名称/服务名是否正确
2. 数据库是否已创建
3. Oracle用户：确认是SID还是Service Name
4. 用户是否有访问该数据库的权限"""
        
    elif error_type == "driver":
        result['error_title'] = "⚙️ 驱动程序错误"
        if "DPI-1047" in error_str or "Oracle Client" in error_str:
            result['error_message'] = "Oracle客户端库未安装"
            result['suggestion'] = """Oracle连接需要安装Oracle Instant Client：

方法一：安装Oracle Instant Client
1. 下载：https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html
2. 解压到如 C:\\oracle\\instantclient_19_24
3. 将该路径添加到系统PATH环境变量（放在最前面）
4. 重启工具

方法二：等待新版本
新版将使用oracledb thin模式，无需Oracle Client"""
        else:
            result['error_message'] = f"数据库驱动程序问题"
            result['suggestion'] = "请联系开发者或重新安装工具"
        
    elif error_type == "config":
        result['error_title'] = "⚙️ 配置错误"
        result['error_message'] = f"连接配置有误"
        result['suggestion'] = """请检查：
1. 主机地址格式是否正确
2. 端口号是否为有效数字
3. Oracle用户：确认监听器是否启动
4. 检查数据库服务是否正在运行"""
        
    else:
        result['error_title'] = "❌ 连接失败"
        result['error_message'] = f"未知错误: {error_str[:200]}"
        result['suggestion'] = """请检查：
1. 所有连接参数是否正确
2. 网络是否通畅
3. 数据库服务是否运行

原始错误信息：""" + error_str
    
    return result


def check_dependencies():
    """检查数据库依赖是否安装"""
    missing = []
    if not SQLALCHEMY_AVAILABLE:
        missing.append("sqlalchemy")
    if not PYMYSQL_AVAILABLE:
        missing.append("pymysql")
    # pyodbc 和 oracledb 是可选的
    return missing


def check_oracle_driver():
    """检查Oracle驱动是否可用"""
    if ORACLE_AVAILABLE:
        return ORACLE_DRIVER
    return None


class DatabaseConnector:
    """数据库连接器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engine: Optional[Engine] = None
        
    def connect(self) -> bool:
        """建立数据库连接"""
        try:
            # 检查依赖
            missing = check_dependencies()
            if missing:
                raise ImportError(f"缺少必要的数据库驱动: {', '.join(missing)}")
            
            self.engine = self._create_engine()
            # 测试连接是否有效
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM DUAL" if self.config.get('db_type') == 'Oracle' else "SELECT 1"))
            logger.info(f"数据库连接成功: {self.config.get('db_type')}:{self.config.get('host')}/{self.config.get('db_name')}")
            return True
        except ImportError as e:
            logger.error(f"缺少依赖: {e}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"数据库连接失败 [{self.config.get('db_type')}] {e}")
            self.engine = None
            return False
        except Exception as e:
            logger.error(f"连接异常 [{self.config.get('db_type')}] {e}")
            self.engine = None
            return False
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            engine = self._create_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM DUAL" if self.config.get('db_type') == 'Oracle' else "SELECT 1"))
            engine.dispose()
            return True
        except Exception:
            return False
    
    def get_connection(self):
        """获取数据库连接"""
        if not self.engine:
            if not self.connect():
                raise ConnectionError(f"无法连接数据库: {self.config.get('db_type')}")
        return self.engine
    
    def _create_engine(self) -> Engine:
        """创建数据库引擎（由子类实现）"""
        raise NotImplementedError("子类必须实现 _create_engine 方法")
    
    def execute_query(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """执行查询"""
        if not query or not query.strip():
            logger.warning("查询语句为空")
            return None
            
        try:
            engine = self.get_connection()
            with engine.connect() as conn:
                result = conn.execute(text(query))
                
                if result.returns_rows:
                    columns = result.keys()
                    rows = result.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    return []
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise
    
    def close(self):
        """关闭连接"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            logger.info(f"数据库连接已关闭: {self.config.get('db_type')}")


class MySQLConnector(DatabaseConnector):
    """MySQL 数据库连接器"""
    
    def _create_engine(self) -> Engine:
        db_config = self.config
        # URL编码密码中的特殊字符
        from urllib.parse import quote_plus
        password = quote_plus(str(db_config.get('password', '')))
        
        connection_string = (
            f"mysql+pymysql://{db_config.get('username')}:"
            f"{password}@{db_config.get('host')}:"
            f"{db_config.get('port')}/{db_config.get('db_name')}?charset=utf8mb4"
        )
        logger.debug(f"创建MySQL连接: {db_config.get('host')}:{db_config.get('port')}/{db_config.get('db_name')}")
        return create_engine(connection_string, pool_pre_ping=True, pool_recycle=3600)
    

class OracleConnector(DatabaseConnector):
    """Oracle 数据库连接器"""
    
    def _create_engine(self) -> Engine:
        db_config = self.config
        
        # 检查Oracle驱动
        if not ORACLE_AVAILABLE:
            raise ImportError(
                "Oracle驱动未安装！\n"
                "请安装Oracle驱动:\n"
                "  pip install oracledb\n"
                "或安装旧版:\n"
                "  pip install cx_Oracle\n"
                "注意: cx_Oracle还需要安装Oracle Instant Client"
            )
        
        from urllib.parse import quote_plus
        password = quote_plus(str(db_config.get('password', '')))
        
        # 构建DSN
        host = db_config.get('host', 'localhost')
        port = db_config.get('port', 1521)
        database = db_config.get('db_name', '')
        
        # 支持两种格式: host:port/service_name 或完整DSN
        dsn = f"{host}:{port}/{database}"
        
        # 使用检测到的Oracle驱动
        connection_string = (
            f"oracle+{ORACLE_DRIVER}://{db_config.get('username')}:"
            f"{password}@{dsn}"
        )
        
        logger.info(f"创建Oracle连接: {host}:{port}/{database} (驱动: {ORACLE_DRIVER})")
        
        # oracledb 需要使用 thick 模式或 thin 模式
        # thin 模式不需要Oracle Client，更简单
        engine = create_engine(connection_string, pool_pre_ping=True)
        
        return engine
    

class SQLServerConnector(DatabaseConnector):
    """SQL Server 数据库连接器"""
    
    def _create_engine(self) -> Engine:
        db_config = self.config
        from urllib.parse import quote_plus
        password = quote_plus(str(db_config.get('password', '')))
        
        connection_string = (
            f"mssql+pyodbc://{db_config.get('username')}:"
            f"{password}@{db_config.get('host')}:"
            f"{db_config.get('port')}/{db_config.get('db_name')}?"
            f"driver=ODBC+Driver+17+for+SQL+Server"
        )
        return create_engine(connection_string, pool_pre_ping=True)


class SQLiteConnector(DatabaseConnector):
    """SQLite 数据库连接器（本地文件）"""
    
    def _create_engine(self) -> Engine:
        db_config = self.config
        database = db_config.get('db_name', '')
        
        # 支持相对路径和绝对路径
        connection_string = f"sqlite:///{database}"
        logger.debug(f"创建SQLite连接: {database}")
        return create_engine(connection_string, pool_pre_ping=True)


def get_connector(connector_type: str, config: Optional[Dict[str, Any]] = None) -> DatabaseConnector:
    """根据数据库类型返回对应的连接器实例"""
    if config is None:
        raise ValueError("数据库配置不能为空")
    
    connector_map = {
        'MySQL': MySQLConnector,
        'Oracle': OracleConnector,
        'SQLServer': SQLServerConnector,
        'SQLite': SQLiteConnector
    }
    
    # SQLite不需要检查这些字段
    if connector_type != 'SQLite':
        # 检查必要字段
        required_fields = ['host', 'port', 'username', 'password', 'database']
        missing_fields = [f for f in required_fields if not config.get(f)]
        if missing_fields:
            raise ValueError(f"配置缺少必要字段: {', '.join(missing_fields)}")
    
    connector_cls = connector_map.get(connector_type)
    if not connector_cls:
        supported = ', '.join(connector_map.keys())
        raise ValueError(f"不支持的数据库类型: {connector_type}。支持的类型有: {supported}")
    
    return connector_cls(config)


def list_configs() -> List[str]:
    """列出所有可用的配置名称"""
    try:
        from src.config.settings import CONFIG_FILE_PATH
        from src.utils.file import load_yaml
        configs = load_yaml(CONFIG_FILE_PATH) or {}
        return list(configs.keys())
    except Exception:
        return []
