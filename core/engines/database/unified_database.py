# 统一数据库操作类
# 路径: core/engines/unified_database.py  
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

import uuid
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import re

# 词汇处理改进 - 添加NLTK支持
try:
    import nltk
    from nltk.stem import PorterStemmer
    
    # 确保必要数据可用
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("📥 首次使用，正在下载NLTK数据包...")
        nltk.download('punkt', quiet=True)
    
    # 创建全局stemmer实例
    stemmer = PorterStemmer()
    NLTK_AVAILABLE = True
    print("✅ NLTK词干提取器已加载")
    
except ImportError:
    stemmer = None
    NLTK_AVAILABLE = False
    print("⚠️  NLTK未安装，使用简单词汇标准化")

from core.models.schema import ModernSchema

class UnifiedDatabase:
    """统一的数据库操作类 - 实现现代化架构"""
    
    def __init__(self, db_path: str = "data/databases/unified.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 确保数据库架构存在
        schema = ModernSchema(db_path)
        schema.create_tables()
        schema.create_views()
    
    def _generate_uuid(self) -> str:
        """生成UUID字符串"""
        return str(uuid.uuid4())
    
    def _calculate_content_hash(self, content: str) -> str:
        """计算内容的SHA256哈希"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    # =================== 文档管理 ===================
    
    def add_document(self, filename: str, content: str, file_path: str = None, 
                    document_type: str = 'text', metadata: Dict = None) -> str:
        """添加文档到数据库"""
        doc_id = self._generate_uuid()
        content_hash = self._calculate_content_hash(content)
        
        # 检查是否已存在相同内容的文档
        existing_doc = self.get_document_by_hash(content_hash)
        if existing_doc:
            print(f"文档已存在: {existing_doc['filename']}")
            return existing_doc['id']
        
        doc_metadata = metadata or {}
        doc_metadata.update({
            'file_size': len(content.encode('utf-8')),
            'word_count': len(content.split()) if document_type == 'text' else 0
        })
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO documents 
                (id, filename, file_path, content_hash, file_size, status, 
                 document_type, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (doc_id, filename, file_path, content_hash, len(content.encode('utf-8')),
                  'pending', document_type, json.dumps(doc_metadata)))
        
        print(f"✅ 文档已添加: {filename} (ID: {doc_id[:8]}...)")
        return doc_id
    
    def update_document_status(self, doc_id: str, status: str, metadata: Dict = None):
        """更新文档状态和元数据"""
        with sqlite3.connect(self.db_path) as conn:
            if metadata:
                conn.execute("""
                    UPDATE documents 
                    SET status = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP,
                        processed_at = CASE WHEN ? = 'completed' THEN CURRENT_TIMESTAMP ELSE processed_at END
                    WHERE id = ?
                """, (status, json.dumps(metadata), status, doc_id))
            else:
                conn.execute("""
                    UPDATE documents 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP,
                        processed_at = CASE WHEN ? = 'completed' THEN CURRENT_TIMESTAMP ELSE processed_at END  
                    WHERE id = ?
                """, (status, status, doc_id))
    
    def get_document_by_hash(self, content_hash: str) -> Optional[Dict]:
        """根据内容哈希获取文档"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM documents WHERE content_hash = ?
            """, (content_hash,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
        return None
    
    def get_all_documents(self, document_type: str = None) -> List[Dict]:
        """获取所有文档"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if document_type:
                cursor = conn.execute("""
                    SELECT * FROM documents WHERE document_type = ? 
                    ORDER BY created_at DESC
                """, (document_type,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM documents ORDER BY created_at DESC
                """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    # =================== 词汇管理 ===================
    
    def add_or_get_word(self, surface_form: str, lemma: str = None, 
                       linguistic_features: Dict = None) -> str:
        """添加词汇或获取已存在词汇的ID - 改进版词汇去重"""
        
        # 改进的词根处理逻辑
        if not lemma:
            lemma = self._get_word_lemma(surface_form)
        
        normalized_form = self._normalize_word(surface_form)
        
        with sqlite3.connect(self.db_path) as conn:
            # 首先尝试基于lemma查找（主要去重逻辑）
            cursor = conn.execute("""
                SELECT id FROM words WHERE lemma = ?
            """, (lemma,))
            
            row = cursor.fetchone()
            if row:
                # 找到相同词根的词汇，更新surface_form（如果更标准）
                word_id = row[0]
                self._update_word_surface_form(conn, word_id, surface_form, lemma)
                return word_id
            
            # 创建新词汇记录
            word_id = self._generate_uuid()
            features = json.dumps(linguistic_features) if linguistic_features else None
            
            conn.execute("""
                INSERT INTO words 
                (id, surface_form, lemma, normalized_form, linguistic_features)
                VALUES (?, ?, ?, ?, ?)
            """, (word_id, surface_form, lemma, normalized_form, features))
            
            return word_id
    
    def _get_word_lemma(self, word: str) -> str:
        """获取词汇的词根形式 - 使用NLTK改进"""
        word_clean = re.sub(r'[^\w]', '', word.lower())
        
        if NLTK_AVAILABLE and stemmer:
            # 使用NLTK Porter Stemmer
            try:
                lemma = stemmer.stem(word_clean)
                
                # 处理一些常见的过度词干化问题
                corrections = {
                    'studi': 'study',
                    'fli': 'fly', 
                    'happi': 'happy',
                    'univers': 'university'
                }
                
                lemma = corrections.get(lemma, lemma)
                return lemma
                
            except Exception as e:
                print(f"⚠️  NLTK处理失败 {word}: {e}")
                
        # 备用：简单规则化处理
        return self._simple_lemmatize(word_clean)
    
    def _simple_lemmatize(self, word: str) -> str:
        """简单的词汇标准化 - 备用方案"""
        word = word.lower()
        
        # 基本复数处理
        if word.endswith('ies') and len(word) > 4:
            return word[:-3] + 'y'  # flies → fly
        elif word.endswith('es') and len(word) > 3:
            return word[:-2]  # boxes → box
        elif word.endswith('s') and len(word) > 2 and not word.endswith('ss'):
            return word[:-1]  # cats → cat
        
        # 基本动词处理
        if word.endswith('ing') and len(word) > 4:
            base = word[:-3]
            # 处理双写字母: running → run
            if len(base) > 2 and base[-1] == base[-2] and base[-1] in 'bdfglmnprt':
                return base[:-1]
            return base
        
        elif word.endswith('ed') and len(word) > 3:
            return word[:-2]
        
        return word
    
    def _update_word_surface_form(self, conn, word_id: str, new_surface: str, lemma: str):
        """更新词汇的表面形式（选择更标准的形式）"""
        try:
            # 获取当前的surface_form
            cursor = conn.execute("SELECT surface_form FROM words WHERE id = ?", (word_id,))
            current_surface = cursor.fetchone()[0]
            
            # 选择更标准的形式（优先小写、更短的形式）
            if (new_surface.lower() == lemma and 
                current_surface.lower() != lemma and 
                len(new_surface) <= len(current_surface)):
                
                conn.execute("""
                    UPDATE words SET surface_form = ? WHERE id = ?
                """, (new_surface, word_id))
                
        except Exception as e:
            # 更新失败不影响主流程
            pass
    
    def _normalize_word(self, word: str) -> str:
        """标准化词汇处理"""
        # 转小写，移除标点
        normalized = re.sub(r'[^\w]', '', word.lower())
        return normalized
    
    def batch_add_words(self, words: List[str]) -> Dict[str, str]:
        """批量添加词汇，返回词汇到ID的映射"""
        word_ids = {}
        with sqlite3.connect(self.db_path) as conn:
            for word in words:
                word_id = self.add_or_get_word(word)
                word_ids[word] = word_id
        return word_ids
    
    # =================== 词频管理 ===================
    
    def store_word_frequencies(self, doc_id: str, word_frequencies: Dict[str, int], 
                              word_positions: Dict[str, List[int]] = None, 
                              context_text: str = None):
        """存储文档的词频数据 - 精细化版本，保留原始词汇形式"""
        if not word_frequencies:
            return
        
        # 批量获取词汇ID - 为每个原始词汇形式创建独立记录
        word_ids = self.batch_add_words_detailed(list(word_frequencies.keys()), context_text)
        
        # 计算总词数用于TF计算
        total_words = sum(word_frequencies.values())
        
        with sqlite3.connect(self.db_path) as conn:
            # 清除可能存在的旧数据
            conn.execute("DELETE FROM occurrences WHERE document_id = ?", (doc_id,))
            
            # 为每个原始词汇形式创建独立的词频记录
            occurrence_data = []
            for word, frequency in word_frequencies.items():
                word_id = word_ids[word]
                tf_score = frequency / total_words  # 计算TF分数
                
                # 处理位置信息
                positions = word_positions.get(word, []) if word_positions else []
                positions = sorted(list(set(positions))) if positions else []
                positions_json = json.dumps(positions) if positions else None
                first_pos = min(positions) if positions else None
                last_pos = max(positions) if positions else None
                
                occurrence_data.append((
                    doc_id, word_id, frequency, tf_score, 
                    positions_json, first_pos, last_pos
                ))
            
            conn.executemany("""
                INSERT INTO occurrences 
                (document_id, word_id, frequency, tf_score, positions, first_position, last_position)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, occurrence_data)
        
        print(f"✅ 存储了 {len(word_frequencies)} 个原始词汇的频率数据")
        
    def batch_add_words_detailed(self, words: List[str], context_text: str = None) -> Dict[str, str]:
        """批量添加词汇，为每个原始形式创建独立记录"""
        word_ids = {}
        with sqlite3.connect(self.db_path) as conn:
            for word in words:
                # 为每个原始词汇形式创建独立的word_id，传递上下文
                word_id = self.add_or_get_word_detailed(word, context_text)
                word_ids[word] = word_id
        return word_ids
    
    def add_or_get_word_detailed(self, surface_form: str, context_text: str = None) -> str:
        """添加或获取词汇，为每个原始形式创建独立记录，包含语言学分析"""
        normalized = self._normalize_word(surface_form)
        lemma = self._get_word_lemma(normalized)
        
        with sqlite3.connect(self.db_path) as conn:
            # 检查是否已存在完全相同的surface_form
            cursor = conn.execute("""
                SELECT id FROM words WHERE surface_form = ? AND lemma = ?
            """, (surface_form, lemma))
            
            existing = cursor.fetchone()
            if existing:
                return existing[0]
            
            # 进行语言学分析
            linguistic_features = self._analyze_linguistic_features(surface_form, context_text)
            
            # 创建新的词汇记录
            word_id = self._generate_uuid()
            conn.execute("""
                INSERT INTO words (id, surface_form, lemma, normalized_form, linguistic_features)
                VALUES (?, ?, ?, ?, ?)
            """, (word_id, surface_form, lemma, normalized, 
                  json.dumps(linguistic_features) if linguistic_features else None))
            
            return word_id
    
    def _analyze_linguistic_features(self, word: str, context_text: str = None) -> dict:
        """分析词汇的语言学特征"""
        try:
            from .linguistic_analyzer import linguistic_analyzer
            
            # 如果有上下文，提取相关词汇作为上下文
            context_words = None
            if context_text:
                # 简单的上下文提取 - 可以根据需要优化
                import re
                words_in_context = re.findall(r'\b\w+\b', context_text.lower())
                # 找到目标词汇周围的词汇
                try:
                    word_index = words_in_context.index(word.lower())
                    start = max(0, word_index - 3)
                    end = min(len(words_in_context), word_index + 4)
                    context_words = words_in_context[start:end]
                except ValueError:
                    # 词汇不在上下文中，使用整个上下文的前几个词
                    context_words = words_in_context[:7]
            
            features = linguistic_analyzer.analyze_word(word, context_words)
            return features
            
        except ImportError:
            print(f"⚠️  语言学分析器不可用，跳过词汇 {word} 的分析")
            return {}
        except Exception as e:
            print(f"⚠️  语言学分析失败 {word}: {e}")
            return {}
    
    # =================== 语言学特征查询 ===================
    
    def get_word_linguistic_features(self, word: str) -> List[Dict]:
        """获取词汇的语言学特征"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT surface_form, lemma, linguistic_features
                FROM words 
                WHERE surface_form = ? OR lemma = ?
                ORDER BY surface_form
            """, (word, word))
            
            results = []
            for surface, lemma, features_json in cursor.fetchall():
                features = json.loads(features_json) if features_json else {}
                results.append({
                    'surface_form': surface,
                    'lemma': lemma,
                    'linguistic_features': features
                })
            
            return results
    
    def get_words_by_pos_type(self, pos_type: str, limit: int = 50) -> List[Dict]:
        """根据词性类型查询词汇"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT w.surface_form, w.lemma, w.linguistic_features,
                       COUNT(o.frequency) as document_count,
                       SUM(o.frequency) as total_frequency
                FROM words w
                LEFT JOIN occurrences o ON w.id = o.word_id
                WHERE w.linguistic_features IS NOT NULL
                  AND JSON_EXTRACT(w.linguistic_features, '$.pos_type') = ?
                GROUP BY w.id
                ORDER BY total_frequency DESC
                LIMIT ?
            """, (pos_type, limit))
            
            results = []
            for surface, lemma, features_json, doc_count, total_freq in cursor.fetchall():
                features = json.loads(features_json) if features_json else {}
                results.append({
                    'surface_form': surface,
                    'lemma': lemma,
                    'linguistic_features': features,
                    'document_count': doc_count or 0,
                    'total_frequency': total_freq or 0
                })
            
            return results
    
    def get_pos_distribution(self) -> Dict:
        """获取词性分布统计"""
        with sqlite3.connect(self.db_path) as conn:
            # 词性类型分布
            cursor = conn.execute("""
                SELECT JSON_EXTRACT(linguistic_features, '$.pos_type') as pos_type,
                       COUNT(*) as count
                FROM words 
                WHERE linguistic_features IS NOT NULL
                GROUP BY pos_type
                ORDER BY count DESC
            """)
            
            pos_type_distribution = dict(cursor.fetchall())
            
            # 详细词性标签分布
            cursor = conn.execute("""
                SELECT JSON_EXTRACT(linguistic_features, '$.pos_tag') as pos_tag,
                       JSON_EXTRACT(linguistic_features, '$.pos_description') as description,
                       COUNT(*) as count
                FROM words 
                WHERE linguistic_features IS NOT NULL
                GROUP BY pos_tag
                ORDER BY count DESC
                LIMIT 20
            """)
            
            pos_tag_distribution = []
            for pos_tag, description, count in cursor.fetchall():
                pos_tag_distribution.append({
                    'pos_tag': pos_tag,
                    'description': description,
                    'count': count
                })
            
            # 形态学复杂度分布
            cursor = conn.execute("""
                SELECT JSON_EXTRACT(linguistic_features, '$.morphology.complexity') as complexity,
                       COUNT(*) as count
                FROM words 
                WHERE linguistic_features IS NOT NULL
                  AND JSON_EXTRACT(linguistic_features, '$.morphology') IS NOT NULL
                GROUP BY complexity
                ORDER BY count DESC
            """)
            
            morphology_distribution = dict(cursor.fetchall())
            
            return {
                'pos_type_distribution': pos_type_distribution,
                'pos_tag_distribution': pos_tag_distribution,
                'morphology_distribution': morphology_distribution,
                'total_analyzed_words': sum(pos_type_distribution.values())
            }
    
    def get_complex_words_analysis(self) -> Dict:
        """分析词汇的复杂度"""
        with sqlite3.connect(self.db_path) as conn:
            # 有前缀的词汇
            cursor = conn.execute("""
                SELECT w.surface_form, w.lemma,
                       JSON_EXTRACT(w.linguistic_features, '$.morphology.prefix') as prefix,
                       SUM(o.frequency) as total_frequency
                FROM words w
                LEFT JOIN occurrences o ON w.id = o.word_id
                WHERE w.linguistic_features IS NOT NULL
                  AND JSON_EXTRACT(w.linguistic_features, '$.morphology.prefix') IS NOT NULL
                GROUP BY w.id
                ORDER BY total_frequency DESC
                LIMIT 20
            """)
            
            prefixed_words = []
            for surface, lemma, prefix, freq in cursor.fetchall():
                prefixed_words.append({
                    'surface_form': surface,
                    'lemma': lemma,
                    'prefix': prefix,
                    'total_frequency': freq or 0
                })
            
            # 有后缀的词汇
            cursor = conn.execute("""
                SELECT w.surface_form, w.lemma,
                       JSON_EXTRACT(w.linguistic_features, '$.morphology.suffix') as suffix,
                       JSON_EXTRACT(w.linguistic_features, '$.morphology.suffix_meaning') as suffix_meaning,
                       SUM(o.frequency) as total_frequency
                FROM words w
                LEFT JOIN occurrences o ON w.id = o.word_id
                WHERE w.linguistic_features IS NOT NULL
                  AND JSON_EXTRACT(w.linguistic_features, '$.morphology.suffix') IS NOT NULL
                GROUP BY w.id
                ORDER BY total_frequency DESC
                LIMIT 20
            """)
            
            suffixed_words = []
            for surface, lemma, suffix, suffix_meaning, freq in cursor.fetchall():
                suffixed_words.append({
                    'surface_form': surface,
                    'lemma': lemma,
                    'suffix': suffix,
                    'suffix_meaning': suffix_meaning,
                    'total_frequency': freq or 0
                })
            
            return {
                'prefixed_words': prefixed_words,
                'suffixed_words': suffixed_words
            }

    # =================== 精细化词汇查询 ===================
    
    def get_word_variants_with_frequencies(self, word: str, doc_id: str = None) -> Dict:
        """获取指定词汇的所有变形及其频率信息"""
        lemma = self._get_word_lemma(word)
        
        with sqlite3.connect(self.db_path) as conn:
            if doc_id:
                # 查询特定文档中的词汇变形
                cursor = conn.execute("""
                    SELECT w.surface_form, w.lemma, o.frequency, o.tf_score, d.filename
                    FROM words w
                    JOIN occurrences o ON w.id = o.word_id
                    JOIN documents d ON o.document_id = d.id
                    WHERE w.lemma = ? AND o.document_id = ?
                    ORDER BY o.frequency DESC
                """, (lemma, doc_id))
            else:
                # 查询所有文档中的词汇变形
                cursor = conn.execute("""
                    SELECT w.surface_form, w.lemma, 
                           SUM(o.frequency) as total_frequency,
                           COUNT(DISTINCT o.document_id) as document_count,
                           AVG(o.frequency) as avg_frequency
                    FROM words w
                    JOIN occurrences o ON w.id = o.word_id
                    WHERE w.lemma = ?
                    GROUP BY w.surface_form
                    ORDER BY total_frequency DESC
                """, (lemma,))
            
            variants = [dict(zip([col[0] for col in cursor.description], row)) 
                       for row in cursor.fetchall()]
            
            return {
                'search_word': word,
                'lemma': lemma,
                'variants': variants,
                'total_variants': len(variants),
                'total_frequency': sum(v.get('total_frequency', v.get('frequency', 0)) for v in variants)
            }
    
    def get_unique_lemma_count(self) -> Dict:
        """获取独特词根数量统计"""
        with sqlite3.connect(self.db_path) as conn:
            # 统计独特词根数量
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT lemma) as unique_lemmas
                FROM words
            """)
            unique_lemmas = cursor.fetchone()[0]
            
            # 统计原始词汇形式数量
            cursor = conn.execute("""
                SELECT COUNT(*) as total_surface_forms
                FROM words
            """)
            total_surface_forms = cursor.fetchone()[0]
            
            # 统计平均每个词根有多少变形
            cursor = conn.execute("""
                SELECT lemma, COUNT(*) as variant_count
                FROM words
                GROUP BY lemma
                ORDER BY variant_count DESC
                LIMIT 10
            """)
            top_varied_lemmas = cursor.fetchall()
            
            return {
                'unique_lemmas': unique_lemmas,
                'total_surface_forms': total_surface_forms,
                'avg_variants_per_lemma': total_surface_forms / unique_lemmas if unique_lemmas > 0 else 0,
                'most_varied_lemmas': [{'lemma': lemma, 'variant_count': count} 
                                     for lemma, count in top_varied_lemmas]
            }
    
    def get_lemma_analysis(self, doc_id: str = None) -> Dict:
        """获取词根级别的分析，支持按文档筛选"""
        with sqlite3.connect(self.db_path) as conn:
            if doc_id:
                # 特定文档的词根分析
                cursor = conn.execute("""
                    SELECT 
                        w.lemma,
                        COUNT(DISTINCT w.surface_form) as variant_count,
                        SUM(o.frequency) as total_frequency,
                        GROUP_CONCAT(w.surface_form || ':' || o.frequency) as variants_detail
                    FROM words w
                    JOIN occurrences o ON w.id = o.word_id
                    WHERE o.document_id = ?
                    GROUP BY w.lemma
                    ORDER BY total_frequency DESC
                """, (doc_id,))
            else:
                # 全局词根分析
                cursor = conn.execute("""
                    SELECT 
                        w.lemma,
                        COUNT(DISTINCT w.surface_form) as variant_count,
                        SUM(o.frequency) as total_frequency,
                        COUNT(DISTINCT o.document_id) as document_count
                    FROM words w
                    JOIN occurrences o ON w.id = o.word_id
                    GROUP BY w.lemma
                    ORDER BY total_frequency DESC
                """)
            
            lemmas = [dict(zip([col[0] for col in cursor.description], row)) 
                     for row in cursor.fetchall()]
            
            return {
                'document_id': doc_id,
                'total_lemmas': len(lemmas),
                'lemma_analysis': lemmas
            }

    # =================== 词汇表管理 ===================
    
    def create_wordlist(self, name: str, description: str = None, 
                       source_file: str = None, metadata: Dict = None) -> str:
        """创建词汇表"""
        wordlist_id = self._generate_uuid()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO wordlists (id, name, description, source_file, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (wordlist_id, name, description, source_file, 
                  json.dumps(metadata) if metadata else None))
        
        print(f"✅ 创建词汇表: {name} (ID: {wordlist_id[:8]}...)")
        return wordlist_id
    
    def add_words_to_wordlist(self, wordlist_id: str, words: List[str], 
                            confidence: float = 1.0) -> Dict[str, int]:
        """将词汇批量添加到词汇表，返回详细统计"""
        word_ids = self.batch_add_words(words)
        
        with sqlite3.connect(self.db_path) as conn:
            # 检查现有关联
            existing_memberships = set()
            if word_ids:
                placeholders = ','.join(['?' for _ in word_ids.values()])
                cursor = conn.execute(f"""
                    SELECT word_id FROM word_wordlist_memberships 
                    WHERE wordlist_id = ? AND word_id IN ({placeholders})
                """, [wordlist_id] + list(word_ids.values()))
                existing_memberships = {row[0] for row in cursor.fetchall()}
            
            # 准备插入数据 - 去重word_ids
            unique_word_ids = list(set(word_ids.values()))
            membership_data = []
            new_associations = 0
            existing_associations = 0
            
            for word_id in unique_word_ids:
                if word_id in existing_memberships:
                    existing_associations += 1
                else:
                    membership_data.append((word_id, wordlist_id, confidence))
                    new_associations += 1
            
            # 插入新关联
            if membership_data:
                conn.executemany("""
                    INSERT INTO word_wordlist_memberships 
                    (word_id, wordlist_id, confidence)
                    VALUES (?, ?, ?)
                """, membership_data)
            
            # 更新词汇表的词汇数量
            conn.execute("""
                UPDATE wordlists 
                SET word_count = (
                    SELECT COUNT(*) FROM word_wordlist_memberships 
                    WHERE wordlist_id = ?
                )
                WHERE id = ?
            """, (wordlist_id, wordlist_id))
        
        print(f"✅ 添加了 {new_associations} 个词汇到词汇表")
        if existing_associations > 0:
            print(f"📋 跳过了 {existing_associations} 个已存在的词汇")
        
        # 计算基于原始词汇的统计
        total_input_words = len(words)
        unique_word_count = len(unique_word_ids)
        
        # 由于词汇去重合并，需要调整统计方式
        # 如果有词汇合并，existing_associations应该按比例调整
        if unique_word_count < total_input_words:
            # 有词汇被合并了，按比例分配
            ratio = total_input_words / unique_word_count if unique_word_count > 0 else 1
            adjusted_new = int(new_associations * ratio)
            adjusted_existing = total_input_words - adjusted_new
        else:
            adjusted_new = new_associations
            adjusted_existing = existing_associations
        
        return {
            'total_words': total_input_words,
            'new_associations': adjusted_new,
            'existing_associations': adjusted_existing,
            'unique_word_ids': unique_word_count,
            'success': True
        }
    
    def get_wordlist_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取词汇表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM wordlists WHERE name = ?
            """, (name,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
        return None
    
    # =================== 分析查询 ===================
    
    def get_vocabulary_coverage(self, doc_id: str) -> List[Dict]:
        """获取文档的词汇覆盖度分析"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM document_vocabulary_coverage 
                WHERE document_id = ?
                ORDER BY covered_words DESC
            """, (doc_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_word_usage_stats(self, min_frequency: int = 1) -> List[Dict]:
        """获取词汇使用统计"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM word_usage_stats 
                WHERE total_frequency >= ?
                ORDER BY total_frequency DESC
            """, (min_frequency,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def analyze_document_similarity(self, doc_id1: str, doc_id2: str) -> Dict:
        """分析两个文档的相似度"""
        # 获取两个文档的词汇集合
        with sqlite3.connect(self.db_path) as conn:
            # 文档1的词汇
            cursor1 = conn.execute("""
                SELECT w.lemma, o.tf_score
                FROM occurrences o
                JOIN words w ON o.word_id = w.id
                WHERE o.document_id = ?
            """, (doc_id1,))
            doc1_words = {row[0]: row[1] for row in cursor1.fetchall()}
            
            # 文档2的词汇  
            cursor2 = conn.execute("""
                SELECT w.lemma, o.tf_score
                FROM occurrences o
                JOIN words w ON o.word_id = w.id
                WHERE o.document_id = ?
            """, (doc_id2,))
            doc2_words = {row[0]: row[1] for row in cursor2.fetchall()}
        
        # 计算Jaccard相似度
        common_words = set(doc1_words.keys()) & set(doc2_words.keys())
        all_words = set(doc1_words.keys()) | set(doc2_words.keys())
        
        jaccard_similarity = len(common_words) / len(all_words) if all_words else 0
        
        # 计算余弦相似度
        cosine_similarity = self._calculate_cosine_similarity(doc1_words, doc2_words)
        
        return {
            'document1_id': doc_id1,
            'document2_id': doc_id2,
            'jaccard_similarity': jaccard_similarity,
            'cosine_similarity': cosine_similarity,
            'common_words_count': len(common_words),
            'total_unique_words': len(all_words)
        }
    
    def _calculate_cosine_similarity(self, doc1_words: Dict, doc2_words: Dict) -> float:
        """计算余弦相似度"""
        import math
        
        # 获取所有词汇
        all_words = set(doc1_words.keys()) | set(doc2_words.keys())
        
        # 构建向量
        vec1 = [doc1_words.get(word, 0) for word in all_words]
        vec2 = [doc2_words.get(word, 0) for word in all_words]
        
        # 计算点积
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # 计算向量长度
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        # 避免除零
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    # =================== 工具方法 ===================
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # 基本计数
            tables = ['documents', 'words', 'wordlists', 'occurrences', 'word_wordlist_memberships']
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # 按状态统计文档
            cursor = conn.execute("""
                SELECT status, COUNT(*) FROM documents GROUP BY status
            """)
            stats['documents_by_status'] = dict(cursor.fetchall())
            
            # 按类型统计文档
            cursor = conn.execute("""
                SELECT document_type, COUNT(*) FROM documents GROUP BY document_type  
            """)
            stats['documents_by_type'] = dict(cursor.fetchall())
            
            return stats
    
    def cleanup_expired_cache(self):
        """清理过期的分析结果缓存"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM analysis_results 
                WHERE expires_at < CURRENT_TIMESTAMP
            """)
            deleted_count = cursor.rowcount
            
        if deleted_count > 0:
            print(f"🧹 清理了 {deleted_count} 个过期缓存")
        
        return deleted_count
    
    def delete_document(self, doc_id: str) -> bool:
        """删除单个文档及其相关数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 外键约束会自动级联删除相关记录
                cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                deleted = cursor.rowcount > 0
                
                if deleted:
                    print(f"✅ 已删除文档: {doc_id[:8]}...")
                
                return deleted
        except Exception as e:
            print(f"❌ 删除文档失败 {doc_id}: {e}")
            return False
    
    def delete_documents_by_type(self, document_type: str) -> int:
        """按类型批量删除文档"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM documents WHERE document_type = ?
                """, (document_type,))
                deleted_count = cursor.rowcount
                
                if deleted_count > 0:
                    print(f"✅ 删除了 {deleted_count} 个 {document_type} 类型的文档")
                
                return deleted_count
        except Exception as e:
            print(f"❌ 批量删除失败: {e}")
            return 0 