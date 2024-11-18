from collections import Counter
from pathlib import Path
from typing import Dict, Tuple
from .reader import TextReader

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

'''
def print_word_frequencies(words, top_n=None):
    """
    打印词频统计
    
    Args:
        words: 词列表
        top_n: 显示前n个高频词，None表示显示所有
    """
    # 使用Counter统计词频
    word_freq = Counter(words)
    
    # 按频率降序排序
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    # 确定要显示的数量
    if top_n:
        sorted_words = sorted_words[:top_n]
    
    # 打印统计结果
    print("\nWord frequency statistics:")
    print("-" * 30)
    print("Word\t\tfrequency")
    print("-" * 30)
    for word, freq in sorted_words:
        # 对齐输出
        print(f"{word:<15}{freq:>5}")
    print("-" * 30)
    print(f"Total: {len(word_freq)} different words")


'''