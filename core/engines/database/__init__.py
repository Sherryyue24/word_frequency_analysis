# 数据库引擎模块 - 最新架构版本
# 路径: core/engines/database/__init__.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

"""
数据库引擎模块 - 最新架构

核心组件：
- UnifiedDatabase: 统一数据库操作类
- UnifiedDatabaseAdapter: 高级API适配器
- DictionaryManager: 系统字典管理器
- LinguisticAnalyzer: 语言学分析器（如果可用）

特性：
- 多词性字典支持
- 精确的dictionary_id关联
- 个人学习状态管理
- 完整的语言学分析
"""

from .unified_database import UnifiedDatabase
from .database_adapter import UnifiedDatabaseAdapter, unified_adapter
from .dictionary_manager import DictionaryManager

# 尝试导入语言学分析器
try:
    from .linguistic_analyzer import LinguisticAnalyzer
    __all__ = [
        'UnifiedDatabase',
        'UnifiedDatabaseAdapter', 
        'unified_adapter',
        'DictionaryManager',
        'LinguisticAnalyzer'
    ]
except ImportError:
    __all__ = [
        'UnifiedDatabase',
        'UnifiedDatabaseAdapter',
        'unified_adapter', 
        'DictionaryManager'
    ]

# 版本信息
__version__ = '2.0.0'
__architecture__ = 'unified_multipos_dictionary' 