from pathlib import Path
from src.core.vocabulary_database import VocabularyDatabase
from src.core.word_analyzer import analyze_text
from src.core.file_reader import TextReader
from src.core.analysis_database import StorageManager
from src.core.file_processor import TextProcessor
from datetime import datetime
from src.core.word_sets.awlpdf_import import  import_awl_to_database
from src.core.word_sets.wordlist_import import import_wordlist_to_database
from src.utils.helpers import print_analysis_results,get_supported_files
from src.utils.file_operations import process_files
from src.utils.db_operations import query_database,delete_logs
import os


def main():
    
    db = VocabularyDatabase()
    reader = TextReader()
    
    try:
        # 读取txt文件
        with open('/Users/yue/Documents/code/word-frequency-analysis/data/word_sets/AWL.txt', 'r') as file:
            wordlist = []
            for line in file:
                if line.strip():
                    word = line.split()[0]
                    if not word.isdigit():
                        wordlist.append(word)
        #df = pd.read_csv('/Users/yue/Documents/code/word-frequency-analysis/data/word_sets/AWL.txt', delim_whitespace=True, header=None)
        #wordlist = df[0][~df[0].str.match(r'^\d+$')].tolist()
        print(wordlist)
        
        # 导入数据
        import_wordlist_to_database(db, wordlist)
        print("导入完成")
        
        # 输出一些统计信息
        metadata = reader.get_metadata()
        print(f"文件大小: {metadata['file_size']} bytes")
        print(f"总字符数: {metadata['char_count']}")
        print(f"总词数: {metadata['word_count']}")
        
    except FileNotFoundError:
        print("找不到文件")
    except Exception as e:
        print(f"导入过程出错: {e}")

    lemmas = db.get_all_lemmas()
    print("所有lemmas:", lemmas)



'''
def main():
    
    # 初始化数据库并选择功能
    processor = TextProcessor()
    storage_manager = StorageManager()

    while True:
        print("\n主菜单:")
        print("1. 处理新文本")
        print("2. 删除文本")
        print("3. 查询数据库")
        print("0. 退出程序")

        choice = input("请选择操作 (0-3): ")

        try:
            if choice == '0':
                print("程序退出")
                break
            elif choice == '1':
                # 增：新文本处理
                directory_path = input("请输入要处理的文件夹路径: ")
                process_files(
                    directory_path=directory_path,
                    processor=processor,
                    storage_manager=storage_manager,
                    min_frequency=100
                )
            elif choice == '2':
                # 删：文本条目删除
                delete_logs(storage_manager)
            elif choice == '3':
                # 查：查询现有数据库
                query_database(storage_manager)
            else:
                print("无效的选择，请重试")

        except Exception as e:
            print(f"操作失败: {str(e)}")
'''

if __name__ == "__main__":
    main()
    
