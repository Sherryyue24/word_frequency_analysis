import sqlite3
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple, List, Set

class StorageManager:
    def __init__(self, storage_type: str = "sqlite"):
        self.storage_type = storage_type
        self.db_path = "data/analysis.db"
        self._init_database()

    def _init_database(self):
        """初始化分析结果数据库"""
        with sqlite3.connect(self.db_path) as conn:
            # 原有的表结构保持不变
            conn.execute("""
                CREATE TABLE IF NOT EXISTS text_analysis (
                    id INTEGER PRIMARY KEY,
                    filename TEXT,
                    content_hash TEXT UNIQUE,
                    analysis_date TEXT,
                    total_words INTEGER,
                    unique_words INTEGER,
                    metadata TEXT
                )
            """)
            
            # 在word_frequencies表中添加processed字段
            conn.execute("""
                CREATE TABLE IF NOT EXISTS word_frequencies (
                    word TEXT,
                    frequency INTEGER,
                    text_id INTEGER,
                    processed BOOLEAN DEFAULT 0,
                    FOREIGN KEY (text_id) REFERENCES text_analysis(id),
                    PRIMARY KEY (word, text_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS word_stats (
                    word TEXT PRIMARY KEY,
                    total_frequency INTEGER,
                    document_count INTEGER,
                    text_ids TEXT
                )
            """)


    def store_analysis(self, content_hash: str, filename: str, basic_info: Dict, word_frequencies: Dict):
        """存储分析结果到数据库"""
        # 检查是否已存在分析结果
        if self.get_existing_analysis(content_hash):
            return

        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.execute("""
                    INSERT INTO text_analysis 
                    (filename, content_hash, analysis_date, total_words, unique_words, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    filename,
                    content_hash,
                    datetime.now().isoformat(),
                    basic_info['total_words'],
                    basic_info['unique_words'],
                    json.dumps(basic_info.get('metadata', {}))
                ))
                
                text_id = cursor.lastrowid
                
                word_freq_data = [(text_id, word, freq) 
                                for word, freq in word_frequencies.items()]
                conn.executemany("""
                    INSERT INTO word_frequencies (text_id, word, frequency)
                    VALUES (?, ?, ?)
                """, word_freq_data)
                
            except sqlite3.Error as e:
                print(f"分析结果数据库存储错误: {str(e)}")
                raise

    def calculate_text_hash(self, text: str) -> str:
        """计算文本的哈希值"""
        processed_text = "".join(text.lower().split())
        return hashlib.md5(processed_text.encode('utf-8')).hexdigest()

    def get_existing_analysis(self, content_hash: str) -> Optional[Tuple[dict, dict]]:
        """检查是否存在相同内容的分析结果"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, filename, analysis_date, total_words, unique_words, metadata
                FROM text_analysis 
                WHERE content_hash = ?
            """, (content_hash,))
            result = cursor.fetchone()
            
            if result:
                text_id, filename, date, total_words, unique_words, metadata = result
                basic_info = {
                    'filename': filename,
                    'analysis_date': date,
                    'total_words': total_words,
                    'unique_words': unique_words,
                    'metadata': json.loads(metadata)
                }
                
                cursor = conn.execute("""
                    SELECT word, frequency 
                    FROM word_frequencies 
                    WHERE text_id = ?
                """, (text_id,))
                word_frequencies = dict(cursor.fetchall())
                
                return basic_info, word_frequencies
        return None

    def get_all_analyses(self) -> list:
        """获取所有分析结果"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, filename, analysis_date, total_words, unique_words
                FROM text_analysis
                ORDER BY analysis_date DESC
            """)
            return cursor.fetchall()

    def delete_analysis(self, text_id: int):
        """删除指定的分析结果"""
        with sqlite3.connect(self.db_path) as conn:
            try:
                # 首先删除词频数据
                conn.execute("DELETE FROM word_frequencies WHERE text_id = ?", 
                           (text_id,))
                # 然后删除基本信息
                conn.execute("DELETE FROM text_analysis WHERE id = ?", 
                           (text_id,))
            except sqlite3.Error as e:
                print(f"删除分析结果错误: {str(e)}")
                raise


    def update_word_stats(self):
        """增量更新word_stats表的统计数据"""
        with sqlite3.connect(self.db_path) as conn:
            # 获取未处理的词频记录
            unprocessed_words = conn.execute("""
                SELECT word, frequency, text_id 
                FROM word_frequencies 
                WHERE processed = 0
            """).fetchall()
            
            # 如果没有新数据,直接返回
            if not unprocessed_words:
                print("所有记录都已处理！没有未处理的记录！")
                return
                
            # 更新word_stats表
            for word, frequency, text_id in unprocessed_words:
                # 尝试更新现有记录
                conn.execute("""
                    INSERT INTO word_stats (word, total_frequency, document_count, text_ids)
                    VALUES (?, ?, 1, ?)
                    ON CONFLICT(word) DO UPDATE SET
                        total_frequency = total_frequency + ?,
                        document_count = document_count + (CASE 
                            WHEN text_ids LIKE ? THEN 0 
                            ELSE 1 
                        END),
                        text_ids = CASE 
                            WHEN text_ids LIKE ? THEN text_ids
                            ELSE text_ids || ',' || ?
                        END
                """, (word, frequency, str(text_id), 
                    frequency, f'%{text_id}%', f'%{text_id}%', str(text_id)))
            
            # 标记已处理的记录
            conn.execute("""
                UPDATE word_frequencies 
                SET processed = 1 
                WHERE processed = 0
            """)
            
            conn.commit()

    def get_word_stats(self, min_frequency=None, min_documents=None):
        """获取词语统计信息,可以设置最小频率和最小文档数过滤"""
        query = "SELECT * FROM word_stats"
        conditions = []
        
        if min_frequency is not None:
            conditions.append(f"total_frequency >= {min_frequency}")
        if min_documents is not None:
            conditions.append(f"document_count >= {min_documents}")
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query)
            return cursor.fetchall()