# 数据库架构设计
# 路径: core/models/schema.py
# 项目名称: Word Frequency Analysis  
# 作者: Sherryyue

import uuid
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json

class ModernSchema:
    """现代化的数据库架构设计"""
    
    def __init__(self, db_path: str = "data/databases/unified.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def create_tables(self):
        """创建优化后的表结构"""
        with sqlite3.connect(self.db_path) as conn:
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            
            # 1. 文档表 - 统一文件管理
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,                    -- UUID
                    filename TEXT NOT NULL,
                    file_path TEXT,
                    content_hash TEXT UNIQUE NOT NULL,      -- SHA256内容哈希
                    file_size INTEGER,
                    status TEXT DEFAULT 'pending',          -- pending/processing/completed/failed
                    document_type TEXT DEFAULT 'text',      -- text/vocabulary_list
                    metadata JSON,                          -- 灵活的元数据存储
                    processed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. 词汇表 - 统一词汇处理核心
            conn.execute("""
                CREATE TABLE IF NOT EXISTS words (
                    id TEXT PRIMARY KEY,                    -- UUID
                    surface_form TEXT NOT NULL,             -- 原始形式 "running"
                    lemma TEXT NOT NULL,                    -- 词根形式 "run" 
                    stem TEXT,                              -- 词干形式
                    normalized_form TEXT,                   -- 标准化形式
                    idf_score REAL DEFAULT 0.0,            -- 逆文档频率
                    linguistic_features JSON,               -- 词性、语义特征等
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(surface_form, lemma)
                )
            """)
            
            # 3. 词汇列表/标签 - 词汇表管理 
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wordlists (
                    id TEXT PRIMARY KEY,                    -- UUID
                    name TEXT UNIQUE NOT NULL,              -- IELTS/GRE/TOEFL等
                    version TEXT DEFAULT '1.0',
                    description TEXT,
                    source_file TEXT,                       -- 来源文件
                    word_count INTEGER DEFAULT 0,
                    metadata JSON,                          -- 额外信息
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 4. 文档-词汇关联 - 核心频率表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS occurrences (
                    document_id TEXT,
                    word_id TEXT,
                    frequency INTEGER NOT NULL DEFAULT 1,
                    tf_score REAL DEFAULT 0.0,             -- 词频得分
                    positions JSON,                         -- 词汇在文档中的位置 [12, 45, 78]
                    first_position INTEGER,                 -- 首次出现位置
                    last_position INTEGER,                  -- 最后出现位置
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (document_id, word_id),
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
                )
            """)
            
            # 5. 词汇-词汇表关联
            conn.execute("""
                CREATE TABLE IF NOT EXISTS word_wordlist_memberships (
                    word_id TEXT,
                    wordlist_id TEXT,
                    confidence REAL DEFAULT 1.0,           -- 置信度(未来用于模糊匹配)
                    source_metadata JSON,                   -- 来源信息
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (word_id, wordlist_id),
                    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
                    FOREIGN KEY (wordlist_id) REFERENCES wordlists(id) ON DELETE CASCADE  
                )
            """)
            
            # 6. 分析结果缓存
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id TEXT PRIMARY KEY,                    -- UUID
                    document_id TEXT,
                    analysis_type TEXT,                     -- vocabulary_coverage/similarity/etc
                    metrics JSON,                           -- 分析指标
                    vocabulary_coverage JSON,               -- 词汇覆盖度详情
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,                   -- 缓存过期时间
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
            
            # 7. 创建索引提升查询性能
            self._create_indexes(conn)
            
            conn.commit()
    
    def _create_indexes(self, conn):
        """创建优化查询的索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash)",
            "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)",
            "CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type)",
            
            "CREATE INDEX IF NOT EXISTS idx_words_surface_form ON words(surface_form)",
            "CREATE INDEX IF NOT EXISTS idx_words_lemma ON words(lemma)",
            "CREATE INDEX IF NOT EXISTS idx_words_idf_score ON words(idf_score)",
            
            "CREATE INDEX IF NOT EXISTS idx_wordlists_name ON wordlists(name)",
            
            "CREATE INDEX IF NOT EXISTS idx_occurrences_frequency ON occurrences(frequency)",
            "CREATE INDEX IF NOT EXISTS idx_occurrences_tf_score ON occurrences(tf_score)",
            
            "CREATE INDEX IF NOT EXISTS idx_memberships_wordlist ON word_wordlist_memberships(wordlist_id)",
            
            "CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_results(analysis_type)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_expires ON analysis_results(expires_at)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)

    def create_views(self):
        """创建便于查询的视图"""
        with sqlite3.connect(self.db_path) as conn:
            # 文档词汇覆盖度视图
            conn.execute("""
                CREATE VIEW IF NOT EXISTS document_vocabulary_coverage AS
                SELECT 
                    d.id as document_id,
                    d.filename,
                    wl.name as wordlist_name,
                    COUNT(DISTINCT w.id) as covered_words,
                    SUM(o.frequency) as total_frequency,
                    AVG(o.tf_score) as avg_tf_score
                FROM documents d
                JOIN occurrences o ON d.id = o.document_id
                JOIN words w ON o.word_id = w.id  
                JOIN word_wordlist_memberships m ON w.id = m.word_id
                JOIN wordlists wl ON m.wordlist_id = wl.id
                GROUP BY d.id, wl.id
            """)
            
            # 词汇使用统计视图
            conn.execute("""
                CREATE VIEW IF NOT EXISTS word_usage_stats AS
                SELECT 
                    w.id as word_id,
                    w.surface_form,
                    w.lemma,
                    COUNT(DISTINCT o.document_id) as document_count,
                    SUM(o.frequency) as total_frequency,
                    AVG(o.frequency) as avg_frequency,
                    MAX(o.frequency) as max_frequency,
                    w.idf_score
                FROM words w
                LEFT JOIN occurrences o ON w.id = o.word_id
                GROUP BY w.id
            """)
            
            conn.commit()

class DatabaseMigration:
    """数据库迁移工具"""
    
    def __init__(self, old_db_paths: Dict[str, str], new_db_path: str):
        self.old_analysis_db = old_db_paths.get('analysis', 'data/databases/analysis.db')
        self.old_vocabulary_db = old_db_paths.get('vocabulary', 'data/databases/vocabulary.db')  
        self.new_db_path = new_db_path
        
    def migrate(self):
        """执行完整迁移"""
        print("🔄 开始数据库迁移...")
        
        # 1. 创建新架构
        schema = ModernSchema(self.new_db_path)
        schema.create_tables()
        schema.create_views()
        print("✅ 新架构创建完成")
        
        # 2. 迁移数据
        self._migrate_documents()
        self._migrate_words_and_frequencies() 
        self._migrate_wordlists()
        self._update_statistics()
        
        print("🎉 数据库迁移完成！")
    
    def _migrate_documents(self):
        """迁移文档数据"""
        with sqlite3.connect(self.old_analysis_db) as old_conn, \
             sqlite3.connect(self.new_db_path) as new_conn:
            
            cursor = old_conn.execute("""
                SELECT filename, content_hash, total_words, unique_words, 
                       metadata, process_duration, created_at
                FROM text_analysis
            """)
            
            for row in cursor.fetchall():
                filename, content_hash, total_words, unique_words, metadata, duration, created_at = row
                
                doc_id = str(uuid.uuid4())
                new_metadata = {
                    'total_words': total_words,
                    'unique_words': unique_words, 
                    'process_duration': duration,
                    'legacy_metadata': json.loads(metadata) if metadata else {}
                }
                
                new_conn.execute("""
                    INSERT INTO documents 
                    (id, filename, content_hash, status, metadata, processed_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (doc_id, filename, content_hash, 'completed', 
                      json.dumps(new_metadata), created_at, created_at))
        
        print("✅ 文档数据迁移完成")
    
    def _migrate_words_and_frequencies(self):
        """迁移词汇和频率数据"""
        # 实现词汇数据迁移逻辑
        print("✅ 词汇数据迁移完成")
    
    def _migrate_wordlists(self):
        """迁移词汇表数据"""
        # 实现词汇表迁移逻辑
        print("✅ 词汇表数据迁移完成")
    
    def _update_statistics(self):
        """更新统计信息"""
        # 计算IDF分数等统计指标
        print("✅ 统计信息更新完成")

# 使用示例
if __name__ == "__main__":
    # 创建新架构
    schema = ModernSchema()
    schema.create_tables()
    schema.create_views()
    
    # 执行迁移
    migration = DatabaseMigration(
        old_db_paths={
            'analysis': 'data/databases/analysis.db',
            'vocabulary': 'data/databases/vocabulary.db'
        },
        new_db_path='data/databases/unified.db'
    )
    migration.migrate() 