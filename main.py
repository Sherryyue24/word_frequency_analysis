from src.core.reader import TextReader
from src.core.analyzer import print_word_frequencies

def main():
    reader = TextReader()
    
    try:
        # 读取TXT文件
        text = reader.read_file('data/samples/story.txt')
        print("\nText preview:")
        print("-" * 50)
        print(text[:100] + "...")  # 打印前100个字符
        print("-" * 50)
        
        # 获取并处理词列表
        words = reader.get_word_list(text)
        
        # 打印基本统计信息
        print(f"\nText Statistics:")
        print(f"Total characters: {len(text)}")
        print(f"Total words {len(words)}")
        
        # 打印词频统计（显示前10个最常见的词）
        print_word_frequencies(words, top_n=10)
        
        # 获取元数据
        metadata = reader.get_metadata()
        if metadata:
            print("\nFile Metadata:")
            for key, value in metadata.items():
                print(f"{key}: {value}")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise e

if __name__ == "__main__":
    main()