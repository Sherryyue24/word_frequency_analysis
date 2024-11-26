from pathlib import Path
from src.core.vocabulary_database import VocabularyDatabase
from src.core.word_analyzer import analyze_text
from src.core.file_reader import TextReader
from src.core.analysis_database import StorageManager
from src.core.file_processor import TextProcessor
from datetime import datetime
from src.core.word_sets.list_import import import_wordlist_to_database
from src.utils.file_operations import process_files
from src.utils.db_operations import query_database,delete_logs
import os



def main():
    # 初始化所有管理器
    processor = TextProcessor()
    storage_manager = StorageManager()
    vocab_db = VocabularyDatabase()
    reader = TextReader()

    while True:
        print("\n=== 文本处理与词汇管理系统 ===")
        print("1. 文本处理")
        print("2. 词汇管理")
        print("0. 退出程序")

        main_choice = input("\n请选择主功能 (0-2): ")

        try:
            if main_choice == '0':
                print("\n感谢使用！程序已退出。")
                break
                
            elif main_choice == '1':
                # 文本处理子菜单
                while True:
                    print("\n=== 文本处理子系统 ===")
                    print("1. 处理新文本")
                    print("2. 删除文本")
                    print("3. 查询数据库")
                    print("0. 返回主菜单")

                    sub_choice = input("\n请选择操作 (0-3): ")

                    if sub_choice == '0':
                        break
                    elif sub_choice == '1':
                        directory_path = input("请输入要处理的文件夹路径: ")
                        process_files(
                            directory_path=directory_path,
                            processor=processor,
                            storage_manager=storage_manager,
                            min_frequency=100
                        )
                    elif sub_choice == '2':
                        delete_logs(storage_manager)
                    elif sub_choice == '3':
                        query_database(storage_manager)
                    else:
                        print("无效的选择，请重试")

            elif main_choice == '2':
                # 词汇管理子菜单
                while True:
                    print("\n=== 词汇管理子系统 ===")
                    print("1. 查询单个单词")
                    print("2. 显示所有标签")
                    print("3. 查询特定标签下的所有单词")
                    print("4. 从文件导入词表") 
                    print("0. 返回主菜单")

                    sub_choice = input("\n请选择功能 (0-4): ")

                    if sub_choice == '0':
                        break
                    elif sub_choice == '1':
                        word = input("请输入要查询的单词: ").strip()
                        info = vocab_db.get_word_info(word)
                        
                        if info:
                            print("\n=== 查询结果 ===")
                            print(f"词元 (Lemma): {info['lemma']}")

                            print("\n词性 (Parts of Speech):")
                            # 定义详细的词性映射表
                            pos_map_detailed = {
                                'CC': '并列连词 (Coordinating conjunction)',
                                'CD': '基数词 (Cardinal number)',
                                'DT': '限定词 (Determiner)',
                                'EX': '存在性词 (Existential there)',
                                'FW': '外来词 (Foreign word)',
                                'IN': '介词或从属连词 (Preposition or subordinating conjunction)',
                                'JJ': '形容词 (Adjective)',
                                'JJR': '形容词比较级 (Adjective, comparative)',
                                'JJS': '形容词最高级 (Adjective, superlative)',
                                'LS': '列表项标记 (List item marker)',
                                'MD': '情态动词 (Modal)',
                                'NN': '名词单数 (Noun, singular or mass)',
                                'NNS': '名词复数 (Noun, plural)',
                                'NNP': '专有名词单数 (Proper noun, singular)',
                                'NNPS': '专有名词复数 (Proper noun, plural)',
                                'PDT': '前限定词 (Predeterminer)',
                                'POS': '所有格标记 (Possessive ending)',
                                'PRP': '人称代词 (Personal pronoun)',
                                'PRP$': '物主代词 (Possessive pronoun)',
                                'RB': '副词 (Adverb)',
                                'RBR': '副词比较级 (Adverb, comparative)',
                                'RBS': '副词最高级 (Adverb, superlative)',
                                'RP': '小品词 (Particle)',
                                'SYM': '符号 (Symbol)',
                                'TO': '"to" (to)',
                                'UH': '感叹词 (Interjection)',
                                'VB': '动词原形 (Verb, base form)',
                                'VBD': '动词过去式 (Verb, past tense)',
                                'VBG': '动词现在分词 (Verb, gerund or present participle)',
                                'VBN': '动词过去分词 (Verb, past participle)',
                                'VBP': '动词非第三人称单数现在式 (Verb, non-3rd person singular present)',
                                'VBZ': '动词第三人称单数现在式 (Verb, 3rd person singular present)',
                                'WDT': 'Wh限定词 (Wh-determiner)',
                                'WP': 'Wh代词 (Wh-pronoun)',
                                'WP$': 'Wh物主代词 (Possessive wh-pronoun)',
                                'WRB': 'Wh副词 (Wh-adverb)'
                            }

                            # 遍历词性列表并输出详细信息
                            for pos in info['pos']:
                                detailed_pos = pos.get('detailed_pos')  # 获取详细词性
                                print(f"{pos_map_detailed.get(detailed_pos, detailed_pos)}")
                            
                            print("\n词形变化 (Word Forms):")
                            for form in sorted(info['forms']):
                                print(f"- {form}")
                            
                            if info['derivatives']:
                                print("\n派生词 (Derivatives):")
                                for derivative in sorted(info['derivatives']):
                                    print(f"- {derivative}")
                            
                            if info['tags']:  # 修改这里，使用新的 tags 字段
                                print("\n标签 (Tags):")
                                for tag in sorted(info['tags']):
                                    print(f"- {tag}")
                                    
                        else:
                            print(f"\n未找到单词 '{word}' 的相关信息")

                    elif sub_choice == '2':
                        tags = vocab_db.get_all_tags()  # 需要在VocabularyDatabase类中添加这个方法
                        if tags:
                            print("\n所有标签及其包含的单词数量:")
                            for tag, word_count in tags.items():
                                print(f"- {tag}: {word_count}个单词")
                            print(f"\n总计 {len(tags)} 个标签")
                        else:
                            print("\n数据库中还没有任何标签")                   

                    elif sub_choice == '3':
                        tag = input("请输入标签名: ").strip()
                        words = vocab_db.get_words_by_tag(tag)
                        
                        if words:
                            # 创建输出文件名（使用标签名和时间戳）
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            output_file = f"tag_{tag}_{timestamp}.txt"
                            
                            # 将单词保存到文件
                            with open(output_file, 'w', encoding='utf-8') as f:
                                f.write(f"=== 标签 '{tag}' 下的单词 ===\n\n")
                                for word in sorted(words):
                                    f.write(f"{word}\n")
                            
                            # 只打印单词数量和文件保存位置
                            print(f"\n标签 '{tag}' 下共有 {len(words)} 个单词")
                            print(f"详细列表已保存至: {output_file}")
                        else:
                            print(f"\n未找到标签 '{tag}' 下的单词")                
                    
                    elif sub_choice == '4':
                        filepath = input("请输入词表文件路径: ").strip()
                        try:
                            import_wordlist_to_database(vocab_db,filepath)                               
                        except FileNotFoundError:
                            print("\n错误：找不到指定文件")
                        except Exception as e:
                            print(f"\n导入过程出错: {e}")


                    else:
                        print("无效的选择，请重试")
            
            else:
                print("无效的选择，请重试")

        except Exception as e:
            print(f"操作失败: {str(e)}")

if __name__ == "__main__":
    main()