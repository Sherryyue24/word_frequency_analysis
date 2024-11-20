import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import sqlite3
from datetime import datetime
from pathlib import Path

# 下载必要的资源
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

class VocabularyDatabase:
    def __init__(self, db_name='vocabulary.db'):
        self.lemmatizer = WordNetLemmatizer()
        self.db_path = Path("data") / db_name
        # 确保数据目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # 检查数据库文件是否存在
        if self.db_path.exists():
            print(f"数据库文件 {db_name} 已存在")
        else:
            print(f"创建新的数据库文件 {db_name}")
    
        self.setup_database()
        
    def setup_database(self):
        """创建数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 词元表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lemmas (
                    id INTEGER PRIMARY KEY,
                    lemma TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 词性表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pos (
                    id INTEGER PRIMARY KEY,
                    lemma_id INTEGER,
                    pos TEXT,
                    FOREIGN KEY (lemma_id) REFERENCES lemmas(id),
                    UNIQUE(lemma_id, pos)
                )
            ''')
            
            # 词形表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS word_forms (
                    id INTEGER PRIMARY KEY,
                    lemma_id INTEGER,
                    form TEXT,
                    FOREIGN KEY (lemma_id) REFERENCES lemmas(id),
                    UNIQUE(lemma_id, form)
                )
            ''')
            
            # 派生词表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS derivatives (
                    id INTEGER PRIMARY KEY,
                    lemma_id INTEGER,
                    derivative TEXT,
                    FOREIGN KEY (lemma_id) REFERENCES lemmas(id),
                    UNIQUE(lemma_id, derivative)
                )
            ''')
            
            # 标签表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 词汇-标签关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lemma_tags (
                    lemma_id INTEGER,
                    tag_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lemma_id) REFERENCES lemmas(id),
                    FOREIGN KEY (tag_id) REFERENCES tags(id),
                    UNIQUE(lemma_id, tag_id)
                )
            ''')
            
            conn.commit()

    def get_wordnet_pos(self, word):
        """获取词性标记"""
        tag = nltk.pos_tag([word])[0][1][0].upper()
        tag_dict = {
            "N": wordnet.NOUN,
            "V": wordnet.VERB,
            "J": wordnet.ADJ,
            "R": wordnet.ADV
        }
        return tag_dict.get(tag, wordnet.NOUN)

    def add_tag(self, tag_name, description=None):
        """添加新标签"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO tags (name, description) VALUES (?, ?)',
                             (tag_name.lower(), description))
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name.lower(),))
                return cursor.fetchone()[0]

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
            
    def add_word(self, word):
        """添加单词及其所有相关形式到数据库"""
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
            
            # 收集并存储所有相关信息
            forms = set([word])
            pos_set = set()
            derivatives = set()
            
            for synset in wordnet.synsets(lemma):
                # 添加词性
                pos_set.add(synset.pos())
                
                for lemma_obj in synset.lemmas():
                    # 添加词形
                    forms.add(lemma_obj.name())
                    
                    # 添加派生词
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
    
    def get_all_lemmas(self):
        """获取数据库中的所有lemmas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 直接从lemmas表获取所有lemma
            cursor.execute('SELECT lemma FROM lemmas')
            lemmas = [row[0] for row in cursor.fetchall()]
            
            return lemmas


    def get_word_info(self, word):
        """从数据库获取词的所有信息，包括标签"""
        word = word.lower().strip()
        pos = self.get_wordnet_pos(word)
        lemma = self.lemmatizer.lemmatize(word, pos)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取词元ID
            cursor.execute('SELECT id FROM lemmas WHERE lemma = ?', (lemma,))
            result = cursor.fetchone()
            
            if result is None:
                return None
                
            lemma_id = result[0]
            
            # 获取词性
            cursor.execute('SELECT pos FROM pos WHERE lemma_id = ?', (lemma_id,))
            pos_list = [row[0] for row in cursor.fetchall()]
            
            # 获取词形
            cursor.execute('SELECT form FROM word_forms WHERE lemma_id = ?', (lemma_id,))
            forms = [row[0] for row in cursor.fetchall()]
            
            # 获取派生词
            cursor.execute('SELECT derivative FROM derivatives WHERE lemma_id = ?', (lemma_id,))
            derivatives = [row[0] for row in cursor.fetchall()]
            
            # 获取标签
            cursor.execute('''
                SELECT t.name, t.description 
                FROM tags t 
                JOIN lemma_tags lt ON t.id = lt.tag_id 
                WHERE lt.lemma_id = ?
            ''', (lemma_id,))
            tags = cursor.fetchall()
            
            return {
                'lemma': lemma,
                'pos': pos_list,
                'forms': forms,
                'derivatives': derivatives,
                'sources': [{'name': t[0], 'description': t[1]} for t in tags]
            }

    def get_words_by_tag(self, tag_name):
        """获取特定标签下的所有词"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT l.lemma 
                FROM lemmas l
                JOIN lemma_tags lt ON l.id = lt.lemma_id
                JOIN tags t ON lt.tag_id = t.id
                WHERE t.name = ?
            ''', (tag_name.lower(),))
            return [row[0] for row in cursor.fetchall()]
