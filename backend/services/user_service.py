# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 用户服务

Author: 飞书百万（AI助手）
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.database import User, UserSchool, School, QueryTemplate, QueryLog
from core.security import verify_password, get_password_hash, create_access_token, TokenData
from core.config import settings
import secrets


class UserService:
    """用户服务"""
    
    @staticmethod
    def authenticate(db: Session, phone: str, password: str) -> Optional[dict]:
        """
        用户登录认证
        
        Args:
            db: 数据库会话
            phone: 手机号
            password: 密码
            
        Returns:
            用户信息和token，认证失败返回None
        """
        # 查找用户
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            return None
        
        # 检查状态
        if user.status != 'active':
            return None
        
        # 验证密码
        if not verify_password(password, user.password):
            return None
        
        # 更新最后登录时间
        user.last_login = datetime.now()
        db.commit()
        
        # 生成token
        access_token = create_access_token({
            "sub": str(user.id),
            "phone": user.phone,
            "role": user.role,
            "name": user.name
        })
        
        return {
            "user": user.to_dict(),
            "token": access_token,
            "role": user.role
        }
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_phone(db: Session, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        return db.query(User).filter(User.phone == phone).first()
    
    @staticmethod
    def get_by_openid(db: Session, openid: str) -> Optional[User]:
        """根据微信openid获取用户"""
        return db.query(User).filter(User.openid == openid).first()
    
    @staticmethod
    def create_user(db: Session, phone: str, password: str, name: str, 
                   id_card: str = None, role: str = 'user') -> User:
        """创建用户"""
        user = User(
            phone=phone,
            password=get_password_hash(password),
            name=name,
            id_card=get_password_hash(id_card) if id_card else None,
            role=role,
            status='active'
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
        """更新用户"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                if key == 'password':
                    setattr(user, key, get_password_hash(value))
                elif key == 'id_card':
                    setattr(user, key, get_password_hash(value))
                else:
                    setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """删除用户"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True
    
    @staticmethod
    def get_user_schools(db: Session, user_id: int) -> List[dict]:
        """获取用户授权的学校列表"""
        perms = db.query(UserSchool).filter(UserSchool.user_id == user_id).all()
        result = []
        for perm in perms:
            if perm.school:
                result.append({
                    'id': perm.school.id,
                    'name': perm.school.name,
                    'code': perm.school.code,
                    'permissions': perm.permissions
                })
        return result
    
    @staticmethod
    def grant_school(db: Session, user_id: int, school_id: int, 
                    permissions: List[str] = None) -> UserSchool:
        """授予用户学校权限"""
        # 检查是否已存在
        existing = db.query(UserSchool).filter(
            and_(UserSchool.user_id == user_id, UserSchool.school_id == school_id)
        ).first()
        
        if existing:
            existing.permissions = permissions or ['query']
            db.commit()
            return existing
        
        perm = UserSchool(
            user_id=user_id,
            school_id=school_id,
            permissions=permissions or ['query']
        )
        db.add(perm)
        db.commit()
        db.refresh(perm)
        return perm
    
    @staticmethod
    def revoke_school(db: Session, user_id: int, school_id: int) -> bool:
        """撤销用户学校权限"""
        perm = db.query(UserSchool).filter(
            and_(UserSchool.user_id == user_id, UserSchool.school_id == school_id)
        ).first()
        
        if not perm:
            return False
        
        db.delete(perm)
        db.commit()
        return True
    
    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表"""
        return db.query(User).offset(skip).limit(limit).all()


class SchoolService:
    """学校服务"""
    
    @staticmethod
    def create(db: Session, name: str, code: str, description: str = None) -> School:
        """创建学校"""
        school = School(
            name=name,
            code=code,
            description=description,
            status='active'
        )
        db.add(school)
        db.commit()
        db.refresh(school)
        return school
    
    @staticmethod
    def get_by_id(db: Session, school_id: int) -> Optional[School]:
        """根据ID获取学校"""
        return db.query(School).filter(School.id == school_id).first()
    
    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[School]:
        """根据编码获取学校"""
        return db.query(School).filter(School.code == code).first()
    
    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[School]:
        """获取学校列表"""
        return db.query(School).offset(skip).limit(limit).all()
    
    @staticmethod
    def update(db: Session, school_id: int, **kwargs) -> Optional[School]:
        """更新学校"""
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            return None
        
        for key, value in kwargs.items():
            if hasattr(school, key) and value is not None:
                setattr(school, key, value)
        
        db.commit()
        db.refresh(school)
        return school
    
    @staticmethod
    def delete(db: Session, school_id: int) -> bool:
        """删除学校"""
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            return False
        db.delete(school)
        db.commit()
        return True


class QueryTemplateService:
    """查询模板服务"""
    
    @staticmethod
    def get_by_school(db: Session, school_id: int) -> List[QueryTemplate]:
        """获取学校的所有查询模板"""
        return db.query(QueryTemplate).filter(
            QueryTemplate.school_id == school_id,
            QueryTemplate.status == 'active'
        ).all()
    
    @staticmethod
    def get_by_category(db: Session, school_id: int, category: str) -> List[QueryTemplate]:
        """获取学校指定业务大类的查询模板（支持 category 或 category_id）"""
        # 先尝试按 category_id 查询
        try:
            category_id = int(category)
            templates = db.query(QueryTemplate).filter(
                QueryTemplate.school_id == school_id,
                QueryTemplate.category_id == category_id,
                QueryTemplate.status == 'active'
            ).all()
            if templates:
                return templates
        except (ValueError, TypeError):
            pass
        
        # 兼容：按 category 编码查询
        return db.query(QueryTemplate).filter(
            QueryTemplate.school_id == school_id,
            QueryTemplate.category == category,
            QueryTemplate.status == 'active'
        ).all()
    
    @staticmethod
    def get_categories(db: Session, school_id: int) -> List[dict]:
        """获取学校的业务大类列表（优先从 template_categories 表获取）"""
        # 优先从业务大类表获取
        from models.database import TemplateCategory
        
        categories_db = db.query(TemplateCategory).filter(
            TemplateCategory.school_id == school_id,
            TemplateCategory.status == 'active'
        ).order_by(TemplateCategory.sort_order).all()
        
        if categories_db:
            # 从独立表获取成功，统计每个分类下的模板数量
            result = []
            for cat in categories_db:
                count = db.query(QueryTemplate).filter(
                    QueryTemplate.school_id == school_id,
                    QueryTemplate.category_id == cat.id,
                    QueryTemplate.status == 'active'
                ).count()
                result.append({
                    'id': cat.code,
                    'category_id': cat.id,
                    'name': cat.name,
                    'icon': cat.icon or '📋',
                    'count': count
                })
            return result
        
        # 兼容旧逻辑：从模板表提取
        templates = db.query(QueryTemplate).filter(
            QueryTemplate.school_id == school_id,
            QueryTemplate.status == 'active'
        ).all()
        
        # 按业务大类分组
        categories = {}
        for t in templates:
            if t.category not in categories:
                categories[t.category] = {
                    'id': t.category,
                    'category_id': t.category_id,
                    'name': t.category_name or t.category,
                    'icon': t.category_icon or '📋',
                    'count': 0
                }
            categories[t.category]['count'] += 1
        
        return list(categories.values())


class QueryLogService:
    """查询日志服务"""
    
    @staticmethod
    def create_log(db: Session, user_id: int, school_id: int, template_id: int,
                  query_name: str, query_params: dict, sql: str,
                  result_count: int, query_time: int, status: str = 'success',
                  error_message: str = None, error_detail: dict = None) -> QueryLog:
        """创建查询日志
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            school_id: 学校ID
            template_id: 模板ID
            query_name: 查询名称
            query_params: 查询参数
            sql: 执行的SQL
            result_count: 结果条数
            query_time: 查询耗时(ms)
            status: 状态 success/failed
            error_message: 错误信息摘要
            error_detail: 错误详情 dict (包含 error_type, error_message, sql, suggestion)
        """
        log = QueryLog(
            user_id=user_id,
            school_id=school_id,
            template_id=template_id,
            query_name=query_name,
            query_params=query_params,
            sql_executed=sql,
            result_count=result_count,
            query_time=query_time,
            status=status,
            error_message=error_message,
            error_detail=error_detail
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def get_user_history(db: Session, user_id: int, skip: int = 0, 
                        limit: int = 30) -> List[QueryLog]:
        """获取用户查询历史"""
        return db.query(QueryLog).filter(
            QueryLog.user_id == user_id
        ).order_by(QueryLog.created_at.desc()).offset(skip).limit(limit).all()
