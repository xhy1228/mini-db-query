# -*- coding: utf-8 -*-

"""
多源数据查询助手 —— 智能查询模板管理模块

Author: 飞书百万（AI助手）
功能：管理查询模板，根据用户选择生成SQL语句
"""

import os
import sys
import json
import shutil
from typing import Dict, List, Optional, Any
from datetime import datetime


def get_app_dir():
    """获取应用程序所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_resource_dir():
    """获取打包资源目录（PyInstaller内部）"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ensure_config_exists():
    """确保配置文件存在，如果不存在则从打包资源复制"""
    app_dir = get_app_dir()
    resource_dir = get_resource_dir()
    
    config_dir = os.path.join(app_dir, "config")
    template_file = os.path.join(config_dir, "query_templates.json")
    
    # 如果配置文件已存在，直接返回
    if os.path.exists(template_file):
        return template_file
    
    # 创建配置目录
    os.makedirs(config_dir, exist_ok=True)
    
    # 尝试从打包资源复制
    resource_template = os.path.join(resource_dir, "config", "query_templates.json")
    if os.path.exists(resource_template):
        shutil.copy(resource_template, template_file)
        print(f"[信息] 已创建默认配置文件: {template_file}")
    else:
        # 创建空的默认配置
        default_config = {
            "version": "1.0",
            "categories": {},
            "default_category": "",
            "default_query": ""
        }
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print(f"[信息] 已创建空配置文件: {template_file}")
    
    return template_file


class QueryTemplateManager:
    """查询模板管理器"""
    
    def __init__(self):
        self.app_dir = get_app_dir()
        self.template_file = os.path.join(self.app_dir, "config", "query_templates.json")
        
        # 确保配置文件存在
        ensure_config_exists()
        
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """加载查询模板"""
        try:
            if os.path.exists(self.template_file):
                with open(self.template_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[错误] 加载查询模板失败: {e}")
        return self._get_default_templates()
    
    def _get_default_templates(self) -> Dict:
        """获取默认模板"""
        return {
            "categories": {},
            "default_category": "",
            "default_query": ""
        }
    
    def save_templates(self):
        """保存查询模板"""
        try:
            os.makedirs(os.path.dirname(self.template_file), exist_ok=True)
            with open(self.template_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[错误] 保存查询模板失败: {e}")
            return False
    
    def get_categories(self) -> List[Dict]:
        """获取所有业务大类"""
        categories = []
        for cat_id, cat_data in self.templates.get("categories", {}).items():
            categories.append({
                "id": cat_id,
                "name": cat_data.get("name", cat_id),
                "description": cat_data.get("description", ""),
                "icon": cat_data.get("icon", "📁")
            })
        return categories
    
    def get_category(self, category_id: str) -> Optional[Dict]:
        """获取业务大类详情"""
        cat_data = self.templates.get("categories", {}).get(category_id)
        if cat_data:
            return {
                "id": category_id,
                "name": cat_data.get("name", category_id),
                "description": cat_data.get("description", ""),
                "icon": cat_data.get("icon", "📁"),
                "queries": list(cat_data.get("queries", {}).keys())
            }
        return None
    
    def get_queries(self, category_id: str) -> List[Dict]:
        """获取业务大类下的所有查询"""
        queries = []
        cat_data = self.templates.get("categories", {}).get(category_id, {})
        for query_id, query_data in cat_data.get("queries", {}).items():
            queries.append({
                "id": query_id,
                "name": query_data.get("name", query_id),
                "description": query_data.get("description", ""),
                "table": query_data.get("table", ""),
                "fields": query_data.get("fields", []),
                "time_field": query_data.get("time_field", ""),
                "default_field": query_data.get("default_field", ""),
                "default_limit": query_data.get("default_limit", 1000)
            })
        return queries
    
    def get_query_template(self, category_id: str, query_id: str) -> Optional[Dict]:
        """获取具体查询模板"""
        cat_data = self.templates.get("categories", {}).get(category_id, {})
        query_data = cat_data.get("queries", {}).get(query_id)
        if query_data:
            return {
                "id": query_id,
                "category_id": category_id,
                "name": query_data.get("name", query_id),
                "description": query_data.get("description", ""),
                "table": query_data.get("table", ""),
                "fields": query_data.get("fields", []),
                "time_field": query_data.get("time_field", ""),
                "default_field": query_data.get("default_field", ""),
                "default_limit": query_data.get("default_limit", 1000),
                "result_columns": query_data.get("result_columns", ["*"]),
                "key_columns": query_data.get("key_columns", []),
                "custom_sql_template": query_data.get("custom_sql_template", ""),
                "time_format": query_data.get("time_format", "mysql")  # 支持Oracle时间格式
            }
        return None
    
    def get_field_link_info(self, category_id: str, query_id: str, field_id: str) -> Optional[str]:
        """获取字段的链接信息（用于二次查询）"""
        template = self.get_query_template(category_id, query_id)
        if not template:
            return None
        
        for f in template["fields"]:
            if f["id"] == field_id:
                return f.get("link_to")
        return None
    
    def get_target_query_info(self, link_path: str) -> Optional[Dict]:
        """
        根据链接路径获取目标查询信息
        
        Args:
            link_path: 格式 "category.query.field"
        
        Returns:
            目标查询信息
        """
        parts = link_path.split(".")
        if len(parts) != 3:
            return None
        
        cat_id, query_id, field_id = parts
        template = self.get_query_template(cat_id, query_id)
        if not template:
            return None
        
        field_label = None
        for f in template["fields"]:
            if f["id"] == field_id:
                field_label = f["label"]
                break
        
        return {
            "category_id": cat_id,
            "category_name": self.get_category(cat_id)["name"] if self.get_category(cat_id) else "",
            "query_id": query_id,
            "query_name": template["name"],
            "field_id": field_id,
            "field_label": field_label
        }
    
    def generate_sql(self, category_id: str, query_id: str, 
                     field_id: str, field_value: str,
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None) -> Optional[str]:
        """
        生成SQL语句
        
        Args:
            category_id: 业务大类ID
            query_id: 查询ID
            field_id: 查询字段ID
            field_value: 查询值
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
        
        Returns:
            生成的SQL语句
        """
        template = self.get_query_template(category_id, query_id)
        if not template:
            return None
        
        # 查找字段配置
        field_config = None
        for f in template["fields"]:
            if f["id"] == field_id:
                field_config = f
                break
        
        if not field_config:
            return None
        
        # 转义单引号防止SQL注入
        safe_value = str(field_value).replace("'", "''")
        column = field_config["column"]
        
        # 检查是否有自定义SQL模板（支持多表JOIN查询）
        custom_sql = template.get("custom_sql_template", "")
        if custom_sql:
            # 替换占位符
            sql = custom_sql.replace("{column}", column)
            sql = sql.replace("{value}", safe_value)
            
            # 处理时间范围
            time_field = template.get("time_field", "")
            time_format = template.get("time_format", "mysql")  # 默认mysql格式
            
            if time_field and (start_time or end_time):
                time_conditions = []
                if time_format == "oracle":
                    # Oracle 时间格式
                    if start_time:
                        time_conditions.append(f"cc.OPDT >= TO_DATE('{start_time.strftime('%Y-%m-%d %H:%M:%S')}', 'YYYY-MM-DD HH24:MI:SS')")
                    if end_time:
                        time_conditions.append(f"cc.OPDT <= TO_DATE('{end_time.strftime('%Y-%m-%d %H:%M:%S')}', 'YYYY-MM-DD HH24:MI:SS')")
                else:
                    # MySQL 时间格式
                    if start_time:
                        time_conditions.append(f"{time_field} >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'")
                    if end_time:
                        time_conditions.append(f"{time_field} <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'")
                
                if "{time_conditions}" in sql:
                    sql = sql.replace("{time_conditions}", " AND " + " AND ".join(time_conditions))
                else:
                    # 如果没有占位符，直接追加条件
                    sql = sql + " AND " + " AND ".join(time_conditions)
            else:
                # 没有时间条件，清空占位符
                sql = sql.replace("{time_conditions}", "")
            
            return sql
        
        # 默认单表查询模式
        conditions = []
        conditions.append(f"{column} = '{safe_value}'")
        
        # 时间范围条件
        time_field = template.get("time_field", "")
        if time_field and (start_time or end_time):
            if start_time:
                conditions.append(f"{time_field} >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'")
            if end_time:
                conditions.append(f"{time_field} <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'")
        
        # 构建SQL
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        limit = template.get("default_limit", 1000)
        
        sql = f"SELECT * FROM {template['table']} WHERE {where_clause} ORDER BY {time_field or '1'} DESC LIMIT {limit}"
        
        return sql
    
    def add_query_template(self, category_id: str, query_id: str, 
                           name: str, description: str, table: str,
                           fields: List[Dict], time_field: str = "",
                           default_limit: int = 1000) -> bool:
        """
        添加查询模板
        
        Args:
            category_id: 业务大类ID
            query_id: 查询ID
            name: 查询名称
            description: 查询描述
            table: 表名
            fields: 查询字段列表
            time_field: 时间字段名
            default_limit: 默认返回条数
        
        Returns:
            是否添加成功
        """
        if category_id not in self.templates.get("categories", {}):
            return False
        
        if "queries" not in self.templates["categories"][category_id]:
            self.templates["categories"][category_id]["queries"] = {}
        
        self.templates["categories"][category_id]["queries"][query_id] = {
            "name": name,
            "description": description,
            "table": table,
            "fields": fields,
            "time_field": time_field,
            "default_limit": default_limit,
            "result_columns": ["*"]
        }
        
        return self.save_templates()
    
    def add_category(self, category_id: str, name: str, 
                     description: str = "", icon: str = "📁") -> bool:
        """
        添加业务大类
        
        Args:
            category_id: 业务大类ID
            name: 业务大类名称
            description: 业务大类描述
            icon: 图标
        
        Returns:
            是否添加成功
        """
        if category_id in self.templates.get("categories", {}):
            return False
        
        if "categories" not in self.templates:
            self.templates["categories"] = {}
        
        self.templates["categories"][category_id] = {
            "name": name,
            "description": description,
            "icon": icon,
            "queries": {}
        }
        
        return self.save_templates()


# 全局实例
_template_manager: Optional[QueryTemplateManager] = None


def get_template_manager() -> QueryTemplateManager:
    """获取模板管理器实例"""
    global _template_manager
    if _template_manager is None:
        _template_manager = QueryTemplateManager()
    return _template_manager
