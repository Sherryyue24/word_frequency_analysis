# 个人词汇状态管理器
# 路径: core/engines/vocabulary/personal_status_manager.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

import sqlite3
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PersonalStatusManager:
    """个人词汇学习状态管理器
    
    管理用户对词汇的学习状态：new/learn/know/master
    为文本难度评估和学习进度跟踪提供数据支撑
    """
    
    # 学习状态常量
    STATUS_NEW = 'new'
    STATUS_LEARN = 'learn'
    STATUS_KNOW = 'know'
    STATUS_MASTER = 'master'
    
    VALID_STATUSES = {STATUS_NEW, STATUS_LEARN, STATUS_KNOW, STATUS_MASTER}
    
    def __init__(self, db_path: str = "data/databases/unified.db"):
        self.db_path = db_path
    
    def set_word_status(self, 
                       word_surface_form: str, 
                       status: str, 
                       create_if_missing: bool = True) -> bool:
        """设置单个词汇的学习状态
        
        Args:
            word_surface_form: 词汇的表面形式
            status: 学习状态 (new/learn/know/master)
            create_if_missing: 如果词汇不存在是否创建
            
        Returns:
            是否成功设置状态
        """
        if status not in self.VALID_STATUSES:
            logger.error(f"❌ 无效的学习状态: {status}")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 查找词汇
                word_info = conn.execute("""
                    SELECT id, lemma FROM words
                    WHERE surface_form = ? OR lemma = ?
                    LIMIT 1
                """, (word_surface_form, word_surface_form)).fetchone()
                
                if word_info:
                    word_id, lemma = word_info
                    # 更新现有词汇状态
                    conn.execute("""
                        UPDATE words
                        SET personal_status = ?,
                            status_updated_at = ?
                        WHERE id = ?
                    """, (status, datetime.now().isoformat(), word_id))
                    
                    logger.info(f"✅ 更新词汇状态: {word_surface_form} -> {status}")
                    return True
                
                elif create_if_missing:
                    # 创建新词汇记录
                    from core.engines.vocabulary.word_analyzer import WordAnalyzer
                    analyzer = WordAnalyzer()
                    
                    # 创建基础词汇记录
                    word_id = analyzer.add_or_get_word(
                        surface_form=word_surface_form,
                        lemma=word_surface_form  # 简化处理
                    )
                    
                    if word_id:
                        # 设置状态
                        conn.execute("""
                            UPDATE words
                            SET personal_status = ?,
                                status_updated_at = ?
                            WHERE id = ?
                        """, (status, datetime.now().isoformat(), word_id))
                        
                        logger.info(f"✅ 创建新词汇并设置状态: {word_surface_form} -> {status}")
                        return True
                
                else:
                    logger.warning(f"⚠️ 词汇不存在且未创建: {word_surface_form}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 设置词汇状态失败: {e}")
            return False
    
    def batch_set_status(self, 
                        word_status_pairs: List[Tuple[str, str]]) -> Dict[str, int]:
        """批量设置词汇状态
        
        Args:
            word_status_pairs: [(word, status), ...] 列表
            
        Returns:
            统计结果 {'updated': n, 'created': n, 'failed': n}
        """
        stats = {'updated': 0, 'created': 0, 'failed': 0}
        
        for word, status in word_status_pairs:
            if self.set_word_status(word, status):
                stats['updated'] += 1
            else:
                stats['failed'] += 1
        
        logger.info(f"📊 批量状态设置完成: {stats}")
        return stats
    
    def get_word_status(self, word_surface_form: str) -> Optional[str]:
        """获取词汇的当前学习状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute("""
                    SELECT personal_status FROM words
                    WHERE surface_form = ? OR lemma = ?
                    LIMIT 1
                """, (word_surface_form, word_surface_form)).fetchone()
                
                return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ 获取词汇状态失败: {e}")
            return None
    
    def get_status_statistics(self) -> Dict[str, int]:
        """获取所有状态的统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # 统计各状态词汇数量（NULL状态视为'new'）
                for status in self.VALID_STATUSES:
                    if status == 'new':
                        # 'new'状态包括明确设置为'new'和NULL的词汇
                        count = conn.execute("""
                            SELECT COUNT(*) FROM words
                            WHERE personal_status = ? OR personal_status IS NULL
                        """, (status,)).fetchone()[0]
                    else:
                        count = conn.execute("""
                            SELECT COUNT(*) FROM words
                            WHERE personal_status = ?
                        """, (status,)).fetchone()[0]
                    stats[status] = count
                
                # 总词汇数
                total = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
                stats['total'] = total
                
                # 字典匹配情况
                dict_matched = conn.execute("""
                    SELECT COUNT(*) FROM words WHERE dictionary_found = TRUE
                """).fetchone()[0]
                stats['dictionary_matched'] = dict_matched
                
                return stats
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {}
    
    def get_words_by_status(self, 
                           status: str, 
                           limit: Optional[int] = None) -> List[Dict]:
        """获取特定状态的词汇列表"""
        if status not in self.VALID_STATUSES:
            logger.error(f"❌ 无效的状态: {status}")
            return []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT w.surface_form, w.lemma, w.dictionary_found,
                           w.dictionary_rank, w.difficulty_level,
                           w.status_updated_at
                    FROM words w
                    WHERE w.personal_status = ?
                    ORDER BY w.dictionary_rank ASC, w.surface_form ASC
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor = conn.execute(query, (status,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'surface_form': row[0],
                        'lemma': row[1],
                        'dictionary_found': bool(row[2]),
                        'dictionary_rank': row[3],
                        'difficulty_level': row[4],
                        'status_updated_at': row[5]
                    })
                
                return results
        except Exception as e:
            logger.error(f"❌ 获取状态词汇失败: {e}")
            return []
    
    def analyze_document_difficulty(self, document_id: str) -> Dict:
        """分析文档基于个人词汇状态的难度情况
        
        Args:
            document_id: 文档ID
            
        Returns:
            难度分析结果
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 获取文档中的所有词汇及其状态
                cursor = conn.execute("""
                    SELECT w.personal_status, w.dictionary_rank, w.difficulty_level,
                           o.frequency, w.surface_form
                    FROM words w
                    JOIN occurrences o ON w.id = o.word_id
                    WHERE o.document_id = ?
                """, (document_id,))
                
                # 统计数据
                status_counts = {status: 0 for status in self.VALID_STATUSES}
                total_word_instances = 0
                unknown_high_freq_words = []  # 高频但用户不认识的词
                
                for row in cursor.fetchall():
                    status, rank, difficulty, frequency, surface_form = row
                    status_counts[status] += frequency  # 按出现次数计算
                    total_word_instances += frequency
                    
                    # 识别需要重点学习的词汇（高频+用户不认识）
                    if status in ['new', 'learn'] and frequency >= 3:
                        unknown_high_freq_words.append({
                            'word': surface_form,
                            'frequency': frequency,
                            'rank': rank,
                            'difficulty': difficulty,
                            'status': status
                        })
                
                # 计算难度指标
                difficulty_analysis = {
                    'total_word_instances': total_word_instances,
                    'status_distribution': status_counts,
                    'difficulty_percentage': {},
                    'recommended_words': sorted(unknown_high_freq_words, 
                                              key=lambda x: x['frequency'], 
                                              reverse=True)[:20]  # 前20个重点词
                }
                
                # 计算各状态百分比
                if total_word_instances > 0:
                    for status, count in status_counts.items():
                        difficulty_analysis['difficulty_percentage'][status] = \
                            round(count / total_word_instances * 100, 2)
                
                # 总体难度评分 (0-100, 100最难)
                new_learn_ratio = (status_counts['new'] + status_counts['learn']) / max(total_word_instances, 1)
                difficulty_analysis['overall_difficulty_score'] = round(new_learn_ratio * 100, 1)
                
                return difficulty_analysis
                
        except Exception as e:
            logger.error(f"❌ 分析文档难度失败: {e}")
            return {}
    
    def import_personal_wordlist(self, 
                                word_status_file: str, 
                                file_format: str = 'csv') -> Dict[str, int]:
        """从文件导入个人词汇状态
        
        Args:
            word_status_file: 词汇状态文件路径
            file_format: 文件格式 ('csv', 'txt', 'json')
            
        Returns:
            导入统计
        """
        import csv
        import json
        
        stats = {'imported': 0, 'failed': 0}
        
        try:
            if file_format == 'csv':
                # CSV格式: word,status
                with open(word_status_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # 跳过表头
                    
                    batch_data = []
                    for row in reader:
                        if len(row) >= 2:
                            word, status = row[0].strip(), row[1].strip().lower()
                            if status in self.VALID_STATUSES:
                                batch_data.append((word, status))
                    
                    result = self.batch_set_status(batch_data)
                    stats['imported'] = result['updated'] + result['created']
                    stats['failed'] = result['failed']
            
            elif file_format == 'txt':
                # TXT格式: word:status (每行一个)
                with open(word_status_file, 'r', encoding='utf-8') as f:
                    batch_data = []
                    for line in f:
                        line = line.strip()
                        if ':' in line:
                            word, status = line.split(':', 1)
                            word, status = word.strip(), status.strip().lower()
                            if status in self.VALID_STATUSES:
                                batch_data.append((word, status))
                    
                    result = self.batch_set_status(batch_data)
                    stats['imported'] = result['updated'] + result['created']
                    stats['failed'] = result['failed']
            
            elif file_format == 'json':
                # JSON格式: {"word": "status", ...}
                with open(word_status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    batch_data = [(word, status.lower()) 
                                for word, status in data.items() 
                                if status.lower() in self.VALID_STATUSES]
                    
                    result = self.batch_set_status(batch_data)
                    stats['imported'] = result['updated'] + result['created']
                    stats['failed'] = result['failed']
            
            logger.info(f"📥 个人词汇导入完成: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ 导入个人词汇失败: {e}")
            stats['failed'] += 1
            return stats

# 使用示例
if __name__ == "__main__":
    manager = PersonalStatusManager()
    
    # 设置一些测试词汇状态
    test_words = [
        ("hello", "master"),
        ("world", "know"),
        ("computer", "learn"),
        ("sophisticated", "new")
    ]
    
    manager.batch_set_status(test_words)
    
    # 查看统计
    stats = manager.get_status_statistics()
    print("�� 当前状态统计:", stats) 