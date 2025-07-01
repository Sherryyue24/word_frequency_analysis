# 数据库适配器 - 最新架构版本
# 路径: core/engines/database/database_adapter.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

from typing import Dict, List, Optional, Tuple, Any
import json
import sqlite3
from pathlib import Path

from .unified_database import UnifiedDatabase

class UnifiedDatabaseAdapter:
    """
    统一数据库适配器 - 最新架构版本
    提供高级API接口，内部使用统一数据库架构
    """
    
    def __init__(self, db_path: str = "data/databases/unified.db"):
        self.unified_db = UnifiedDatabase(db_path)
    
    # ================= 文档和分析管理 =================
    
    def store_analysis(self, content_hash: str, filename: str, basic_info: Dict, 
                      word_frequencies: Dict, process_duration: float, 
                      original_text: str = None):
        """存储文档分析结果"""
        # 添加文档
        metadata = {
            'total_words': basic_info.get('total_words', 0),
            'unique_words': basic_info.get('unique_words', 0),
            'process_duration': process_duration,
            'basic_info': basic_info
        }
        
        doc_id = self.unified_db.add_document(
            filename=filename,
            content=content_hash,
            document_type='text',
            metadata=metadata
        )
        
        # 存储词频数据，包含上下文用于语言学分析
        self.unified_db.store_word_frequencies(doc_id, word_frequencies, 
                                              context_text=original_text)
        
        # 更新文档状态
        self.unified_db.update_document_status(doc_id, 'completed', metadata)
    
    def get_existing_analysis(self, content_hash: str) -> Optional[Tuple[dict, dict]]:
        """检查是否存在相同内容的分析结果"""
        doc = self.unified_db.get_document_by_hash(content_hash)
        if not doc:
            return None
        
        # 获取基本信息
        metadata = json.loads(doc.get('metadata', '{}')) if doc.get('metadata') else {}
        basic_info = {
            'filename': doc['filename'],
            'analysis_date': doc.get('processed_at', doc['created_at']),
            'total_words': metadata.get('total_words', 0),
            'unique_words': metadata.get('unique_words', 0),
            'process_duration': metadata.get('process_duration', 0),
            'created_at': doc['created_at'],
            'updated_at': doc['updated_at']
        }
        
        # 获取词频数据
        word_frequencies = self._get_document_word_frequencies(doc['id'])
        
        return basic_info, word_frequencies
    
    def _get_document_word_frequencies(self, doc_id: str) -> Dict[str, int]:
        """获取文档的词频数据"""
        with sqlite3.connect(self.unified_db.db_path) as conn:
            cursor = conn.execute("""
                SELECT w.surface_form, o.frequency
                FROM occurrences o
                JOIN words w ON o.word_id = w.id
                WHERE o.document_id = ?
            """, (doc_id,))
            
            return dict(cursor.fetchall())
    
    def get_all_analyses(self) -> List[Tuple]:
        """获取所有分析结果"""
        documents = self.unified_db.get_all_documents(document_type='text')
        
        result = []
        for doc in documents:
            metadata = json.loads(doc.get('metadata', '{}')) if doc.get('metadata') else {}
            
            result.append((
                doc['id'],
                doc['filename'],
                doc.get('processed_at', doc['created_at']),
                metadata.get('total_words', 0),
                metadata.get('unique_words', 0)
            ))
        
        return result
    
    def get_all_texts(self) -> List[Dict]:
        """获取所有文本记录"""
        documents = self.unified_db.get_all_documents(document_type='text')
        
        result = []
        for doc in documents:
            metadata = json.loads(doc.get('metadata', '{}')) if doc.get('metadata') else {}
            
            result.append({
                'id': doc['id'],
                'filename': doc['filename'],
                'analysis_date': doc.get('processed_at', doc['created_at']),
                'total_words': metadata.get('total_words'),
                'unique_words': metadata.get('unique_words')
            })
        
        return result
    
    def get_sepcific_analysis(self, text_id: str) -> List[Tuple]:
        """获取特定文本的词频统计"""
        with sqlite3.connect(self.unified_db.db_path) as conn:
            cursor = conn.execute("""
                SELECT w.surface_form, o.frequency
                FROM occurrences o
                JOIN words w ON o.word_id = w.id
                WHERE o.document_id = ?
                ORDER BY o.frequency DESC, w.surface_form ASC
            """, (text_id,))
            
            return cursor.fetchall()
    
    def get_global_word_frequencies(self, min_frequency: int = 1, limit: int = 20) -> List[Tuple]:
        """获取全局词频统计"""
        with sqlite3.connect(self.unified_db.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    w.surface_form,
                    SUM(o.frequency) as total_frequency,
                    COUNT(DISTINCT o.document_id) as document_count
                FROM words w
                JOIN occurrences o ON w.id = o.word_id
                GROUP BY w.id
                HAVING total_frequency >= ?
                ORDER BY total_frequency DESC
                LIMIT ?
            """, (min_frequency, limit))
            
            return cursor.fetchall()
    
    def get_text_by_id(self, text_id: str) -> Optional[Dict]:
        """根据ID获取文本信息"""
        with sqlite3.connect(self.unified_db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM documents WHERE id = ?
            """, (text_id,))
            
            row = cursor.fetchone()
            if row:
                doc = dict(row)
                metadata = json.loads(doc.get('metadata', '{}')) if doc.get('metadata') else {}
                
                return {
                    'id': doc['id'],
                    'filename': doc['filename'],
                    'analysis_date': doc.get('processed_at', doc['created_at']),
                    'total_words': metadata.get('total_words'),
                    'unique_words': metadata.get('unique_words'),
                    'metadata': metadata
                }
        return None
    
    def delete_all_texts(self) -> bool:
        """删除所有文本记录"""
        try:
            with sqlite3.connect(self.unified_db.db_path) as conn:
                cursor = conn.execute("DELETE FROM documents WHERE document_type = 'text'")
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除失败: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """删除单个文档"""
        return self.unified_db.delete_document(doc_id)
    
    def delete_documents_by_type(self, document_type: str) -> int:
        """按类型批量删除文档"""
        return self.unified_db.delete_documents_by_type(document_type)
    
    def calculate_text_hash(self, text: str) -> str:
        """计算文本哈希"""
        return self.unified_db._calculate_content_hash(text)
    
    # ================= 词汇表管理 =================
    
    def create_wordlist(self, name: str, description: str = None) -> str:
        """创建新的词汇表"""
        return self.unified_db.create_wordlist(name, description)
    
    def add_words_to_wordlist(self, wordlist_name: str, words: List[str]) -> Dict:
        """将词汇添加到词汇表（通过字典关联）"""
        # 先获取词汇表
        wordlist = self.unified_db.get_wordlist_by_name(wordlist_name)
        if not wordlist:
            # 创建新词汇表
            wordlist_id = self.unified_db.create_wordlist(wordlist_name)
        else:
            wordlist_id = wordlist['id']
        
        # 添加词汇
        return self.unified_db.add_words_to_wordlist(wordlist_id, words)
    
    def get_all_wordlists(self) -> List[Dict]:
        """获取所有词汇表"""
        with sqlite3.connect(self.unified_db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, name, description, word_count, created_at
                FROM wordlists 
                ORDER BY name
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_wordlist_words(self, wordlist_name: str) -> List[str]:
        """获取词汇表中的词汇（通过字典关联）"""
        with sqlite3.connect(self.unified_db.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT d.word, d.pos_primary
                FROM wordlists wl
                JOIN dictionary_wordlist_memberships m ON wl.id = m.wordlist_id
                JOIN common_dictionary d ON m.dictionary_id = d.id
                WHERE wl.name = ?
                ORDER BY d.word
            """, (wordlist_name,))
            
            # 返回词汇列表，如果有多个词性，显示为"word (pos)"
            words = []
            current_word = None
            pos_list = []
            
            for word, pos in cursor.fetchall():
                if word != current_word:
                    if current_word and pos_list:
                        if len(pos_list) == 1:
                            words.append(current_word)
                        else:
                            words.append(f"{current_word} ({', '.join(pos_list)})")
                    current_word = word
                    pos_list = [pos]
                else:
                    pos_list.append(pos)
            
            # 处理最后一个词汇
            if current_word and pos_list:
                if len(pos_list) == 1:
                    words.append(current_word)
                else:
                    words.append(f"{current_word} ({', '.join(pos_list)})")
            
            return words
    
    # ================= 词汇查询和分析 =================
    
    def get_word_variants(self, word: str, doc_id: str = None) -> Dict:
        """获取词汇变形"""
        return self.unified_db.get_word_variants_with_frequencies(word, doc_id)
    
    def get_lemma_statistics(self) -> Dict:
        """获取词根统计"""
        return self.unified_db.get_unique_lemma_count()
    
    def get_lemma_analysis_data(self, doc_id: str = None) -> Dict:
        """获取词根分析数据"""
        return self.unified_db.get_lemma_analysis(doc_id)
    
    def get_linguistic_features(self, word: str) -> List[Dict]:
        """获取词汇的语言学特征"""
        return self.unified_db.get_word_linguistic_features(word)
    
    def get_words_by_pos(self, pos_type: str, limit: int = 50) -> List[Dict]:
        """根据词性获取词汇"""
        return self.unified_db.get_words_by_pos_type(pos_type, limit)
    
    def get_pos_statistics(self) -> Dict:
        """获取词性分布统计"""
        return self.unified_db.get_pos_distribution()
    
    def get_morphology_analysis(self) -> Dict:
        """获取形态学分析"""
        return self.unified_db.get_complex_words_analysis()
    
    # ================= 高级分析功能 =================
    
    def get_vocabulary_coverage_analysis(self, doc_id: str) -> List[Dict]:
        """获取词汇覆盖度分析"""
        return self.unified_db.get_vocabulary_coverage(doc_id)
    
    def analyze_document_similarity(self, doc_id1: str, doc_id2: str) -> Dict:
        """分析文档相似性"""
        return self.unified_db.analyze_document_similarity(doc_id1, doc_id2)
    
    def get_word_usage_statistics(self, min_frequency: int = 1) -> List[Dict]:
        """获取词汇使用统计"""
        return self.unified_db.get_word_usage_stats(min_frequency)
    
    def search_words(self, search_term: str, detailed: bool = False) -> List[Tuple]:
        """搜索词汇"""
        with sqlite3.connect(self.unified_db.db_path) as conn:
            if detailed:
                # 详细模式：包含字典信息
                cursor = conn.execute("""
                    SELECT 
                        w.surface_form,
                        w.lemma,
                        w.personal_status,
                        w.dictionary_found,
                        w.dictionary_rank,
                        w.difficulty_level,
                        d.pos_primary,
                        d.definition,
                        COUNT(DISTINCT o.document_id) as doc_count,
                        SUM(o.frequency) as total_freq
                    FROM words w
                    LEFT JOIN common_dictionary d ON w.dictionary_id = d.id
                    LEFT JOIN occurrences o ON w.id = o.word_id
                    WHERE w.surface_form LIKE ? OR w.lemma LIKE ?
                    GROUP BY w.id
                    ORDER BY total_freq DESC, w.surface_form
                    LIMIT 50
                """, (f'%{search_term}%', f'%{search_term}%'))
                
                return cursor.fetchall()
            else:
                # 基础模式
                cursor = conn.execute("""
                    SELECT w.surface_form, w.lemma
                    FROM words w
                    WHERE w.surface_form LIKE ? OR w.lemma LIKE ?
                    ORDER BY w.surface_form
                    LIMIT 50
                """, (f'%{search_term}%', f'%{search_term}%'))
                
                return cursor.fetchall()
    
    # ================= 个人学习状态管理 =================
    
    def set_word_status(self, word: str, status: str) -> bool:
        """设置词汇学习状态"""
        from ..vocabulary.personal_status_manager import PersonalStatusManager
        manager = PersonalStatusManager(self.unified_db.db_path)
        return manager.set_word_status(word, status)
    
    def get_personal_status_stats(self) -> Dict:
        """获取个人学习状态统计"""
        from ..vocabulary.personal_status_manager import PersonalStatusManager
        manager = PersonalStatusManager(self.unified_db.db_path)
        return manager.get_status_statistics()
    
    def get_words_by_status(self, status: str, limit: int = None) -> List[Dict]:
        """获取特定状态的词汇"""
        from ..vocabulary.personal_status_manager import PersonalStatusManager
        manager = PersonalStatusManager(self.unified_db.db_path)
        return manager.get_words_by_status(status, limit)
    
    def analyze_document_difficulty(self, doc_id: str) -> Dict:
        """分析文档难度"""
        from ..vocabulary.personal_status_manager import PersonalStatusManager
        manager = PersonalStatusManager(self.unified_db.db_path)
        return manager.analyze_document_difficulty(doc_id)
    
    # ================= 字典管理 =================
    
    def import_dictionary(self, file_path: str, max_words: int = None) -> Dict:
        """导入字典数据"""
        from .dictionary_manager import DictionaryManager
        manager = DictionaryManager(self.unified_db.db_path)
        return manager.import_coca_dictionary(file_path, max_words)
    
    def get_dictionary_stats(self) -> Dict:
        """获取字典统计信息"""
        from .dictionary_manager import DictionaryManager
        manager = DictionaryManager(self.unified_db.db_path)
        return manager.get_dictionary_stats()
    
    def query_dictionary_word(self, word: str) -> List[Dict]:
        """查询字典词汇"""
        from .dictionary_manager import DictionaryManager
        manager = DictionaryManager(self.unified_db.db_path)
        return manager.query_word(word)
    
    def update_words_dictionary_mapping(self):
        """更新词汇的字典映射"""
        from .dictionary_manager import DictionaryManager
        manager = DictionaryManager(self.unified_db.db_path)
        return manager.update_words_dictionary_mapping()
    
    # ================= 系统信息 =================
    
    def get_database_info(self) -> Dict:
        """获取数据库统计信息"""
        return self.unified_db.get_database_stats()

# 全局适配器实例
unified_adapter = UnifiedDatabaseAdapter() 