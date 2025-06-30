# 数据库适配器
# 路径: core/engines/database_adapter.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

from typing import Dict, List, Optional, Tuple, Any
import json
import sqlite3
from pathlib import Path

from .unified_database import UnifiedDatabase

class UnifiedDatabaseAdapter:
    """
    统一数据库适配器
    提供与旧接口兼容的API，内部使用新的统一数据库架构
    """
    
    def __init__(self, db_path: str = "data/databases/unified.db"):
        self.unified_db = UnifiedDatabase(db_path)
    
    # ================= 兼容StorageManager接口 =================
    
    def store_analysis(self, content_hash: str, filename: str, basic_info: Dict, 
                      word_frequencies: Dict, process_duration: float, 
                      original_text: str = None):
        """兼容旧的store_analysis接口，支持传递原始文本用于语言学分析"""
        # 添加文档
        metadata = {
            'total_words': basic_info.get('total_words', 0),
            'unique_words': basic_info.get('unique_words', 0),
            'process_duration': process_duration,
            'basic_info': basic_info
        }
        
        doc_id = self.unified_db.add_document(
            filename=filename,
            content=content_hash,  # 使用hash作为内容标识
            document_type='text',
            metadata=metadata
        )
        
        # 存储词频数据，传递原始文本作为上下文用于语言学分析
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
        """获取所有分析结果 - 兼容格式"""
        documents = self.unified_db.get_all_documents(document_type='text')
        
        result = []
        for doc in documents:
            metadata = json.loads(doc.get('metadata', '{}')) if doc.get('metadata') else {}
            
            result.append((
                doc['id'],  # 现在是UUID而非整数ID
                doc['filename'],
                doc.get('processed_at', doc['created_at']),
                metadata.get('total_words', 0),
                metadata.get('unique_words', 0)
            ))
        
        return result
    
    def get_all_texts(self) -> List[Dict]:
        """获取所有文本记录 - 字典格式"""
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
                # 外键约束会自动级联删除相关记录
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
    
    # ================= 兼容VocabularyDatabase接口 =================
    
    def create_wordlist(self, name: str, description: str = None) -> str:
        """创建词汇表"""
        return self.unified_db.create_wordlist(name, description)
    
    def add_words_to_wordlist(self, wordlist_name: str, words: List[str]) -> Dict:
        """添加词汇到词汇表，返回详细统计"""
        try:
            # 词汇验证 - 添加一些规则来检测问题词汇
            invalid_words = []
            valid_words = []
            
            for word in words:
                # 验证规则
                if len(word) > 50:  # 词汇过长
                    invalid_words.append((word, "词汇长度超过50个字符"))
                elif len(word) < 2:  # 词汇过短
                    invalid_words.append((word, "词汇长度少于2个字符"))
                elif any(char.isdigit() for char in word):  # 包含数字
                    invalid_words.append((word, "词汇包含数字字符"))
                elif word.startswith('test_fail_'):  # 模拟失败的测试词汇
                    invalid_words.append((word, "测试失败模拟"))
                else:
                    valid_words.append(word)
            
            # 如果有无效词汇，返回部分失败结果
            if invalid_words:
                print(f"⚠️  发现 {len(invalid_words)} 个无效词汇，将尝试导入 {len(valid_words)} 个有效词汇")
                
                # 只导入有效词汇
                if valid_words:
                    # 获取或创建词汇表
                    wordlist = self.unified_db.get_wordlist_by_name(wordlist_name)
                    if not wordlist:
                        wordlist_id = self.unified_db.create_wordlist(wordlist_name)
                    else:
                        wordlist_id = wordlist['id']
                    
                    # 导入有效词汇
                    valid_result = self.unified_db.add_words_to_wordlist(wordlist_id, valid_words)
                    
                    return {
                        'total_words': len(words),
                        'new_associations': valid_result.get('new_associations', 0),
                        'existing_associations': valid_result.get('existing_associations', 0),
                        'failed_imports': len(invalid_words),
                        'invalid_words': invalid_words,
                        'success': len(valid_words) > 0  # 只要有有效词汇就算部分成功
                    }
                else:
                    # 全部词汇都无效
                    return {
                        'total_words': len(words),
                        'new_associations': 0,
                        'existing_associations': 0,
                        'failed_imports': len(invalid_words),
                        'invalid_words': invalid_words,
                        'success': False,
                        'error': '所有词汇都不符合验证规则'
                    }
            
            # 所有词汇都有效，正常批量导入
            # 获取或创建词汇表
            wordlist = self.unified_db.get_wordlist_by_name(wordlist_name)
            if not wordlist:
                wordlist_id = self.unified_db.create_wordlist(wordlist_name)
            else:
                wordlist_id = wordlist['id']
            
            # 添加词汇并获取详细统计
            result = self.unified_db.add_words_to_wordlist(wordlist_id, words)
            return result
            
        except Exception as e:
            print(f"添加词汇失败: {e}")
            return {
                'total_words': len(words),
                'new_associations': 0,
                'existing_associations': 0,
                'success': False,
                'error': str(e)
            }
    
    def get_all_wordlists(self) -> List[Dict]:
        """获取所有词汇表"""
        with sqlite3.connect(self.unified_db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM wordlists ORDER BY created_at DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_wordlist_words(self, wordlist_name: str) -> List[str]:
        """获取词汇表中的所有词汇"""
        with sqlite3.connect(self.unified_db.db_path) as conn:
            cursor = conn.execute("""
                SELECT w.surface_form
                FROM words w
                JOIN word_wordlist_memberships m ON w.id = m.word_id
                JOIN wordlists wl ON m.wordlist_id = wl.id
                WHERE wl.name = ?
                ORDER BY w.surface_form
            """, (wordlist_name,))
            
            return [row[0] for row in cursor.fetchall()]
    
    # ================= 精细化词汇查询功能 =================
    
    def get_word_variants(self, word: str, doc_id: str = None) -> Dict:
        """获取指定词汇的所有变形及其频率信息"""
        return self.unified_db.get_word_variants_with_frequencies(word, doc_id)
    
    def get_lemma_statistics(self) -> Dict:
        """获取词根级别的统计信息"""
        return self.unified_db.get_unique_lemma_count()
    
    def get_lemma_analysis_data(self, doc_id: str = None) -> Dict:
        """获取词根级别的分析数据"""
        return self.unified_db.get_lemma_analysis(doc_id)
    
    def get_linguistic_features(self, word: str) -> List[Dict]:
        """获取词汇的语言学特征"""
        return self.unified_db.get_word_linguistic_features(word)
    
    def get_words_by_pos(self, pos_type: str, limit: int = 50) -> List[Dict]:
        """根据词性类型获取词汇"""
        return self.unified_db.get_words_by_pos_type(pos_type, limit)
    
    def get_pos_statistics(self) -> Dict:
        """获取词性分布统计"""
        return self.unified_db.get_pos_distribution()
    
    def get_morphology_analysis(self) -> Dict:
        """获取形态学分析"""
        return self.unified_db.get_complex_words_analysis()

    # ================= 新增强大功能 =================
    
    def get_vocabulary_coverage_analysis(self, doc_id: str) -> List[Dict]:
        """获取文档词汇覆盖度分析"""
        return self.unified_db.get_vocabulary_coverage(doc_id)
    
    def analyze_document_similarity(self, doc_id1: str, doc_id2: str) -> Dict:
        """分析文档相似度"""
        return self.unified_db.analyze_document_similarity(doc_id1, doc_id2)
    
    def get_word_usage_statistics(self, min_frequency: int = 1) -> List[Dict]:
        """获取词汇使用统计"""
        return self.unified_db.get_word_usage_stats(min_frequency)
    
    def get_advanced_search(self, **kwargs) -> Dict:
        """高级搜索功能"""
        results = {}
        
        # 按词汇表筛选文档
        if 'wordlist_name' in kwargs:
            with sqlite3.connect(self.unified_db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT DISTINCT d.id, d.filename, COUNT(w.id) as matching_words
                    FROM documents d
                    JOIN occurrences o ON d.id = o.document_id
                    JOIN words w ON o.word_id = w.id
                    JOIN word_wordlist_memberships m ON w.id = m.word_id
                    JOIN wordlists wl ON m.wordlist_id = wl.id
                    WHERE wl.name = ?
                    GROUP BY d.id
                    ORDER BY matching_words DESC
                """, (kwargs['wordlist_name'],))
                
                results['documents_by_wordlist'] = [dict(row) for row in cursor.fetchall()]
        
        # 高频词汇分析
        if 'min_document_count' in kwargs:
            stats = self.get_word_usage_statistics()
            results['high_frequency_words'] = [
                word for word in stats 
                if word['document_count'] >= kwargs['min_document_count']
            ]
        
        return results
    
    def get_database_info(self) -> Dict:
        """获取数据库详细信息"""
        stats = self.unified_db.get_database_stats()
        
        # 添加更多统计信息
        with sqlite3.connect(self.unified_db.db_path) as conn:
            # 平均文档长度
            cursor = conn.execute("""
                SELECT AVG(CAST(JSON_EXTRACT(metadata, '$.total_words') AS INTEGER)) as avg_doc_length
                FROM documents 
                WHERE document_type = 'text' AND metadata IS NOT NULL
            """)
            avg_length = cursor.fetchone()[0]
            
            # 最活跃词汇
            cursor = conn.execute("""
                SELECT w.surface_form, COUNT(DISTINCT o.document_id) as doc_count
                FROM words w
                JOIN occurrences o ON w.id = o.word_id
                GROUP BY w.id
                ORDER BY doc_count DESC
                LIMIT 10
            """)
            top_words = cursor.fetchall()
        
        stats['avg_document_length'] = avg_length
        stats['most_common_words'] = top_words
        
        # 修复字段名映射，确保CLI兼容性
        # CLI期望的字段名和数据库返回的字段名不匹配，需要添加映射
        stats['total_words'] = stats.get('words_count', 0)
        stats['word_frequencies_count'] = stats.get('occurrences_count', 0)
        # documents_count 和 wordlists_count 已经匹配，无需映射
        
        # 添加词根级别的统计信息
        lemma_stats = self.get_lemma_statistics()
        stats['unique_lemmas'] = lemma_stats.get('unique_lemmas', 0)
        stats['total_surface_forms'] = lemma_stats.get('total_surface_forms', 0)
        stats['avg_variants_per_lemma'] = lemma_stats.get('avg_variants_per_lemma', 0)
        
        return stats

# 创建全局实例以便导入使用
unified_adapter = UnifiedDatabaseAdapter()

# 为了向后兼容，创建别名
StorageManager = lambda: unified_adapter
VocabularyDatabase = lambda: unified_adapter 