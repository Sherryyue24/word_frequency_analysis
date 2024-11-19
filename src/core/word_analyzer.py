from collections import Counter
from pathlib import Path
from typing import Dict, Tuple
from .file_reader import TextReader

def analyze_text(text: str, reader: TextReader) -> Tuple[Dict, Dict]:
    """分析文本内容"""
    try:
        # 预处理文本
        processed_text = reader.preprocess_text(text)
        
        # 获取词列表并计算词频
        words = reader.get_word_list(processed_text)
        word_frequencies = dict(Counter(words))
        
        # 获取元数据
        metadata = reader.get_metadata()
        
        basic_info = {
            'total_words': len(words),
            'unique_words': len(word_frequencies),
            'metadata': metadata
        }
        
        return basic_info, word_frequencies
        
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")
        raise e
