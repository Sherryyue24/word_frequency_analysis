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
    """现代化的数据库架构设计 - 最新版本"""
    
    def __init__(self, db_path: str = "data/databases/unified.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def create_tables(self):
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
            
            # 2. 系统词典表 - 支持多词性独立词条
            conn.execute("""
                CREATE TABLE IF NOT EXISTS common_dictionary (
                    id TEXT PRIMARY KEY,                    -- UUID
                    word TEXT NOT NULL,                     -- 标准词形 (小写)
                    lemma TEXT NOT NULL,                    -- 词根 (同word)
                    pos_primary TEXT NOT NULL,              -- 主要词性 (noun/verb/adjective/adverb)
                    definition TEXT,                        -- 核心定义 (一句话)
                    frequency_rank INTEGER,                 -- COCA词频排名 (1-60000)
                    difficulty_level INTEGER,               -- 难度级别 (1-5)
                    common_forms TEXT,                      -- JSON字符串: ["runs", "running", "ran"]
                    source_data JSON,                       -- 原始数据 {"coca_pos": "V", "wordnet_synsets": [...]}
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(word, pos_primary)               -- 词汇+词性的复合唯一约束
                )
            """)
            
            # 3. 用户词汇表 - 精确字典关联
            conn.execute("""
                CREATE TABLE IF NOT EXISTS words (
                    id TEXT PRIMARY KEY,                    -- UUID
                    surface_form TEXT NOT NULL,             -- 原始形式 "running"
                    lemma TEXT NOT NULL,                    -- 词根形式 "run" 
                    stem TEXT,                              -- 词干形式
                    normalized_form TEXT,                   -- 标准化形式
                    idf_score REAL DEFAULT 0.0,            -- 逆文档频率
                    linguistic_features JSON,               -- 词性、语义特征等
                    
                    -- 字典关联字段 (最新版本：使用dictionary_id精确关联)
                    dictionary_id TEXT,                     -- 关联到字典表的UUID
                    dictionary_found BOOLEAN DEFAULT FALSE, -- 是否在字典中找到
                    dictionary_rank INTEGER,                -- 对应的词频排名
                    difficulty_level INTEGER,               -- 继承的难度等级
                    
                    -- 个人学习状态
                    personal_status TEXT CHECK (personal_status IN ('new', 'learn', 'know', 'master')) DEFAULT 'new',
                    personal_notes TEXT,                    -- 个人笔记
                    status_updated_at TIMESTAMP,            -- 状态更新时间
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(surface_form, lemma),
                    FOREIGN KEY (dictionary_id) REFERENCES common_dictionary(id) ON DELETE SET NULL
                )
            """)
            
            # 4. 词汇列表/标签 - 词汇表管理 
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
            
            # 5. 文档-词汇关联 - 核心频率表
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
            
            # 6. 字典词汇-词汇表关联 
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dictionary_wordlist_memberships (
                    dictionary_id TEXT,                     -- 字典词汇的UUID (精确关联)
                    wordlist_id TEXT,
                    confidence REAL DEFAULT 1.0,           -- 置信度(未来用于模糊匹配)
                    source_metadata JSON,                   -- 来源信息
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (dictionary_id, wordlist_id),
                    FOREIGN KEY (dictionary_id) REFERENCES common_dictionary(id) ON DELETE CASCADE,
                    FOREIGN KEY (wordlist_id) REFERENCES wordlists(id) ON DELETE CASCADE  
                )
            """)
            
            # 7. 分析结果缓存
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
            
            # 8. 创建索引提升查询性能
            self._create_indexes(conn)
            
            conn.commit()
    
    def _create_indexes(self, conn):
        """创建优化查询的索引"""
        indexes = [
            # 文档表索引
            "CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash)",
            "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)",
            "CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type)",
            
            # 字典表索引
            "CREATE INDEX IF NOT EXISTS idx_dictionary_word ON common_dictionary(word)",
            "CREATE INDEX IF NOT EXISTS idx_dictionary_lemma ON common_dictionary(lemma)",
            "CREATE INDEX IF NOT EXISTS idx_dictionary_rank ON common_dictionary(frequency_rank)",
            "CREATE INDEX IF NOT EXISTS idx_dictionary_difficulty ON common_dictionary(difficulty_level)",
            "CREATE INDEX IF NOT EXISTS idx_dictionary_pos ON common_dictionary(pos_primary)",
            
            # 用户词汇表索引
            "CREATE INDEX IF NOT EXISTS idx_words_surface_form ON words(surface_form)",
            "CREATE INDEX IF NOT EXISTS idx_words_lemma ON words(lemma)",
            "CREATE INDEX IF NOT EXISTS idx_words_idf_score ON words(idf_score)",
            "CREATE INDEX IF NOT EXISTS idx_words_dictionary_id ON words(dictionary_id)",
            "CREATE INDEX IF NOT EXISTS idx_words_dictionary_found ON words(dictionary_found)",
            "CREATE INDEX IF NOT EXISTS idx_words_dictionary_rank ON words(dictionary_rank)",
            "CREATE INDEX IF NOT EXISTS idx_words_personal_status ON words(personal_status)",
            "CREATE INDEX IF NOT EXISTS idx_words_difficulty ON words(difficulty_level)",
            
            # 词汇表索引
            "CREATE INDEX IF NOT EXISTS idx_wordlists_name ON wordlists(name)",
            
            # 词频关联索引
            "CREATE INDEX IF NOT EXISTS idx_occurrences_frequency ON occurrences(frequency)",
            "CREATE INDEX IF NOT EXISTS idx_occurrences_tf_score ON occurrences(tf_score)",
            
            # 字典-词汇表关联索引
            "CREATE INDEX IF NOT EXISTS idx_dict_memberships_dict ON dictionary_wordlist_memberships(dictionary_id)",
            "CREATE INDEX IF NOT EXISTS idx_dict_memberships_wordlist ON dictionary_wordlist_memberships(wordlist_id)",
            
            # 分析结果索引
            "CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_results(analysis_type)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_expires ON analysis_results(expires_at)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)

    def create_views(self):
        """创建便于查询的视图"""
        with sqlite3.connect(self.db_path) as conn:
            # 文档词汇覆盖度视图 (通过字典ID精确关联)
            conn.execute("""
                CREATE VIEW IF NOT EXISTS document_vocabulary_coverage AS
                SELECT 
                    d.id as document_id,
                    d.filename,
                    wl.name as wordlist_name,
                    COUNT(DISTINCT w.id) as covered_words,
                    SUM(o.frequency) as total_frequency,
                    AVG(o.tf_score) as avg_tf_score,
                    COUNT(DISTINCT w.dictionary_id) as unique_dictionary_words
                FROM documents d
                JOIN occurrences o ON d.id = o.document_id
                JOIN words w ON o.word_id = w.id
                JOIN dictionary_wordlist_memberships m ON w.dictionary_id = m.dictionary_id
                JOIN wordlists wl ON m.wordlist_id = wl.id
                WHERE w.dictionary_found = TRUE
                GROUP BY d.id, wl.id
            """)
            
            # 词汇使用统计视图 (增强字典信息)
            conn.execute("""
                CREATE VIEW IF NOT EXISTS word_usage_stats AS
                SELECT 
                    w.id as word_id,
                    w.surface_form,
                    w.lemma,
                    w.dictionary_found,
                    w.dictionary_rank,
                    w.difficulty_level,
                    w.personal_status,
                    d.word as dictionary_word,
                    d.pos_primary as dictionary_pos,
                    d.definition as dictionary_definition,
                    COUNT(DISTINCT o.document_id) as document_count,
                    SUM(o.frequency) as total_frequency,
                    AVG(o.frequency) as avg_frequency,
                    MAX(o.frequency) as max_frequency,
                    w.idf_score
                FROM words w
                LEFT JOIN occurrences o ON w.id = o.word_id
                LEFT JOIN common_dictionary d ON w.dictionary_id = d.id
                GROUP BY w.id
            """)
            
            # 字典匹配统计视图
            conn.execute("""
                CREATE VIEW IF NOT EXISTS dictionary_match_stats AS
                SELECT 
                    d.id as document_id,
                    d.filename,
                    COUNT(DISTINCT w.id) as total_unique_words,
                    COUNT(DISTINCT CASE WHEN w.dictionary_found THEN w.id END) as dictionary_matched_words,
                    COUNT(DISTINCT CASE WHEN w.personal_status = 'new' THEN w.id END) as new_words,
                    COUNT(DISTINCT CASE WHEN w.personal_status = 'learn' THEN w.id END) as learning_words,
                    COUNT(DISTINCT CASE WHEN w.personal_status = 'know' THEN w.id END) as known_words,
                    COUNT(DISTINCT CASE WHEN w.personal_status = 'master' THEN w.id END) as mastered_words,
                    AVG(w.dictionary_rank) as avg_word_rank,
                    AVG(w.difficulty_level) as avg_difficulty
                FROM documents d
                JOIN occurrences o ON d.id = o.document_id
                JOIN words w ON o.word_id = w.id
                GROUP BY d.id
            """)
            
            # 个人学习进度视图
            conn.execute("""
                CREATE VIEW IF NOT EXISTS personal_learning_progress AS
                SELECT 
                    w.personal_status,
                    w.difficulty_level,
                    COUNT(*) as word_count,
                    AVG(w.dictionary_rank) as avg_rank,
                    COUNT(DISTINCT CASE WHEN w.dictionary_found THEN w.id END) as dictionary_matched
                FROM words w
                WHERE w.personal_status IS NOT NULL
                GROUP BY w.personal_status, w.difficulty_level
                ORDER BY w.difficulty_level, 
                        CASE w.personal_status 
                            WHEN 'new' THEN 1
                            WHEN 'learn' THEN 2
                            WHEN 'know' THEN 3
                            WHEN 'master' THEN 4
                        END
            """) 