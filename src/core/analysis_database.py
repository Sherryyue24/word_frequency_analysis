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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS text_analysis (
                    id INTEGER PRIMARY KEY,
                    filename TEXT,
                    content_hash TEXT UNIQUE,
                    analysis_date TEXT,
                    total_words INTEGER,
                    unique_words INTEGER,
                    metadata TEXT,
                    process_duration FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

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

    def store_analysis(self, content_hash: str, filename: str, basic_info: Dict, word_frequencies: Dict, process_duration: float):
        """存储分析结果到数据库"""
        if self.get_existing_analysis(content_hash):
            return

        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.execute("""
                    INSERT INTO text_analysis 
                    (filename, content_hash, analysis_date, total_words, unique_words, 
                     metadata, process_duration, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    filename,
                    content_hash,
                    datetime.now().isoformat(),
                    basic_info['total_words'],
                    basic_info['unique_words'],
                    json.dumps(basic_info.get('metadata', {})),
                    process_duration
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
                SELECT id, filename, analysis_date, total_words, unique_words, 
                       metadata, process_duration, created_at, updated_at
                FROM text_analysis 
                WHERE content_hash = ?
            """, (content_hash,))
            result = cursor.fetchone()
            
            if result:
                (text_id, filename, date, total_words, unique_words, 
                 metadata, process_duration, created_at, updated_at) = result
                basic_info = {
                    'filename': filename,
                    'analysis_date': date,
                    'total_words': total_words,
                    'unique_words': unique_words,
                    'metadata': json.loads(metadata),
                    'process_duration': process_duration,
                    'created_at': created_at,
                    'updated_at': updated_at
                }
                
                cursor = conn.execute("""
                    SELECT word, frequency 
                    FROM word_frequencies 
                    WHERE text_id = ?
                """, (text_id,))
                word_frequencies = dict(cursor.fetchall())
                
                return basic_info, word_frequencies
        return None

    def get_sepcific_analysis(self, text_id: int) -> list:
        """
        获取特定文本的词频统计
        Args:
            text_id: 文本ID
        Returns:
            list: 包含(词语, 频率)元组的列表，按频率降序排序
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 首先检查文本是否存在
                cursor = conn.execute("""
                    SELECT filename 
                    FROM text_analysis 
                    WHERE id = ?
                """, (text_id,))
                
                if not cursor.fetchone():
                    print(f"未找到ID为 {text_id} 的文本")
                    return []

                # 查询词频数据
                cursor = conn.execute("""
                    SELECT word, frequency 
                    FROM word_frequencies 
                    WHERE text_id = ?
                    ORDER BY frequency DESC, word ASC
                """, (text_id,))
                
                return cursor.fetchall()

        except sqlite3.Error as e:
            print(f"查询词频数据错误: {str(e)}")
            return []
        except Exception as e:
            print(f"发生错误: {str(e)}")
            return []

    def update_analysis_timestamp(self, content_hash: str) -> bool:
        """更新分析结果的时间戳"""
        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.execute("""
                    UPDATE text_analysis 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE content_hash = ?
                """, (content_hash,))
                return cursor.rowcount > 0
            except sqlite3.Error as e:
                print(f"更新时间戳时发生错误: {str(e)}")
                return False

    def get_all_analyses(self) -> list:
        """获取所有分析结果"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, filename, analysis_date
                FROM text_analysis
                ORDER BY analysis_date DESC
            """)
            return cursor.fetchall()

    def delete_analysis(self, text_id: int):
        """删除指定的分析结果"""
        # 确保 text_id 是整数
        try:
            text_id = int(text_id)
        except ValueError:
            print(f"无效的文本ID格式: {text_id}")
            return False

        with sqlite3.connect(self.db_path) as conn:
            try:
                # 首先获取要删除的词频数据
                cursor = conn.execute("""
                    SELECT word, frequency 
                    FROM word_frequencies 
                    WHERE text_id = ?
                """, (text_id,))  # 这里传入的是元组
                words_to_update = cursor.fetchall()
                
                # 更新 word_stats 表中的词频
                for word, freq in words_to_update:
                    # 减少总频率
                    conn.execute("""
                        UPDATE word_stats 
                        SET total_frequency = total_frequency - ?,
                            document_count = document_count - 1
                        WHERE word = ?
                    """, (freq, word))  # 注意参数顺序
                    
                    # 删除频率为0的词条
                    conn.execute("""
                        DELETE FROM word_stats 
                        WHERE word = ? AND 
                        (total_frequency <= 0 OR document_count <= 0)
                    """, (word,))  # 单个参数也需要是元组
                
                # 删除词频数据
                conn.execute("DELETE FROM word_frequencies WHERE text_id = ?", 
                        (text_id,))
                
                # 删除基本信息
                conn.execute("DELETE FROM text_analysis WHERE id = ?", 
                        (text_id,))
                
                conn.commit()
                print(f"成功删除文本ID {text_id} 的所有相关数据")
                return True
                
            except sqlite3.Error as e:
                print(f"删除分析结果错误: {str(e)}")
                conn.rollback()
                return False

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
        

    def get_word_usage(self, word: str) -> tuple:
        """
        获取特定词语在所有文本中的使用情况
        Args:
            word: 要查询的词语
        Returns:
            tuple: (总体统计信息, 具体使用列表)
                总体统计信息: (总频率, 文档数)
                具体使用列表: [(文本ID, 文件名, 分析日期, 在该文本中的频率), ...]
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 获取词语的总体统计信息
                cursor = conn.execute("""
                    SELECT total_frequency, document_count
                    FROM word_stats
                    WHERE word = ?
                """, (word,))
                
                stats = cursor.fetchone()
                if not stats:
                    return (0, 0), []

                # 获取词语在各个文本中的具体使用情况
                cursor = conn.execute("""
                    SELECT 
                        t.id,
                        t.filename,
                        t.analysis_date,
                        wf.frequency
                    FROM word_frequencies wf
                    JOIN text_analysis t ON wf.text_id = t.id
                    WHERE wf.word = ?
                    ORDER BY t.analysis_date DESC
                """, (word,))
                
                usage_list = cursor.fetchall()
                
                return stats, usage_list

        except sqlite3.Error as e:
            print(f"查询词语使用情况错误: {str(e)}")
            return (0, 0), []
        except Exception as e:
            print(f"发生错误: {str(e)}")
            return (0, 0), []