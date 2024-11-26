import sqlite3
from src.core.vocabulary_database import VocabularyDatabase


'''
def main():
    
    db = VocabularyDatabase()
    reader = TextReader()

    word ="happy"
    get_word_info()
    
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

def import_wordlist_from_file(db, filepath):
    """
    从文件导入词表到数据库，使用文件名作为标签
    
    Args:
        db: 数据库实例
        filepath: 文件路径
    
    Returns:
        bool: 导入是否成功
    """
    try:
        # 获取文件名作为标签（去除扩展名）
        tag_name = Path(filepath).stem
        
        # 读取文件，获取单词列表
        words = []
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                word = line.strip().split()[0].lower()  # 获取每行第一列并转小写
                if word and word.isalpha():  # 确保是非空的纯字母单词
                    words.append(word)
        
        if not words:
            print("未找到有效单词")
            return False
            
        print(f"找到 {len(words)} 个有效单词")
        print(f"将使用标签: {tag_name}")
        
        # 导入数据库
        with sqlite3.connect(db.db_path) as conn:
            # 开启事务
            conn.execute("BEGIN TRANSACTION")
            
            try:
                # 添加标签
                tag_id = db.add_tag(tag_name)
                
                # 添加单词并关联标签
                for word in words:
                    # 添加单词
                    word_id = db.add_word(word)
                    
                    # 关联标签
                    conn.execute('''
                        INSERT OR IGNORE INTO lemma_tags (lemma_id, tag_id)
                        VALUES (?, ?)
                    ''', (word_id, tag_id))
                
                conn.commit()
                print("导入完成")
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

def import_wordlist_from_file(db, reader, filepath):
    """从文件导入词表到数据库"""
    try:
        # 读取txt文件
        with open(filepath, 'r') as file:
            wordlist = []
            for line in file:
                if line.strip():
                    word = line.split()[0]
                    if not word.isdigit():
                        wordlist.append(word)
        print("读取到的词表:", wordlist)
        
        # 导入数据
        import_wordlist_to_database(db, wordlist)
        print("词表导入完成")
        
        # 输出统计信息
        metadata = reader.get_metadata()
        print(f"\n文件统计信息:")
        print(f"文件大小: {metadata['file_size']} bytes")
        print(f"总字符数: {metadata['char_count']}")
        print(f"总词数: {metadata['word_count']}")
        
        # 显示所有lemmas
        lemmas = db.get_all_lemmas()
        print("\n数据库中的所有lemmas:", lemmas)
        return True
        
    except FileNotFoundError:
        print("错误：找不到指定文件")
        return False
    except Exception as e:
        print(f"错误：导入过程出现异常: {e}")
        return False

def parse_txt_data(first_column):
    """解析一列单词列表并返回结构化数据"""
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
    words_data = parse_txt_data(first_column)
    
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


def add_word_with_tag(self, word, tag_name, tag_description=None):
        """添加单词及其标签"""
        word = word.lower().strip()
        pos = self.get_wordnet_pos(word)
        lemma = self.lemmatizer.lemmatize(word, pos)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 插入词元
            try:
                cursor.execute('INSERT INTO lemmas (lemma) VALUES (?)', (lemma,))
                lemma_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                cursor.execute('SELECT id FROM lemmas WHERE lemma = ?', (lemma,))
                lemma_id = cursor.fetchone()[0]
            
            
            # 添加标签
            print("添加标签")
            tag_id = self.add_tag(tag_name, tag_description)
            print("添加失败")
            

            # 关联词汇和标签
            
            try:
                cursor.execute('INSERT INTO lemma_tags (lemma_id, tag_id) VALUES (?, ?)',
                             (lemma_id, tag_id))
            except sqlite3.IntegrityError:
                print("无法关联")
            
            # 收集并存储所有相关信息
            forms = set([word])
            pos_set = set()
            derivatives = set()
            
            for synset in wordnet.synsets(lemma):
                pos_set.add(synset.pos())
                for lemma_obj in synset.lemmas():
                    forms.add(lemma_obj.name())
                    for derived in lemma_obj.derivationally_related_forms():
                        derivatives.add(derived.name())
            
            # 存储词性
            for pos in pos_set:
                try:
                    cursor.execute('INSERT INTO pos (lemma_id, pos) VALUES (?, ?)',
                                 (lemma_id, pos))
                except sqlite3.IntegrityError:
                    pass
            
            # 存储词形
            for form in forms:
                try:
                    cursor.execute('INSERT INTO word_forms (lemma_id, form) VALUES (?, ?)',
                                 (lemma_id, form))
                except sqlite3.IntegrityError:
                    pass
            
            # 存储派生词
            for derivative in derivatives:
                try:
                    cursor.execute('INSERT INTO derivatives (lemma_id, derivative) VALUES (?, ?)',
                                 (lemma_id, derivative))
                except sqlite3.IntegrityError:
                    pass
            
            conn.commit()