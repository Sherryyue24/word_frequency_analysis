# 输入处理模块 - 最新架构版本
# 路径: core/engines/input/__init__.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

"""
输入处理模块 - 最新架构

核心组件：
- FileProcessor: 文件处理器
- FileReader: 文件读取器
- ModernWordlistImport: 现代词汇表导入器
- PersonalWordlistImport: 个人词汇表导入器

特性：
- 通过字典ID精确关联
- 支持多种文件格式
- 智能词汇匹配
- 个人词汇状态导入
"""

from .file_processor import FileProcessor
from .file_reader import TextReader
from .modern_wordlist_import import import_wordlist_from_file
from .personal_wordlist_import import PersonalWordlistImporter

__all__ = [
    'FileProcessor',
    'TextReader', 
    'import_wordlist_from_file',
    'PersonalWordlistImporter'
]

# 版本信息
__version__ = '2.0.0'
__supported_formats__ = ['txt', 'csv', 'json']
__architecture__ = 'dictionary_id_based' 