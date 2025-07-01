# 字典管理器 - 系统内置词典管理
# 路径: core/engines/database/dictionary_manager.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

import uuid
import csv
import json
import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DictionaryManager:
    """系统内置字典管理器
    
    负责管理系统内置的权威词典数据，包括：
    - COCA词频表导入和管理
    - WordNet定义数据集成
    - 字典数据的查询和统计
    
    注意：这不是用户输入功能，而是系统维护功能
    """
    
    def __init__(self, db_path: str = "data/databases/unified.db"):
        self.db_path = db_path
        self.wordnet_available = False
        self._init_wordnet()
    
    def _init_wordnet(self):
        """初始化WordNet资源"""
        try:
            import nltk
            from nltk.corpus import wordnet as wn
            self.wn = wn
            self.wordnet_available = True
            logger.info("✅ WordNet已加载，可用于补充定义信息")
        except ImportError:
            logger.warning("⚠️ NLTK/WordNet不可用，将跳过定义补充")
    
    def import_coca_dictionary(self, 
                              coca_file_path: str, 
                              max_words: Optional[int] = None,
                              skip_proper_nouns: bool = True) -> Dict[str, int]:
        """导入COCA词频表作为系统内置词典
        
        Args:
            coca_file_path: COCA词表文件路径
            max_words: 最大导入词汇数（None为全部）
            skip_proper_nouns: 是否跳过专有名词（首字母大写）
            
        Returns:
            导入统计信息
        """
        logger.info(f"🚀 开始导入COCA系统词典: {coca_file_path}")
        
        stats = {
            'total_processed': 0,
            'successfully_imported': 0,
            'skipped_proper_nouns': 0,
            'wordnet_definitions_added': 0,
            'errors': 0
        }
        
        try:
            # 读取COCA文件
            with open(coca_file_path, 'r', encoding='utf-8') as file:
                # 检测是否有表头
                first_line = file.readline().strip()
                file.seek(0)
                
                # 如果第一行包含"RANK"等关键词，跳过表头
                has_header = any(keyword in first_line.upper() 
                               for keyword in ['RANK', 'POS', 'WORD', 'TOTAL'])
                
                reader = csv.reader(file)  # 使用默认逗号分隔符
                if has_header:
                    next(reader)  # 跳过表头
                
                # 批量处理数据
                batch_size = 1000
                batch_data = []
                
                for row in reader:
                    if len(row) < 4:  # 至少需要rank, pos, word_caps, word_lower
                        continue
                    
                    stats['total_processed'] += 1
                    
                    # 限制导入数量
                    if max_words and stats['total_processed'] > max_words:
                        break
                    
                    # 解析数据
                    try:
                        rank = int(row[0])
                        pos = row[1].strip()
                        word_caps = row[2].strip()  # 大写形式
                        word = row[3].strip()       # 小写形式（实际使用）
                        
                        # 跳过无效或专有名词
                        if not word or len(word) < 2:
                            continue
                        
                        # 跳过专有名词（根据需要）
                        if skip_proper_nouns and (word != word.lower() or word.isupper()):
                            stats['skipped_proper_nouns'] += 1
                            continue
                        
                        # 标准化词汇
                        word_normalized = word.lower()
                        
                        # 处理词条
                        word_data = self._process_dictionary_entry(
                            word=word_normalized,
                            rank=rank,
                            pos=pos
                        )
                        
                        if word_data:
                            batch_data.append(word_data)
                            
                            # 批量写入数据库
                            if len(batch_data) >= batch_size:
                                self._batch_insert_dictionary(batch_data)
                                stats['successfully_imported'] += len(batch_data)
                                batch_data = []
                                
                                # 进度报告
                                if stats['successfully_imported'] % 5000 == 0:
                                    logger.info(f"📊 已导入 {stats['successfully_imported']} 个词汇...")
                    
                    except (ValueError, IndexError) as e:
                        stats['errors'] += 1
                        logger.warning(f"❌ 处理行时出错: {row[:3]} - {e}")
                
                # 写入剩余数据
                if batch_data:
                    self._batch_insert_dictionary(batch_data)
                    stats['successfully_imported'] += len(batch_data)
        
        except FileNotFoundError:
            logger.error(f"❌ 文件未找到: {coca_file_path}")
            stats['errors'] += 1
        except Exception as e:
            logger.error(f"❌ 导入过程出错: {e}")
            stats['errors'] += 1
        
        # 输出统计信息
        self._print_import_stats(stats)
        return stats
    
    def _process_dictionary_entry(self, word: str, rank: int, pos: str) -> Optional[Dict]:
        """处理单个词典条目，补充定义等信息"""
        
        # POS标准化映射
        pos_mapping = {
            'N': 'noun', 'V': 'verb', 'A': 'adjective', 'R': 'adverb',
            'n': 'noun', 'v': 'verb', 'a': 'adjective', 'r': 'adverb',
            'ADJ': 'adjective', 'ADV': 'adverb', 'NOUN': 'noun', 'VERB': 'verb'
        }
        
        pos_standardized = pos_mapping.get(pos, pos.lower())
        
        # 基础词条数据
        word_data = {
            'id': str(uuid.uuid4()),
            'word': word,
            'lemma': word,  # 暂时设为同word，后续可以用lemmatizer优化
            'pos_primary': pos_standardized,
            'frequency_rank': rank,
            'source_data': {
                'coca_pos': pos,
                'coca_rank': rank
            }
        }
        
        # 补充WordNet定义（如果可用）
        if self.wordnet_available:
            definition = self._get_wordnet_definition(word, pos_standardized)
            if definition:
                word_data['definition'] = definition
                word_data['source_data']['wordnet_found'] = True
        
        # 计算难度等级（基于词频排名）
        word_data['difficulty_level'] = self._calculate_difficulty_level(rank)
        
        return word_data
    
    def _get_wordnet_definition(self, word: str, pos: str) -> Optional[str]:
        """从WordNet获取词汇定义"""
        if not self.wordnet_available:
            return None
        
        # POS转换为WordNet格式
        pos_map = {
            'noun': 'n',
            'verb': 'v', 
            'adjective': 'a',
            'adverb': 'r'
        }
        
        wn_pos = pos_map.get(pos)
        if not wn_pos:
            return None
        
        try:
            synsets = self.wn.synsets(word, pos=wn_pos)
            if synsets:
                # 取第一个同义词集的定义
                return synsets[0].definition()
        except Exception:
            pass
        
        return None
    
    def _calculate_difficulty_level(self, rank: int) -> int:
        """基于词频排名计算难度等级 (1-5)"""
        if rank <= 2000:           # 最常用2000词
            return 1
        elif rank <= 5000:         # 常用5000词  
            return 2
        elif rank <= 15000:        # 中等15000词
            return 3
        elif rank <= 35000:        # 较难35000词
            return 4
        else:                      # 高难度词汇
            return 5
    
    def _batch_insert_dictionary(self, batch_data: List[Dict]):
        """批量插入字典数据到数据库，支持多词性独立词条"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("BEGIN TRANSACTION")
                
                for word_data in batch_data:
                    word = word_data['word']
                    pos = word_data['pos_primary']
                    new_rank = word_data['frequency_rank']
                    
                    # 检查是否已存在该词汇+词性组合
                    existing = conn.execute("""
                        SELECT frequency_rank, id FROM common_dictionary 
                        WHERE word = ? AND pos_primary = ?
                    """, (word, pos)).fetchone()
                    
                    if existing:
                        existing_rank, existing_id = existing
                        
                        # 只有新词汇的排名更高（数字更小）时才替换
                        if new_rank < existing_rank:
                            # 保留原ID，更新其他字段
                            conn.execute("""
                                UPDATE common_dictionary 
                                SET lemma = ?, pos_primary = ?, definition = ?, frequency_rank = ?, 
                                    difficulty_level = ?, source_data = ?, created_at = ?
                                WHERE id = ?
                            """, (
                                word_data['lemma'],
                                word_data['pos_primary'],
                                word_data.get('definition'),
                                word_data['frequency_rank'],
                                word_data['difficulty_level'],
                                json.dumps(word_data['source_data']),
                                datetime.now().isoformat(),
                                existing_id
                            ))
                        # 如果新词汇排名更低，跳过插入（保留现有的高频版本）
                    else:
                        # 新词汇，直接插入
                        conn.execute("""
                            INSERT INTO common_dictionary 
                            (id, word, lemma, pos_primary, definition, frequency_rank, 
                             difficulty_level, source_data, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            word_data['id'],
                            word_data['word'],
                            word_data['lemma'],
                            word_data['pos_primary'],
                            word_data.get('definition'),
                            word_data['frequency_rank'],
                            word_data['difficulty_level'],
                            json.dumps(word_data['source_data']),
                            datetime.now().isoformat()
                        ))
                
                conn.execute("COMMIT")
                
        except Exception as e:
            logger.error(f"❌ 批量插入失败: {e}")
            raise
    
    def _print_import_stats(self, stats: Dict[str, int]):
        """打印导入统计信息"""
        logger.info("=" * 50)
        logger.info("📊 系统词典导入完成统计:")
        logger.info(f"   📝 总处理词汇: {stats['total_processed']}")
        logger.info(f"   ✅ 成功导入: {stats['successfully_imported']}")
        logger.info(f"   🚫 跳过专有名词: {stats['skipped_proper_nouns']}")
        logger.info(f"   📖 WordNet定义补充: {stats['wordnet_definitions_added']}")
        logger.info(f"   ❌ 处理错误: {stats['errors']}")
        logger.info("=" * 50)
    
    def update_words_dictionary_mapping(self):
        """更新words表中的字典映射字段（使用dictionary_id）"""
        logger.info("🔄 开始更新words表的字典映射...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 查询所有需要更新的words
                cursor = conn.execute("""
                    SELECT w.id, w.lemma, w.surface_form
                    FROM words w
                    WHERE w.dictionary_found = FALSE OR w.dictionary_found IS NULL
                """)
                
                updated_count = 0
                
                for word_id, lemma, surface_form in cursor.fetchall():
                    # 先尝试精确匹配lemma
                    dict_match = conn.execute("""
                        SELECT id, lemma, frequency_rank, difficulty_level
                        FROM common_dictionary
                        WHERE word = ? OR lemma = ?
                        ORDER BY frequency_rank ASC
                        LIMIT 1
                    """, (lemma, lemma)).fetchone()
                    
                    # 如果没找到，尝试匹配surface_form
                    if not dict_match:
                        dict_match = conn.execute("""
                            SELECT id, lemma, frequency_rank, difficulty_level
                            FROM common_dictionary
                            WHERE word = ?
                            ORDER BY frequency_rank ASC
                            LIMIT 1
                        """, (surface_form,)).fetchone()
                    
                    # 更新words表（使用dictionary_id）
                    if dict_match:
                        dict_id, dict_lemma, rank, difficulty = dict_match
                        conn.execute("""
                            UPDATE words
                            SET dictionary_id = ?,
                                dictionary_found = TRUE,
                                dictionary_rank = ?,
                                difficulty_level = ?
                            WHERE id = ?
                        """, (dict_id, rank, difficulty, word_id))
                        updated_count += 1
                
                conn.commit()
                logger.info(f"✅ 更新了 {updated_count} 个词汇的字典映射")
                
        except Exception as e:
            logger.error(f"❌ 更新字典映射失败: {e}")
            raise
    
    # =================== 字典查询功能 ===================
    
    def query_word(self, word: str) -> List[Dict]:
        """查询单词在字典中的信息，返回所有词性的版本"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, word, lemma, pos_primary, definition, frequency_rank, 
                           difficulty_level, source_data
                    FROM common_dictionary
                    WHERE word = ? OR lemma = ?
                    ORDER BY frequency_rank ASC
                """, (word.lower(), word.lower()))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row[0],
                        'word': row[1],
                        'lemma': row[2],
                        'pos_primary': row[3],
                        'definition': row[4],
                        'frequency_rank': row[5],
                        'difficulty_level': row[6],
                        'source_data': json.loads(row[7]) if row[7] else {}
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"❌ 查询词汇失败: {e}")
            return []
    
    def get_dictionary_stats(self) -> Dict[str, int]:
        """获取字典统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # 总词汇数
                total = conn.execute("SELECT COUNT(*) FROM common_dictionary").fetchone()[0]
                stats['total_words'] = total
                
                # 按词性统计
                cursor = conn.execute("""
                    SELECT pos_primary, COUNT(*) as count
                    FROM common_dictionary
                    GROUP BY pos_primary
                    ORDER BY count DESC
                """)
                pos_stats = dict(cursor.fetchall())
                stats['pos_distribution'] = pos_stats
                
                # 按难度级别统计
                for level in range(1, 6):
                    count = conn.execute("""
                        SELECT COUNT(*) FROM common_dictionary 
                        WHERE difficulty_level = ?
                    """, (level,)).fetchone()[0]
                    stats[f'difficulty_level_{level}'] = count
                
                # 有定义的词汇数
                with_definition = conn.execute("""
                    SELECT COUNT(*) FROM common_dictionary 
                    WHERE definition IS NOT NULL
                """).fetchone()[0]
                stats['words_with_definition'] = with_definition
                
                # words表匹配情况（通过dictionary_id）
                total_user_words = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
                matched_words = conn.execute("""
                    SELECT COUNT(*) FROM words WHERE dictionary_found = TRUE
                """).fetchone()[0]
                
                stats['total_user_words'] = total_user_words
                stats['matched_user_words'] = matched_words
                stats['match_rate'] = (matched_words / total_user_words * 100) if total_user_words > 0 else 0
                
                # 独特词汇和多词性统计
                unique_words = conn.execute("""
                    SELECT COUNT(DISTINCT word) FROM common_dictionary
                """).fetchone()[0]
                stats['unique_words'] = unique_words
                
                # 多词性词汇统计
                multipos_words = conn.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT word FROM common_dictionary
                        GROUP BY word
                        HAVING COUNT(*) > 1
                    )
                """).fetchone()[0]
                stats['multipos_words'] = multipos_words
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ 获取字典统计失败: {e}")
            return {}
    
    def get_words_by_difficulty(self, difficulty_level: int, limit: int = 50) -> List[Dict]:
        """获取指定难度级别的词汇列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT word, pos_primary, definition, frequency_rank
                    FROM common_dictionary
                    WHERE difficulty_level = ?
                    ORDER BY frequency_rank ASC
                    LIMIT ?
                """, (difficulty_level, limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'word': row[0],
                        'pos_primary': row[1],
                        'definition': row[2],
                        'frequency_rank': row[3]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"❌ 获取难度词汇失败: {e}")
            return []

# 维护性命令行工具（仅供开发/管理员使用）
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="系统字典管理工具（仅供维护使用）")
    parser.add_argument("--import-coca", help="导入COCA词表文件路径")
    parser.add_argument("--max-words", type=int, help="最大导入词汇数")
    parser.add_argument("--db-path", default="data/databases/unified.db", help="数据库路径")
    parser.add_argument("--update-mapping", action="store_true", help="更新words表字典映射")
    parser.add_argument("--stats", action="store_true", help="显示字典统计信息")
    parser.add_argument("--query", help="查询单词信息")
    
    args = parser.parse_args()
    
    manager = DictionaryManager(args.db_path)
    
    if args.import_coca:
        # 导入COCA词表
        stats = manager.import_coca_dictionary(
            coca_file_path=args.import_coca,
            max_words=args.max_words
        )
        
        # 更新映射
        if args.update_mapping:
            manager.update_words_dictionary_mapping()
    
    elif args.stats:
        # 显示统计信息
        stats = manager.get_dictionary_stats()
        print("📖 字典统计信息:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    elif args.query:
        # 查询单词
        result = manager.query_word(args.query)
        if result:
            print(f"📝 词汇信息: {args.query}")
            for key, value in result.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ 未找到词汇: {args.query}")
    
    else:
        parser.print_help() 