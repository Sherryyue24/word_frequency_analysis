# 基础数据模型
# 路径: core/models/base.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime


class BaseModel(ABC):
    """
    所有数据模型的基类
    提供通用的功能和接口定义
    """
    
    def __init__(self):
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """将模型转换为字典格式"""
        return {
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()


class TextModel(BaseModel):
    """文本数据模型"""
    
    def __init__(self, content: str, filename: str = None):
        super().__init__()
        self.content = content
        self.filename = filename
        self.word_count = 0
        self.unique_words = 0
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            'filename': self.filename,
            'word_count': self.word_count,
            'unique_words': self.unique_words,
            'metadata': self.metadata
        })
        return base_dict


class WordModel(BaseModel):
    """单词数据模型"""
    
    def __init__(self, word: str, frequency: int = 0):
        super().__init__()
        self.word = word
        self.frequency = frequency
        self.lemma = None
        self.pos_tags = []
        self.derivatives = []
        self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            'word': self.word,
            'frequency': self.frequency,
            'lemma': self.lemma,
            'pos_tags': self.pos_tags,
            'derivatives': self.derivatives,
            'tags': self.tags
        })
        return base_dict


class AnalysisResult(BaseModel):
    """分析结果模型"""
    
    def __init__(self, text_id: str):
        super().__init__()
        self.text_id = text_id
        self.word_frequencies = {}
        self.basic_info = {}
        self.processing_time = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            'text_id': self.text_id,
            'word_frequencies': self.word_frequencies,
            'basic_info': self.basic_info,
            'processing_time': self.processing_time
        })
        return base_dict 