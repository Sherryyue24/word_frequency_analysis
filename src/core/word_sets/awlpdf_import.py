import sqlite3
from src.core.vocabulary_database import VocabularyDatabase


def parse_awl_data(content):
    """解析AWL文档内容并返回结构化数据"""
    current_sublist = None
    words_data = []
    
    for line in content.split('\n'):
        line = line.strip()
        
        # 检测sublist标题
        if line.startswith('Sublist'):
            try:
                current_sublist = int(line.split()[1])
                continue
            except (IndexError, ValueError):
                continue
                
        # 跳过空行和标题行
        if not line or line.startswith(('Overview', 'Contents', 'Guidance')):
            continue
            
        # 解析单词数据
        if current_sublist and line[0].isdigit():
            parts = line.split()
            if len(parts) >= 2:
                word_data = {
                    'sublist': current_sublist,
                    'base_word': None,
                    'forms': set()
                }
                
                # 提取所有词形
                for part in parts[1:]:
                    # 清理标点和特殊字符
                    word = part.strip('.,()[]{}').lower()
                    if word and word.isalpha():
                        if not word_data['base_word']:
                            word_data['base_word'] = word
                        word_data['forms'].add(word)
                
                if word_data['base_word']:
                    words_data.append(word_data)
    
    return words_data
'''
def import_awl_to_database(db, content):
    ## 添加标签
    db.add_tag(tag_name="AWL")

    """将AWL数据导入到现有数据库"""
    words_data = parse_awl_data(content)
    
    for word_data in words_data:
        # 首先添加基本词形
        #db.add_word_with_tag(word_data['base_word'],tag_name="AWL")
        db.add_word(word_data['base_word'])
        
        # 然后添加其他词形
        for form in word_data['forms']:
            if form != word_data['base_word']:
                #db.add_word_with_tag(form,tag_name="AWL")
                db.add_word(form)
'''
def import_awl_to_database(db, content):
    """将AWL数据导入到现有数据库"""
    words_data = parse_awl_data(content)
    
    with sqlite3.connect(db.db_path) as conn:
        try:
            # 开始事务
            conn.execute("BEGIN TRANSACTION")
            
            # 首先添加所有单词
            for word_data in words_data:
                # 添加基本词形
                db.add_word(word_data['base_word'])
                
                # 添加其他词形
                for form in word_data['forms']:
                    if form != word_data['base_word']:
                        db.add_word(form)
            
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