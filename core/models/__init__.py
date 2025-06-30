# 数据模型包
# 路径: core/models/__init__.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

"""
数据模型包

包含所有核心数据模型的定义:
- BaseModel: 基础模型类
- TextModel: 文本数据模型
- WordModel: 单词数据模型
- AnalysisResult: 分析结果模型
"""

from .base import BaseModel, TextModel, WordModel, AnalysisResult

__all__ = [
    'BaseModel',
    'TextModel', 
    'WordModel',
    'AnalysisResult'
]
