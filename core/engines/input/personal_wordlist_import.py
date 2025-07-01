# 个人词汇表导入器 - 最新架构版本
# 路径: core/engines/input/personal_wordlist_import.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

"""
个人词汇表导入器

支持导入个人学习状态和词汇标记：
- CSV格式：word,status,notes
- JSON格式：[{"word": "test", "status": "learn", "notes": "..."}]
- TXT格式：每行一个词汇（默认状态new）
"""

import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class PersonalWordlistImporter:
    """个人词汇表导入器"""
    
    VALID_STATUSES = {'new', 'learn', 'know', 'master'}
    
    def __init__(self, db_path: str = "data/databases/unified.db"):
        self.db_path = db_path
    
    def import_from_file(self, file_path: str, file_format: str = 'auto') -> Dict:
        """从文件导入个人词汇表"""
        
        # 自动检测格式
        if file_format == 'auto':
            file_format = self._detect_format(file_path)
        
        if file_format == 'csv':
            return self._import_csv(file_path)
        elif file_format == 'json':
            return self._import_json(file_path)
        elif file_format == 'txt':
            return self._import_txt(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_format}")
    
    def _detect_format(self, file_path: str) -> str:
        """自动检测文件格式"""
        ext = Path(file_path).suffix.lower()
        if ext == '.csv':
            return 'csv'
        elif ext == '.json':
            return 'json'
        elif ext == '.txt':
            return 'txt'
        else:
            return 'txt'  # 默认为txt
    
    def _import_csv(self, file_path: str) -> Dict:
        """导入CSV格式文件"""
        stats = {'imported': 0, 'errors': 0, 'invalid_status': 0}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row.get('word', '').strip()
                status = row.get('status', 'new').strip().lower()
                notes = row.get('notes', '').strip()
                
                if not word:
                    stats['errors'] += 1
                    continue
                
                if status not in self.VALID_STATUSES:
                    stats['invalid_status'] += 1
                    status = 'new'
                
                if self._set_word_status(word, status, notes):
                    stats['imported'] += 1
                else:
                    stats['errors'] += 1
        
        return stats
    
    def _import_json(self, file_path: str) -> Dict:
        """导入JSON格式文件"""
        stats = {'imported': 0, 'errors': 0, 'invalid_status': 0}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("JSON文件必须包含词汇对象数组")
            
            for item in data:
                word = item.get('word', '').strip()
                status = item.get('status', 'new').strip().lower()
                notes = item.get('notes', '').strip()
                
                if not word:
                    stats['errors'] += 1
                    continue
                
                if status not in self.VALID_STATUSES:
                    stats['invalid_status'] += 1
                    status = 'new'
                
                if self._set_word_status(word, status, notes):
                    stats['imported'] += 1
                else:
                    stats['errors'] += 1
        
        return stats
    
    def _import_txt(self, file_path: str) -> Dict:
        """导入TXT格式文件（每行一个词汇）"""
        stats = {'imported': 0, 'errors': 0, 'invalid_status': 0}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if not word or word.startswith('#'):  # 跳过空行和注释
                    continue
                
                if self._set_word_status(word, 'new'):
                    stats['imported'] += 1
                else:
                    stats['errors'] += 1
        
        return stats
    
    def _set_word_status(self, word: str, status: str, notes: str = None) -> bool:
        """设置词汇状态"""
        try:
            from ..vocabulary.personal_status_manager import PersonalStatusManager
            manager = PersonalStatusManager(self.db_path)
            return manager.set_word_status(word, status, create_if_missing=True)
        except Exception as e:
            print(f"设置词汇状态失败 {word}: {e}")
            return False
    
    def export_to_file(self, file_path: str, status_filter: str = None) -> Dict:
        """导出个人词汇表到文件"""
        try:
            from ..vocabulary.personal_status_manager import PersonalStatusManager
            manager = PersonalStatusManager(self.db_path)
            
            if status_filter:
                words = manager.get_words_by_status(status_filter)
            else:
                # 获取所有状态的词汇
                all_words = []
                for status in self.VALID_STATUSES:
                    words_by_status = manager.get_words_by_status(status)
                    all_words.extend(words_by_status)
                words = all_words
            
            # 根据文件扩展名选择格式
            ext = Path(file_path).suffix.lower()
            
            if ext == '.csv':
                self._export_csv(file_path, words)
            elif ext == '.json':
                self._export_json(file_path, words)
            else:
                self._export_txt(file_path, words)
            
            return {'exported': len(words), 'file_path': file_path}
            
        except Exception as e:
            return {'error': str(e)}
    
    def _export_csv(self, file_path: str, words: List[Dict]):
        """导出为CSV格式"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['word', 'status', 'dictionary_found', 'difficulty_level', 'notes'])
            
            for word_info in words:
                writer.writerow([
                    word_info.get('surface_form', ''),
                    word_info.get('personal_status', 'new'),
                    word_info.get('dictionary_found', False),
                    word_info.get('difficulty_level', ''),
                    word_info.get('personal_notes', '')
                ])
    
    def _export_json(self, file_path: str, words: List[Dict]):
        """导出为JSON格式"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(words, f, ensure_ascii=False, indent=2)
    
    def _export_txt(self, file_path: str, words: List[Dict]):
        """导出为TXT格式"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for word_info in words:
                f.write(f"{word_info.get('surface_form', '')}\n")

# 兼容函数
def import_personal_wordlist(file_path: str, file_format: str = 'auto') -> Dict:
    """导入个人词汇表（兼容函数）"""
    importer = PersonalWordlistImporter()
    return importer.import_from_file(file_path, file_format)

def export_personal_wordlist(file_path: str, status_filter: str = None) -> Dict:
    """导出个人词汇表（兼容函数）"""
    importer = PersonalWordlistImporter()
    return importer.export_to_file(file_path, status_filter)

# 示例用法
if __name__ == "__main__":
    # 测试导入功能
    test_csv_content = "word,status\nhello,master\nworld,know\ncomputer,learn\nrunning,new\ntesting,learn"
    
    with open("test_personal_vocab.csv", "w", encoding="utf-8") as f:
        f.write(test_csv_content)
    
    print("🧪 测试个人词汇表导入功能...")
    print("=" * 50)
    
    # 导入测试
    stats = import_personal_wordlist("test_personal_vocab.csv", default_status="new")
    
    # 导出测试
    print("\n🧪 测试个人词汇表导出功能...")
    success = export_personal_wordlist("exported_personal_vocab.csv")
    if success:
        print("✅ 导出成功! 查看文件: exported_personal_vocab.csv")
    else:
        print("❌ 导出失败")
    
    # 清理测试文件
    import os
    try:
        os.remove("test_personal_vocab.csv")
        if os.path.exists("exported_personal_vocab.csv"):
            os.remove("exported_personal_vocab.csv")
        print("\n🧹 测试文件已清理")
    except Exception as e:
        print(f"清理文件时出错: {e}") 