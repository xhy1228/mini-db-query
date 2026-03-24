# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 数据库模型 v1.2.0

Author: 飞书百万（AI助手）

架构说明:
- schools: 学校
- database_configs: 学校的数据库连接（每个学校可配置多个）
- query_templates: 通用查询模板（独立、可复用）
- school_template_bindings: 学校-模板绑定（指定学校用哪个数据库）
- query_fields: 查询条件
- template_permissions: 模板权限
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class School(Base):
    """学校/项目表"""
    __tablename__ = 'schools'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='学校名称')
    code = Column(String(50), unique=True, nullable=False, comment='学校编码')
    description = Column(Text, comment='描述')
    status = Column(String(20), default='active', comment='状态: active/inactive')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联 - v1.2.0 调整
    databases = relationship("DatabaseConfig", back_populates="school", cascade="all, delete-orphan")
    bindings = relationship("SchoolTemplateBinding", back_populates="school", cascade="all, delete-orphan")
    user_permissions = relationship("UserSchool", back_populates="school", cascade="all, delete-orphan")
    
    # 保留与旧版本的兼容
    templates = relationship("QueryTemplate", back_populates="school", cascade="all, delete-orphan")
    categories = relationship("TemplateCategory", back_populates="school", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DatabaseConfig(Base):
    """数据库配置表 - v1.2.0
    
    说明：每个学校可以配置多个数据库连接（MySQL、Oracle等）
    """
    __tablename__ = 'database_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    school_id = Column(Integer, ForeignKey('schools.id'), nullable=False, comment='学校ID')
    name = Column(String(100), nullable=False, comment='连接名称，如：MySQL消费库')
    db_type = Column(String(50), nullable=False, comment='数据库类型: MySQL/Oracle/SQLServer/SQLite')
    host = Column(String(255), nullable=False, comment='主机地址')
    port = Column(Integer, nullable=False, comment='端口')
    username = Column(String(100), nullable=False, comment='用户名')
    password = Column(Text, nullable=False, comment='密码(加密)')
    db_name = Column(String(100), comment='数据库名')
    service_name = Column(String(100), comment='Oracle服务名')
    driver = Column(String(100), comment='ODBC驱动')
    description = Column(Text, comment='描述')
    status = Column(String(20), default='active', comment='状态')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联 - v1.2.0 调整
    school = relationship("School", back_populates="databases")
    bindings = relationship("SchoolTemplateBinding", back_populates="database", cascade="all, delete-orphan")
    
    # 保留与旧版本的兼容
    templates = relationship("QueryTemplate", back_populates="database")
    
    def to_dict(self, include_password=False):
        result = {
            'id': self.id,
            'school_id': self.school_id,
            'name': self.name,
            'db_type': self.db_type,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'db_name': self.db_name,
            'service_name': self.service_name,
            'driver': self.driver,
            'description': self.description,
            'status': self.status
        }
        if include_password:
            result['password'] = self.password
        return result


class TemplateCategory(Base):
    """业务大类表 - v1.2.0
    
    说明：系统预置的业务分类，如消费、门禁、充值等
    """
    __tablename__ = 'template_categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    school_id = Column(Integer, ForeignKey('schools.id'), nullable=False, comment='学校ID(0表示系统预置)')
    code = Column(String(50), nullable=False, comment='业务大类编码')
    name = Column(String(100), nullable=False, comment='业务大类名称')
    icon = Column(String(50), comment='图标')
    sort_order = Column(Integer, default=0, comment='排序')
    description = Column(Text, comment='描述')
    status = Column(String(20), default='active', comment='状态')
    is_system = Column(Integer, default=0, comment='是否系统预置：1是 0否')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联
    school = relationship("School", back_populates="categories")
    templates = relationship("QueryTemplate", back_populates="category_obj")
    
    def to_dict(self):
        return {
            'id': self.id,
            'school_id': self.school_id,
            'code': self.code,
            'name': self.name,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'description': self.description,
            'status': self.status,
            'is_system': self.is_system
        }


class QueryTemplate(Base):
    """查询模板表 - v1.2.0 重构
    
    说明：通用模板，可被多个学校复用
    - category: 业务分类（consume/access/recharge等）
    - supported_db_types: 支持的数据库类型
    - 学校关联通过 school_template_bindings 表管理
    """
    __tablename__ = 'query_templates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    # v1.2.0: 移除 school_id 和 database_id，通过绑定表管理
    category = Column(String(50), nullable=False, comment='业务分类编码: consume/access/recharge')
    category_name = Column(String(100), comment='业务分类名称')
    category_icon = Column(String(20), comment='业务分类图标')
    name = Column(String(100), nullable=False, comment='模板名称')
    table_name = Column(String(100), comment='查询表名')
    description = Column(Text, comment='描述')
    sql_template = Column(Text, nullable=False, comment='SQL模板')
    select_columns = Column(JSON, comment='返回字段配置 [{"column": "CUSTNAME", "alias": "姓名"}, ...]')
    fields = Column(JSON, comment='查询字段配置(兼容旧版)')
    time_field = Column(String(100), comment='时间字段')
    default_limit = Column(Integer, default=500, comment='默认条数限制')
    supported_db_types = Column(JSON, comment='支持的数据库类型: ["MySQL", "Oracle"]')
    status = Column(String(20), default='active', comment='状态')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # v1.2.0: 新增关联
    bindings = relationship("SchoolTemplateBinding", back_populates="template", cascade="all, delete-orphan")
    
    # 保留与旧版本的兼容（可选字段）
    school_id = Column(Integer, ForeignKey('schools.id'), nullable=True, comment='学校ID(兼容旧版)')
    database_id = Column(Integer, ForeignKey('database_configs.id'), nullable=True, comment='数据库配置ID(兼容旧版)')
    category_id = Column(Integer, ForeignKey('template_categories.id'), nullable=True, comment='业务大类ID(兼容旧版)')
    version = Column(String(20), default='v1.0.0', comment='版本号(兼容旧版)')
    change_log = Column(Text, comment='变更日志(兼容旧版)')
    
    # 关联 - 保留兼容
    school = relationship("School", back_populates="templates")
    database = relationship("DatabaseConfig", back_populates="templates")
    category_obj = relationship("TemplateCategory", back_populates="templates")
    query_fields = relationship("QueryField", back_populates="template", cascade="all, delete-orphan")
    permissions = relationship("TemplatePermission", back_populates="template", cascade="all, delete-orphan")
    
    def to_dict(self):
        result = {
            'id': self.id,
            'category': self.category,
            'category_name': self.category_name,
            'category_icon': self.category_icon,
            'name': self.name,
            'description': self.description,
            'sql_template': self.sql_template,  # 添加sql_template字段
            'time_field': self.time_field,
            'default_limit': self.default_limit,
            'supported_db_types': self.supported_db_types or ['MySQL', 'Oracle'],
            'status': self.status,
            # 兼容旧版字段
            'school_id': self.school_id,
            'database_id': self.database_id,
            'category_id': self.category_id,
            'version': self.version,
        }
        
        # 字段处理：优先使用独立表字段，兼容旧版 fields 字段
        if self.query_fields and len(self.query_fields) > 0:
            result['fields'] = [
                {
                    'id': f.field_key,
                    'label': f.field_label,
                    'column': f.db_column or f.field_key,
                    'type': f.field_type or 'text',
                    'operator': f.operator or '=',
                    'default_value': f.default_value,
                    'options': f.options,
                    'required': bool(f.required),
                    'placeholder': f.placeholder
                }
                for f in sorted(self.query_fields, key=lambda x: x.sort_order)
            ]
        else:
            result['fields'] = self.fields or []
        
        return result


class SchoolTemplateBinding(Base):
    """学校-模板绑定表 - v1.2.0 新增
    
    说明：学校与模板的绑定关系，指定学校使用哪个数据库
    核心功能：
    - 一个学校可以有多个数据库连接
    - 一个模板可以被多个学校使用
    - 通过绑定表指定学校用哪个数据库执行查询
    """
    __tablename__ = 'school_template_bindings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    school_id = Column(Integer, ForeignKey('schools.id'), nullable=False, comment='学校ID')
    template_id = Column(Integer, ForeignKey('query_templates.id'), nullable=False, comment='模板ID')
    database_id = Column(Integer, ForeignKey('database_configs.id'), nullable=False, comment='使用的数据库ID')
    enabled = Column(Integer, default=1, comment='是否启用：1启用 0禁用')
    custom_name = Column(String(100), comment='自定义名称(可选)')
    sort_order = Column(Integer, default=0, comment='排序')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联
    school = relationship("School", back_populates="bindings")
    template = relationship("QueryTemplate", back_populates="bindings")
    database = relationship("DatabaseConfig", back_populates="bindings")
    
    def to_dict(self):
        return {
            'id': self.id,
            'school_id': self.school_id,
            'template_id': self.template_id,
            'database_id': self.database_id,
            'enabled': self.enabled,
            'custom_name': self.custom_name,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # 关联信息
            'school_name': self.school.name if self.school else None,
            'template_name': self.template.name if self.template else None,
            'template_category': self.template.category if self.template else None,
            'database_name': self.database.name if self.database else None,
            'database_type': self.database.db_type if self.database else None,
        }


class QueryField(Base):
    """查询条件表"""
    __tablename__ = 'query_fields'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey('query_templates.id'), nullable=False, comment='模板ID')
    field_key = Column(String(50), nullable=False, comment='字段标识')
    field_label = Column(String(100), nullable=False, comment='字段名称')
    field_type = Column(String(20), default='text', comment='字段类型')
    db_column = Column(String(100), comment='数据库列名')
    operator = Column(String(20), default='=', comment='操作符')
    default_value = Column(String(255), comment='默认值')
    options = Column(JSON, comment='选项')
    required = Column(Integer, default=0, comment='是否必填')
    sort_order = Column(Integer, default=0, comment='排序')
    placeholder = Column(String(200), comment='提示文字')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联
    template = relationship("QueryTemplate", back_populates="query_fields")
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'field_key': self.field_key,
            'field_label': self.field_label,
            'field_type': self.field_type,
            'db_column': self.db_column,
            'operator': self.operator,
            'default_value': self.default_value,
            'options': self.options,
            'required': self.required,
            'sort_order': self.sort_order,
            'placeholder': self.placeholder
        }


class QueryTemplateHistory(Base):
    """模板历史表"""
    __tablename__ = 'query_template_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey('query_templates.id'), nullable=False, comment='模板ID')
    version = Column(String(20), nullable=False, comment='版本号')
    name = Column(String(100), comment='查询名称')
    description = Column(Text, comment='描述')
    sql_template = Column(Text, comment='SQL模板')
    fields = Column(JSON, comment='查询字段配置')
    change_log = Column(Text, comment='变更日志')
    changed_by = Column(Integer, comment='修改人ID')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'version': self.version,
            'name': self.name,
            'description': self.description,
            'change_log': self.change_log,
            'changed_by': self.changed_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TemplatePermission(Base):
    """模板权限表"""
    __tablename__ = 'template_permissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    template_id = Column(Integer, ForeignKey('query_templates.id'), nullable=False, comment='模板ID')
    can_query = Column(Integer, default=1, comment='可查询')
    can_export = Column(Integer, default=0, comment='可导出')
    created_at = Column(DateTime, default=datetime.now, comment='授权时间')
    
    # 关联
    user = relationship("User", back_populates="template_permissions")
    template = relationship("QueryTemplate", back_populates="permissions")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'template_id': self.template_id,
            'can_query': self.can_query,
            'can_export': self.can_export,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), unique=True, nullable=False, comment='手机号(登录账号)')
    password = Column(String(255), nullable=False, comment='密码(加密)')
    name = Column(String(100), nullable=False, comment='姓名')
    id_card = Column(String(255), comment='身份证号(加密)')
    openid = Column(String(100), unique=True, nullable=True, comment='微信openid')
    unionid = Column(String(100), unique=True, nullable=True, comment='微信unionid')
    avatar = Column(String(500), nullable=True, comment='头像URL')
    role = Column(String(20), default='user', comment='角色: admin/user')
    status = Column(String(20), default='active', comment='状态')
    last_login = Column(DateTime, comment='最后登录时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联
    school_permissions = relationship("UserSchool", back_populates="user", cascade="all, delete-orphan")
    query_logs = relationship("QueryLog", back_populates="user", cascade="all, delete-orphan")
    operation_logs = relationship("OperationLog", back_populates="user", cascade="all, delete-orphan")
    template_permissions = relationship("TemplatePermission", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'name': self.name,
            'openid': self.openid,
            'avatar': self.avatar,
            'role': self.role,
            'status': self.status,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserSchool(Base):
    """用户学校权限表"""
    __tablename__ = 'user_schools'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    school_id = Column(Integer, ForeignKey('schools.id'), nullable=False, comment='学校ID')
    permissions = Column(JSON, comment='权限列表')
    template_permissions = Column(JSON, comment='模板权限详情')
    created_at = Column(DateTime, default=datetime.now, comment='授权时间')
    
    # 关联
    user = relationship("User", back_populates="school_permissions")
    school = relationship("School", back_populates="user_permissions")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'school_id': self.school_id,
            'school_name': self.school.name if self.school else None,
            'permissions': self.permissions,
            'template_permissions': self.template_permissions,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class QueryLog(Base):
    """查询日志表"""
    __tablename__ = 'query_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    school_id = Column(Integer, ForeignKey('schools.id'), comment='学校ID')
    template_id = Column(Integer, ForeignKey('query_templates.id'), comment='模板ID')
    binding_id = Column(Integer, ForeignKey('school_template_bindings.id'), comment='绑定ID')
    query_name = Column(String(200), comment='查询名称')
    query_params = Column(JSON, comment='查询参数')
    sql_executed = Column(Text, comment='执行的SQL')
    result_count = Column(Integer, default=0, comment='结果条数')
    query_time = Column(Integer, comment='查询耗时(ms)')
    status = Column(String(20), default='success', comment='状态: success/failed')
    error_message = Column(Text, comment='错误信息')
    error_detail = Column(JSON, comment='错误详情')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关联
    user = relationship("User", back_populates="query_logs")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'school_id': self.school_id,
            'template_id': self.template_id,
            'binding_id': self.binding_id,
            'query_name': self.query_name,
            'query_params': self.query_params,
            'result_count': self.result_count,
            'query_time': self.query_time,
            'status': self.status,
            'error_message': self.error_message,
            'error_detail': self.error_detail,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class OperationLog(Base):
    """操作日志表 - 管理员操作审计"""
    __tablename__ = 'operation_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='操作用户ID')
    username = Column(String(50), comment='操作用户名')
    action = Column(String(50), nullable=False, comment='操作类型: create/update/delete/query/export')
    resource_type = Column(String(50), nullable=False, comment='资源类型: school/template/config/user/database')
    resource_id = Column(Integer, comment='资源ID')
    resource_name = Column(String(200), comment='资源名称')
    details = Column(JSON, comment='操作详情')
    ip_address = Column(String(50), comment='IP地址')
    user_agent = Column(String(500), comment='用户代理')
    status = Column(String(20), default='success', comment='状态: success/failed')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关联
    user = relationship("User", back_populates="operation_logs")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'resource_name': self.resource_name,
            'details': self.details,
            'ip_address': self.ip_address,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = 'system_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, comment='配置键')
    config_value = Column(Text, comment='配置值(加密)')
    config_type = Column(String(50), default='text', comment='类型: text/secret/json')
    display_name = Column(String(100), comment='显示名称')
    description = Column(Text, comment='描述')
    category = Column(String(50), default='system', comment='分类: wechat/system/security')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self, hide_secret=True):
        """转换为字典，敏感信息隐藏显示"""
        value = self.config_value
        
        # 解密
        if self.config_type == 'secret' and self.config_value:
            try:
                from core.security import decrypt_password
                value = decrypt_password(self.config_value)
                
                # 隐藏中间部分
                if hide_secret and len(value) > 4:
                    if 'secret' in self.config_key.lower() or 'key' in self.config_key.lower():
                        value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else value[:2] + '*' * (len(value) - 2)
                    elif 'appid' in self.config_key.lower():
                        value = value[:4] + '*' * (len(value) - 4)
            except:
                value = '******'
        
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': value,
            'config_type': self.config_type,
            'display_name': self.display_name,
            'description': self.description,
            'category': self.category,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 数据库初始化函数
def init_database(engine):
    """初始化数据库表"""
    Base.metadata.create_all(engine)


def create_default_admin(session):
    """创建默认超级管理员"""
    from core.security import get_password_hash
    
    # 检查是否已存在
    admin = session.query(User).filter(User.phone == 'admin').first()
    if admin:
        return admin
    
    # 创建超级管理员
    admin = User(
        phone='admin',
        password=get_password_hash('123456'),
        name='超级管理员',
        role='admin',
        status='active'
    )
    session.add(admin)
    session.commit()
    return admin
