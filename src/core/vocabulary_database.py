import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from pattern.en import (conjugate, INFINITIVE, PRESENT, PAST, PARTICIPLE,
                       pluralize, singularize, comparative, superlative)
import sqlite3
from datetime import datetime
from pathlib import Path

# 下载必要的资源
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger_en')
nltk.download('tagsets')  # 下载 POS 标记的说明

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
            
            # 词性表，存储详细词性和 WordNet 词性
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pos (
                    id INTEGER PRIMARY KEY,
                    lemma_id INTEGER,
                    detailed_pos TEXT,  -- Penn Treebank 标记 (如 NNP, VBG 等)
                    wordnet_pos TEXT,   -- WordNet 标记 (如 n, v, a, r)
                    FOREIGN KEY (lemma_id) REFERENCES lemmas(id),
                    UNIQUE(lemma_id, detailed_pos)
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

    def get_detailed_pos(self, word):
        """
        获取详细的 Penn Treebank 词性标记
        """
        tag = nltk.pos_tag([word])[0][1]  # 获取完整的 Penn Treebank 标记
        return tag

    def penn_to_wordnet_pos(self, tag):
        """
        将 Penn Treebank 标记映射到 WordNet 支持的词性
        """
        tag_dict = {
            "N": wordnet.NOUN,  # 名词
            "V": wordnet.VERB,  # 动词
            "J": wordnet.ADJ,   # 形容词
            "R": wordnet.ADV    # 副词
        }
        return tag_dict.get(tag[0].upper(), None)  # 返回大类词性，无法映射时返回 None

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
          
    def add_word(self, word):
        """添加单词及其所有相关形式到数据库，返回lemma_id"""
        word = word.lower().strip()
        detailed_pos = self.get_detailed_pos(word)  
        wordnet_pos = self.penn_to_wordnet_pos(detailed_pos)  
        lemma = self.lemmatizer.lemmatize(word, wordnet_pos if wordnet_pos else wordnet.NOUN)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 首先确保我们能获得正确的lemma_id
            try:
                cursor.execute('INSERT INTO lemmas (lemma) VALUES (?)', (lemma,))
                lemma_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                cursor.execute('SELECT id FROM lemmas WHERE lemma = ?', (lemma,))
                result = cursor.fetchone()
                lemma_id = result[0] if result else None
                
            if lemma_id is None:
                raise ValueError(f"Failed to get lemma_id for word: {word}")
                
            # 收集并存储所有相关信息
            forms = set([lemma])  # 基本形式
            pos_set = set()
            derivatives = set()
            
            # 获取词性和派生词
            for synset in wordnet.synsets(lemma):
                pos_set.add(synset.pos())
                for lemma_obj in synset.lemmas():
                    for derived in lemma_obj.derivationally_related_forms():
                        derivatives.add(derived.name())
            
            # 使用 pattern 获取词形变化
            if 'v' in pos_set:  # 动词
                forms.add(conjugate(lemma, INFINITIVE))
                forms.add(conjugate(lemma, PRESENT, 3))
                forms.add(conjugate(lemma, PRESENT + 'PARTICIPLE'))
                forms.add(conjugate(lemma, PAST))
                forms.add(conjugate(lemma, PARTICIPLE))
                
            if 'n' in pos_set:  # 名词
                singular = singularize(lemma)
                plural = pluralize(lemma)
                forms.add(singular)
                forms.add(plural)
                forms.add(singular + "'s")
                if plural.endswith('s'):
                    forms.add(plural + "'")
                else:
                    forms.add(plural + "'s")
                    
            if 'a' in pos_set or 'j' in pos_set:  # 形容词
                forms.add(comparative(lemma))
                forms.add(superlative(lemma))
                if lemma.endswith('y'):
                    forms.add(lemma[:-1] + 'ily')
                elif lemma.endswith('le'):
                    forms.add(lemma[:-1] + 'y')
                else:
                    forms.add(lemma + 'ly')
                    
            if 'r' in pos_set:  # 副词
                try:
                    forms.add(comparative(lemma))
                    forms.add(superlative(lemma))
                except:
                    pass
            
            # 移除空字符串或 None 值
            forms = {f for f in forms if f and isinstance(f, str)}
            
            # 存储详细词性和 WordNet 词性
            try:
                cursor.execute('''INSERT INTO pos (lemma_id, detailed_pos, wordnet_pos) 
                                VALUES (?, ?, ?)''',
                                (lemma_id, detailed_pos, wordnet_pos if wordnet_pos else None))
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
            return lemma_id  # 确保返回lemma_id
    
    def get_all_tags(self):
        """获取所有标签及其包含的单词数量"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 查询所有标签及其关联的单词数量
                cursor.execute('''
                    SELECT t.name, COUNT(DISTINCT lt.lemma_id) as word_count
                    FROM tags t
                    LEFT JOIN lemma_tags lt ON t.id = lt.tag_id
                    GROUP BY t.name
                    ORDER BY t.name
                ''')
                
                results = cursor.fetchall()
                return {tag: count for tag, count in results}
                
        except sqlite3.Error as e:
            print(f"数据库查询出错: {e}")
            return {}

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
        detailed_pos = self.get_detailed_pos(word)  # 获取详细词性标记
        wordnet_pos = self.penn_to_wordnet_pos(detailed_pos)  # 获取 WordNet POS
        lemma = self.lemmatizer.lemmatize(word, wordnet_pos if wordnet_pos else wordnet.NOUN)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取词元ID
            cursor.execute('SELECT id FROM lemmas WHERE lemma = ?', (lemma,))
            result = cursor.fetchone()
            
            if result is None:
                return None
                
            lemma_id = result[0]
            
            # 获取详细词性标记
            cursor.execute('SELECT detailed_pos, wordnet_pos FROM pos WHERE lemma_id = ?', (lemma_id,))
            pos_list = [{'detailed_pos': row[0], 'wordnet_pos': row[1]} for row in cursor.fetchall()]
            
            # 获取词形
            cursor.execute('SELECT form FROM word_forms WHERE lemma_id = ?', (lemma_id,))
            forms = [row[0] for row in cursor.fetchall()]
            
            # 获取派生词
            cursor.execute('SELECT derivative FROM derivatives WHERE lemma_id = ?', (lemma_id,))
            derivatives = [row[0] for row in cursor.fetchall()]
            
            # 获取标签
            cursor.execute('''
                SELECT tags.name 
                FROM tags 
                JOIN lemma_tags ON tags.id = lemma_tags.tag_id 
                WHERE lemma_tags.lemma_id = ?
            ''', (lemma_id,))
            tags = [row[0] for row in cursor.fetchall()]
            
            return {
                'lemma': lemma,
                'lemma_id': lemma_id,  # 添加 lemma_id
                'pos': pos_list,
                'forms': forms,
                'derivatives': derivatives,
                'tags': tags  # 添加标签列表
            }

    def get_words_by_tag(self, tag_name):
        """
        查询属于特定标签的所有单词
        
        参数:
            tag_name (str): 标签名称
            
        返回:
            list: 包含所有符合条件的单词的列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 查询标签 ID
            cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name.lower(),))
            tag_result = cursor.fetchone()
            
            if tag_result is None:
                print(f"标签 '{tag_name}' 不存在。")
                return []
            
            tag_id = tag_result[0]
            
            # 查询属于该标签的所有词元 (lemmas)
            cursor.execute('''
                SELECT l.lemma 
                FROM lemmas l
                JOIN lemma_tags lt ON l.id = lt.lemma_id
                WHERE lt.tag_id = ?
            ''', (tag_id,))
            
            # 获取所有结果
            words = [row[0] for row in cursor.fetchall()]
            
            return words