# 词汇处理模块 - 最新架构版本
# 路径: core/engines/vocabulary/__init__.py
# 项目名称: Word Frequency Analysis  
# 作者: Sherryyue

"""
词汇处理模块 - 最新架构

核心组件：
- WordAnalyzer: 词汇分析器
- PersonalStatusManager: 个人学习状态管理器

特性：
- 精确的字典关联（dictionary_id）
- 个人学习状态跟踪（new/learn/know/master）
- 词汇难度评估
- 学习进度分析
"""

from .word_analyzer import WordAnalyzer
from .personal_status_manager import PersonalStatusManager

__all__ = [
    'WordAnalyzer',
    'PersonalStatusManager'
]

# 版本信息
__version__ = '2.0.0'
__features__ = ['dictionary_id_mapping', 'personal_status_tracking', 'difficulty_analysis'] 