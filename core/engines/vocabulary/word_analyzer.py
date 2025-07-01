# 词汇分析器 - 最新架构版本
# 路径: core/engines/vocabulary/word_analyzer.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

import re
import json
from typing import Dict, List, Set, Tuple
from collections import Counter
import sqlite3

class WordAnalyzer:
    """词汇分析器 - 最新架构版本
    
    负责：
    - 文本词汇提取和分析
    - 词频统计
    - 语言学特征分析
    - 字典匹配和关联
    """
    
    def __init__(self, db_path: str = "data/databases/unified.db"):
        self.db_path = db_path
    
    def analyze_text(self, text: str) -> Dict:
        """分析文本中的词汇"""
        # 基本文本统计
        words = self.extract_words(text)
        word_frequencies = Counter(words)
        
        # 基本统计信息
        basic_info = {
            'total_words': len(words),
            'unique_words': len(word_frequencies),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'longest_word': max(words, key=len) if words else '',
            'most_common_word': word_frequencies.most_common(1)[0] if word_frequencies else ('', 0)
        }
        
        return {
            'basic_info': basic_info,
            'word_frequencies': dict(word_frequencies),
            'vocabulary': list(word_frequencies.keys())
        }
    
    def extract_words(self, text: str) -> List[str]:
        """从文本中提取词汇"""
        # 简单的词汇提取：只保留字母，转为小写
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # 过滤过短的词汇
        words = [word for word in words if len(word) >= 2]
        
        return words
    
    def calculate_word_frequencies(self, words: List[str]) -> Dict[str, int]:
        """计算词频"""
        return dict(Counter(words))
    
    def extract_vocabulary(self, text: str) -> Set[str]:
        """提取词汇表"""
        words = self.extract_words(text)
        return set(words)
    
    def add_or_get_word(self, surface_form: str, lemma: str = None) -> str:
        """添加或获取词汇记录"""
        from ..database.unified_database import UnifiedDatabase
        
        db = UnifiedDatabase(self.db_path)
        return db.add_or_get_word(surface_form, lemma)
    
    def get_word_analysis(self, word: str) -> Dict:
        """获取词汇的详细分析"""
        from ..database.unified_database import UnifiedDatabase
        
        db = UnifiedDatabase(self.db_path)
        
        # 获取词汇变形
        variants = db.get_word_variants_with_frequencies(word)
        
        # 获取语言学特征
        features = db.get_word_linguistic_features(word)
        
        return {
            'word': word,
            'variants': variants,
            'linguistic_features': features
        }

# 兼容函数
def analyze_text(text: str) -> Dict:
    """分析文本中的词汇（兼容函数）"""
    analyzer = WordAnalyzer()
    return analyzer.analyze_text(text)

def analyze_text_words(text: str) -> List[str]:
    """提取文本中的词汇（兼容函数）"""
    analyzer = WordAnalyzer()
    return analyzer.extract_words(text)

def calculate_word_frequencies(words: List[str]) -> Dict[str, int]:
    """计算词频（兼容函数）"""
    analyzer = WordAnalyzer()
    return analyzer.calculate_word_frequencies(words)

def extract_vocabulary(text: str) -> Set[str]:
    """提取词汇表（兼容函数）"""
    analyzer = WordAnalyzer()
    return analyzer.extract_vocabulary(text)
