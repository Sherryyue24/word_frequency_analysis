# 核心引擎模块 - 最新架构版本
# 路径: core/engines/__init__.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

"""
核心引擎模块 - 最新架构

分层设计：
- database: 数据库层（统一数据库、字典管理、语言学分析）
- input: 输入处理层（文件处理、词汇表导入）
- vocabulary: 词汇处理层（词汇分析、学习状态管理）

核心特性：
- 多词性字典系统
- 精确的dictionary_id关联
- 个人学习状态追踪
- 完整的语言学分析
- 统一的数据架构
"""

# 导入核心组件
from .database import UnifiedDatabase, UnifiedDatabaseAdapter, unified_adapter, DictionaryManager
from .input import FileProcessor, TextReader, import_wordlist_from_file, PersonalWordlistImporter  
from .vocabulary import WordAnalyzer, PersonalStatusManager

# 向后兼容的导出
from .input.file_processor import *
from .vocabulary.word_analyzer import analyze_text
from .database.database_adapter import unified_adapter

__all__ = [
    # 数据库层
    'UnifiedDatabase',
    'UnifiedDatabaseAdapter', 
    'unified_adapter',
    'DictionaryManager',
    
    # 输入处理层
    'FileProcessor',
    'TextReader',
    'import_wordlist_from_file',
    'PersonalWordlistImporter',
    
    # 词汇处理层
    'WordAnalyzer',
    'PersonalStatusManager',
    
    # 向后兼容
    'analyze_text'
]

# 架构信息
__version__ = '2.0.0'
__architecture__ = 'unified_multipos_dictionary'
__features__ = [
    'multipos_dictionary',
    'dictionary_id_mapping', 
    'personal_status_tracking',
    'linguistic_analysis',
    'vocabulary_coverage',
    'difficulty_analysis'
]
