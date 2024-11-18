from pathlib import Path
from src.core.analyzer import analyze_text
from src.core.reader import TextReader
from src.core.data import StorageManager
from src.core.processor import TextProcessor
from datetime import datetime
from src.utils.helpers import print_analysis_results,get_supported_files
import os

'''
def analyze_and_store_text(file_path: str):
    # 创建所需的实例
    reader = TextReader()
    storage_manager = StorageManager()
    
    try:
        # 读取文件内容
        text = reader.read_file(file_path)
        
        # 计算文本哈希值
        content_hash = storage_manager.calculate_text_hash(text)
        
        # 检查是否存在缓存的分析结果
        cached_result = storage_manager.get_existing_analysis(content_hash)
        if cached_result:
            print("找到缓存的分析结果")
            return cached_result, content_hash
            
        # 如果没有缓存，进行新的分析
        print("没有缓存，进行分析")
        basic_info, word_frequencies = analyze_text(text, reader)
        
        # 补充基本信息
        basic_info['filename'] = Path(file_path).name
        basic_info['analysis_date'] = datetime.now().isoformat()
        
        # 存储分析结果到数据库
        storage_manager.store_analysis(
            content_hash=content_hash,
            filename=basic_info['filename'],
            basic_info=basic_info,
            word_frequencies=word_frequencies
        )
        
        print("分析完成并保存到数据库")
        return (basic_info, word_frequencies), content_hash
        
    except Exception as e:
        print(f"分析失败: {str(e)}")
        raise
'''


from src.core.processor import TextProcessor
from src.core.data import StorageManager
import os

def main():
    processor = TextProcessor()
    storage_manager = StorageManager()
    
    # 指定要分析的文件夹路径
    directory_path = "/Users/yue/Documents/code/word-frequency-analysis/data/samples/new"
    
    try:
        # 获取所有支持的文件
        file_paths = get_supported_files(directory_path)
        
        if not file_paths:
            print(f"在目录 {directory_path} 及其子目录中没有找到支持的文件类型")
            return
        
        # 处理所有文件
        print("\n开始处理所有文件...")
        processor.process_new_texts(directory_path)

        '''
        for i, file_path in enumerate(file_paths, 1):
            rel_path = os.path.relpath(file_path, directory_path)
            print(f"\n[{i}/{len(file_paths)}] 处理文件: {rel_path}")
            try:
                # 分析并存储结果
                processor.process_file(file_path)
            except Exception as e:
                print(f"处理文件失败: {str(e)}")
                continue
        '''
        # 所有文件处理完成后，更新词频统计
        #storage_manager.update_word_stats()
        
        # 打印统计信息
        top_words = storage_manager.get_word_stats(min_frequency=100)
        if top_words:
            print("\n高频词统计:")
            for word, total_freq, doc_count, _ in top_words:
                print(f"词语: {word}, 总频率: {total_freq}, 出现文档数: {doc_count}")
            
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()