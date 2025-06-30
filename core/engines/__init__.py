# Engines模块初始化
# 路径: core/engines/__init__.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

"""
Engines 模块 - 核心处理引擎

重新组织为三个功能模块：
- input: 输入处理模块（文件处理、词汇表导入）
- vocabulary: 词汇处理模块（词汇分析、处理）
- database: 数据库模块（数据存储、检索）
"""

# 导入三大功能模块
from . import input
from . import vocabulary 
from . import database

# 为了向后兼容，直接导出常用组件
from .input.file_processor import TextProcessor, FileProcessor
from .input.file_reader import TextReader
from .input.modern_wordlist_import import (
    import_wordlist_from_file,
    import_multiple_wordlists
)

from .vocabulary.word_analyzer import analyze_text

from .database.unified_database import UnifiedDatabase
from .database.database_adapter import UnifiedDatabaseAdapter, unified_adapter

# 向后兼容的别名（使用统一适配器）
StorageManager = lambda: unified_adapter
VocabularyDatabase = lambda: unified_adapter

# 模块版本和信息
__version__ = "1.0.0"
__author__ = "Sherryyue"

# 公开的API接口
__all__ = [
    # 功能模块
    'input',
    'vocabulary', 
    'database',
    
    # 新统一架构
    'UnifiedDatabase',
    'unified_adapter', 
    'UnifiedDatabaseAdapter',
    
    # 核心处理器
    'TextProcessor',
    'FileProcessor', 
    'TextReader',
    'analyze_text',
    
    # 词汇表导入
    'import_wordlist_from_file',
    'import_multiple_wordlists',
    
    # 向后兼容别名
    'StorageManager',
    'VocabularyDatabase',
]
