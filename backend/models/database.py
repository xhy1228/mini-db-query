# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 数据库模型

Author: 飞书百万（AI助手）
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
    
    # 关联
    databases = relationship("DatabaseConfig", back_populates="school", cascade="all, delete-orphan")
    templates = relationship("QueryTemplate", back_populates="school", cascade="all, delete-orphan")
    user_permissions = relationship("UserSchool", back_populates="school", cascade="all, delete-orphan")
    
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
    """数据库配置表"""
    __tablename__ = 'database_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    school_id = Column(Integer, ForeignKey('schools.id'), nullable=False, comment='学校ID')
    name = Column(String(100), nullable=False, comment='配置名称')
    db_type = Column(String(50), nullable=False, comment='数据库类型')
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
    
    # 关联
    school = relationship("School", back_populates="databases")
    
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
            'description': self.description,
            'status': self.status
        }
        if include_password:
            result['password'] = self.password
        return result


class QueryTemplate(Base):
    """查询模板表"""
    __tablename__ = 'query_templates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    school_id = Column(Integer, ForeignKey('schools.id'), nullable=False, comment='学校ID')
    category = Column(String(50), nullable=False, comment='业务大类')
    category_name = Column(String(100), comment='业务大类名称')
    category_icon = Column(String(20), comment='业务大类图标')
    name = Column(String(100), nullable=False, comment='查询名称')
    description = Column(Text, comment='描述')
    sql_template = Column(Text, nullable=False, comment='SQL模板')
    fields = Column(JSON, comment='查询字段配置')
    time_field = Column(String(100), comment='时间字段')
    default_limit = Column(Integer, default=500, comment='默认条数限制')
    status = Column(String(20), default='active', comment='状态')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联
    school = relationship("School", back_populates="templates")
    
    def to_dict(self):
        return {
            'id': self.id,
            'school_id': self.school_id,
            'category': self.category,
            'category_name': self.category_name,
            'category_icon': self.category_icon,
            'name': self.name,
            'description': self.description,
            'fields': self.fields,
            'time_field': self.time_field,
            'default_limit': self.default_limit,
            'status': self.status
        }


class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), unique=True, nullable=False, comment='手机号(登录账号)')
    password = Column(String(255), nullable=False, comment='密码(加密)')
    name = Column(String(100), nullable=False, comment='姓名')
    id_card = Column(String(255), comment='身份证号(加密)')
    role = Column(String(20), default='user', comment='角色: admin/user')
    status = Column(String(20), default='active', comment='状态')
    last_login = Column(DateTime, comment='最后登录时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联
    school_permissions = relationship("UserSchool", back_populates="user", cascade="all, delete-orphan")
    query_logs = relationship("QueryLog", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'name': self.name,
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
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class QueryLog(Base):
    """查询日志表"""
    __tablename__ = 'query_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    school_id = Column(Integer, ForeignKey('schools.id'), comment='学校ID')
    template_id = Column(Integer, ForeignKey('query_templates.id'), comment='模板ID')
    query_name = Column(String(200), comment='查询名称')
    query_params = Column(JSON, comment='查询参数')
    sql_executed = Column(Text, comment='执行的SQL')
    result_count = Column(Integer, default=0, comment='结果条数')
    query_time = Column(Integer, comment='查询耗时(ms)')
    status = Column(String(20), default='success', comment='状态: success/failed')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关联
    user = relationship("User", back_populates="query_logs")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'school_id': self.school_id,
            'template_id': self.template_id,
            'query_name': self.query_name,
            'query_params': self.query_params,
            'result_count': self.result_count,
            'query_time': self.query_time,
            'status': self.status,
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
                        # 显示前4位和后4位
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
