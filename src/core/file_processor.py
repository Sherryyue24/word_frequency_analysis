from pathlib import Path
from datetime import datetime
from .word_analyzer import analyze_text
from .file_reader import TextReader
from .database import StorageManager
from ..utils.helpers import get_supported_files
import os
import time

class TextProcessor:
    """负责处理新文本文件的类"""
    def __init__(self):
        self.reader = TextReader()  # 组合关系
        self.storage_manager = StorageManager()
    
    def process_new_texts(self, directory_path, scan_subdirs=True):
        """处理指定目录下的新文本文件"""
        try:
            file_paths = get_supported_files(directory_path, scan_subdirs, 
                                           supported_formats=self.reader.supported_formats.keys())
            if not self._validate_files(file_paths, directory_path):
                return
                
            self._process_files(file_paths, directory_path)
            self._update_word_stats() #更新词频
            
        except Exception as e:
            print(f"处理文本时发生错误: {str(e)}")
    
    def _validate_files(self, file_paths, directory_path):
        """验证找到的文件"""
        if not file_paths:
            print(f"在目录 {directory_path} 中没有找到支持的文件类型")
            return False
            
        print(f"\n找到 {len(file_paths)} 个文件待处理:")
        for path in file_paths:
            rel_path = os.path.relpath(path, directory_path)
            print(f"- {rel_path}")
        return True
    
    def _process_files(self, file_paths, directory_path):
        """处理文件列表"""
        print("\n开始处理文件...")
        for i, file_path in enumerate(file_paths, 1):
            rel_path = os.path.relpath(file_path, directory_path)
            print(f"\n[{i}/{len(file_paths)}] 处理文件: {rel_path}")
            try:
                self._process_single_file(file_path)
            except Exception as e:
                print(f"处理文件失败: {str(e)}")
                continue
   
    def _process_single_file(self, file_path):
        """处理单个文件"""
        # 使用TextReader读取和预处理文本
        text = self.reader.read_file(file_path)
        text = self.reader.preprocess_text(text)
        content_hash = self.storage_manager.calculate_text_hash(text)
        
        # 检查缓存
        cached_result = self.storage_manager.get_existing_analysis(content_hash)
        if cached_result:
            print("找到缓存的分析结果")
            # 更新时间戳
            if self.storage_manager.update_analysis_timestamp(content_hash):
                print("已更新访问时间戳")
            return cached_result, content_hash
        
        # 新分析
        print("没有缓存，进行分析")
        start_time = time.time()  # 开始计时
        
        basic_info, word_frequencies = analyze_text(text, self.reader)
        
        # 计算处理时长（秒）
        process_duration = time.time() - start_time
        
        # 获取文件元数据
        metadata = self.reader.get_metadata()
        basic_info.update(metadata)
        basic_info['filename'] = Path(file_path).name
        basic_info['analysis_date'] = datetime.now().isoformat()
        basic_info['process_duration'] = process_duration  # 添加处理时长到基本信息中
        
        self.storage_manager.store_analysis(
            content_hash=content_hash,
            filename=basic_info['filename'],
            basic_info=basic_info,
            word_frequencies=word_frequencies,
            process_duration=process_duration
        )
        
        print(f"分析完成并保存到数据库，处理时长：{process_duration:.4f}秒")
        return (basic_info, word_frequencies), content_hash

    def _update_word_stats(self):
        """更新词频统计"""
        print("\n更新词频统计信息...")
        self.storage_manager.update_word_stats()
        print("词频统计更新完成!")