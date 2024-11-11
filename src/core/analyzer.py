
from collections import Counter

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