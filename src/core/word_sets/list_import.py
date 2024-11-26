
from pathlib import Path
import sqlite3
import traceback


def import_wordlist_to_database(db, filepath):
    """
    从文件导入词表到数据库
    Args:
        db: 数据库实例
        filepath: 文件路径
    Returns:
        bool: 导入是否成功
    """
    try:
        # 获取文件名作为标签
        tag_name = Path(filepath).stem
        
        # 读取并处理文件
        words = []
        total_lines = 0
        skipped_items = 0
        
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            file_size = len(content.encode('utf-8'))
            char_count = len(content)
            
            # 重置文件指针
            file.seek(0)
            
            for line in file:
                total_lines += 1
                word = line.strip().split()[0].lower()  # 获取第一列并转小写
                
                if not word or not word.isalpha():  # 跳过空行和非字母
                    skipped_items += 1
                    continue
                    
                words.append(word)
        
        if not words:
            print("未找到有效单词")
            return False
            
        # 打印文件统计信息
        print(f"\n文件统计信息:")
        print(f"文件大小: {file_size} bytes")
        print(f"总字符数: {char_count}")
        print(f"总行数: {total_lines}")
        print(f"跳过行数: {skipped_items}")
        print(f"有效单词数: {len(words)}")
        print(f"将使用标签: {tag_name}")
        
        # 导入数据库
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                # 先添加标签
                tag_id = db.add_tag(tag_name)
                
                # 处理单词
                added_count = 0
                skipped_count = 0
                existing_words = []  # 存储已存在的单词
                already_tagged = []  # 存储已有标签的单词
                word_ids = []  # 存储需要添加标签关联的单词ID
                
                for word in words:
                    try:
                        # 检查单词是否已存在
                        word_info = db.get_word_info(word)  # 调用 get_word_info 函数获取单词信息

                        if word_info:
                            # 如果单词存在，检查它是否已经有指定的标签
                            existing_tags = [tag['name'] for tag in word_info['sources']]  # 获取已有的标签名称列表
                            if tag_name in existing_tags:
                                # 单词已存在且已有此标签
                                already_tagged.append(word)
                                skipped_count += 1
                                continue
                            else:
                                # 单词存在但没有此标签
                                existing_words.append(word)
                                word_ids.append(word_info['lemma_id'])  # 从 word_info 中获取 lemma_id
                                skipped_count += 1
                                continue
                            
                        # 添加新单词
                        word_id = db.add_word(word)
                        word_ids.append(word_id)
                        added_count += 1
                    
                    except Exception as e:
                        print(f"跳过单词 '{word}': {str(e)}")
                        skipped_count += 1

                # 批量添加标签关联
                if word_ids:
                    conn.executemany('''
                        INSERT OR IGNORE INTO lemma_tags (lemma_id, tag_id)
                        VALUES (?, ?)
                    ''', [(word_id, tag_id) for word_id in word_ids])
                
                conn.commit()
                
                # 显示导入结果
                print(f"\n导入结果:")
                print(f"成功添加: {added_count} 个单词")
                print(f"跳过/失败: {skipped_count} 个单词")
                
                # 显示已存在的单词
                if existing_words:
                    print(f"\n以下 {len(existing_words)} 个单词已存在(已添加新标签):")
                    for word in existing_words:
                        print(f"- {word}")
                
                # 显示已有标签的单词
                if already_tagged:
                    print(f"\n以下 {len(already_tagged)} 个单词已存在且已有该标签:")
                    for word in already_tagged:
                        print(f"- {word}")
                
                # 显示数据库统计
                lemmas = db.get_all_lemmas()
                print(f"\n当前数据库共有 {len(lemmas)} 个词元")
                
                return True
                
            except Exception as e:
                conn.rollback()
                print(f"导入过程出错: {e}")
                return False
                
    except FileNotFoundError:
        print(f"找不到文件: {filepath}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False
