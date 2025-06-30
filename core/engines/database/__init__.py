# 数据库模块
# 路径: core/engines/database/__init__.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

"""
数据库模块 - 负责数据存储和检索

该模块包含：
- 统一数据库：现代化数据库架构实现
- 数据库适配器：兼容性接口和数据访问
"""

from .unified_database import UnifiedDatabase
from .database_adapter import UnifiedDatabaseAdapter, unified_adapter

__all__ = [
    # 核心数据库
    'UnifiedDatabase',
    
    # 适配器和实例
    'UnifiedDatabaseAdapter',
    'unified_adapter'
] 