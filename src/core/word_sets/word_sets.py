import sqlite3
from src.core.vocabulary_database import VocabularyDatabase

def parse_wordlist_data(first_column):
    """解析AWL单词列表并返回结构化数据"""
    words_data = []
    
    for word in first_column:
        # 跳过空值或非字母的项
        if not word or not word.isalpha():
            continue
            
        word_data = {
            'base_word': word.lower(),
            'forms': {word.lower()}  # 使用集合存储词形，初始只包含基本词形
        }
        
        words_data.append(word_data)
    
    return words_data

def import_wordlist_to_database(db, first_column):
    """将AWL数据导入到现有数据库"""
    words_data = parse_wordlist_data(first_column)
    
    with sqlite3.connect(db.db_path) as conn:
        try:
            # 开始事务
            conn.execute("BEGIN TRANSACTION")
            
            # 添加所有单词
            for word_data in words_data:
                # 添加基本词形
                db.add_word(word_data['base_word'])
            
            # 获取所有添加的单词的lemma_id
            cursor = conn.cursor()
            
            # 添加AWL标签
            tag_id = db.add_tag("AWL")
            
            # 为所有添加的单词关联AWL标签
            cursor.execute('''
                INSERT OR IGNORE INTO lemma_tags (lemma_id, tag_id)
                SELECT id, ? FROM lemmas
                WHERE lemma IN (
                    SELECT DISTINCT form 
                    FROM word_forms
                )
            ''', (tag_id,))
            
            conn.commit()
            print("导入完成")
            
        except Exception as e:
            conn.rollback()
            print(f"导入过程出错: {e}")
            raise