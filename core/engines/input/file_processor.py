# 文件处理器 - 使用统一数据库适配器
# 路径: core/engines/file_processor.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

from pathlib import Path
from datetime import datetime
from ..vocabulary.word_analyzer import analyze_text
from .file_reader import TextReader
from ..database.database_adapter import unified_adapter
from ...utils.helpers import get_supported_files
import os
import time
import shutil
from collections import Counter

class TextProcessor:
    """负责处理新文本文件的类 - 现已使用统一架构"""
    def __init__(self, storage_manager=None, move_processed=True):
        self.reader = TextReader()  # 组合关系
        # 使用传入的存储管理器或默认的统一适配器
        self.storage_manager = storage_manager or unified_adapter
        # 是否在处理完成后移动文件到processed目录
        self.move_processed = move_processed
    
    def process_new_texts(self, directory_path, scan_subdirs=True):
        """处理指定目录下的新文本文件"""
        try:
            file_paths = get_supported_files(directory_path, scan_subdirs, 
                                           supported_formats=self.reader.supported_formats.keys())
            if not self._validate_files(file_paths, directory_path):
                return
                
            self._process_files(file_paths, directory_path)
            # 统一架构下不需要手动更新词频统计
            print("✅ 所有文件处理完成")
            
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
                result = self._process_single_file(file_path)
                if result and self.move_processed:
                    self._move_to_processed(file_path)
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
            process_duration=process_duration,
            original_text=text
        )
        
        # 生成分析报告
        self.save_analysis_report(file_path, basic_info, word_frequencies, content_hash)
        
        print(f"分析完成并保存到数据库，处理时长：{process_duration:.4f}秒")
        return (basic_info, word_frequencies), content_hash

    def _move_to_processed(self, file_path):
        """将处理完的文件移动到processed目录"""
        try:
            file_path = Path(file_path)
            
            # 确定processed目录路径
            # 如果文件在data/files/new/下，移动到data/files/processed/
            if 'data/files/new' in str(file_path):
                processed_dir = Path('data/files/processed')
            else:
                # 否则在同级目录创建processed目录
                processed_dir = file_path.parent / 'processed'
            
            # 创建processed目录（如果不存在）
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            # 目标文件路径
            target_path = processed_dir / file_path.name
            
            # 如果目标文件已存在，添加时间戳避免冲突
            if target_path.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                stem = target_path.stem
                suffix = target_path.suffix
                target_path = processed_dir / f"{stem}_{timestamp}{suffix}"
            
            # 移动文件
            shutil.move(str(file_path), str(target_path))
            print(f"📁 文件已移动: {file_path.name} → {processed_dir.name}/")
            
        except Exception as e:
            print(f"⚠️  文件移动失败 {file_path}: {e}")
            # 移动失败不影响主流程，继续处理其他文件

    def organize_existing_files(self):
        """整理已处理的文件：将数据库中已存在的文件移动到processed目录"""
        try:
            print("🗂️  开始整理已处理的文件...")
            
            # 获取数据库中所有已分析的文件名
            analyses = self.storage_manager.get_all_analyses()
            
            # 处理不同的数据格式
            if not analyses:
                print("📊 数据库中没有已分析文件")
                return
                
            # 提取文件名，处理元组格式的数据
            analyzed_filenames = set()
            for analysis in analyses:
                if isinstance(analysis, dict):
                    # 字典格式
                    analyzed_filenames.add(analysis['filename'])
                elif isinstance(analysis, (list, tuple)) and len(analysis) > 1:
                    # 元组/列表格式，假设filename在第二个位置
                    analyzed_filenames.add(analysis[1])
                else:
                    # 其他格式，尝试直接添加
                    try:
                        analyzed_filenames.add(str(analysis))
                    except:
                        continue
            
            print(f"📊 数据库中有 {len(analyzed_filenames)} 个已分析文件")
            
            # 检查new目录中的文件
            new_dir = Path('data/files/new')
            if not new_dir.exists():
                print("❌ data/files/new 目录不存在")
                return
            
            moved_count = 0
            for file_path in new_dir.rglob('*'):
                if file_path.is_file() and file_path.name in analyzed_filenames:
                    self._move_to_processed(file_path)
                    moved_count += 1
            
            print(f"✅ 整理完成，共移动了 {moved_count} 个已处理的文件")
            
        except Exception as e:
            print(f"❌ 整理文件时出错: {e}")
            import traceback
            traceback.print_exc()

    def save_analysis_report(self, filepath: str, basic_info: dict, word_frequencies: dict, content_hash: str, generate_report: bool = True):
        """保存文本分析报告到文件"""
        if not generate_report:
            return
            
        try:
            # 确保exports目录存在
            exports_dir = Path("data/exports")
            exports_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成报告文件名：文件名_分析报告_时间戳.txt
            filename = Path(filepath).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"{filename}_analysis_report_{timestamp}.txt"
            report_file = exports_dir / report_filename
            
            # 计算统计信息
            total_words = basic_info.get('total_words', 0)
            unique_words = basic_info.get('unique_words', 0)
            total_sentences = basic_info.get('sentences', 0)
            total_paragraphs = basic_info.get('paragraphs', 0)
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            
            # 词频分析
            sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
            most_frequent = sorted_words[:20]  # 前20个高频词
            
            # 词长分析
            word_lengths = [len(word) for word in word_frequencies.keys()]
            avg_word_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0
            length_counter = Counter(word_lengths)
            
            # 频率分析
            freq_values = list(word_frequencies.values())
            freq_counter = Counter(freq_values)
            single_occurrence = freq_counter.get(1, 0)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                # 报告头部
                f.write("=" * 60 + "\n")
                f.write("          文本分析报告\n")
                f.write("=" * 60 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"源文件: {filepath}\n")
                f.write(f"文件名: {basic_info.get('filename', 'Unknown')}\n")
                f.write(f"文件大小: {file_size} bytes\n")
                f.write(f"内容哈希: {content_hash[:16]}...\n")
                f.write(f"分析时间: {basic_info.get('analysis_date', 'Unknown')}\n")
                f.write(f"处理时长: {basic_info.get('process_duration', 0):.4f} 秒\n")
                f.write("-" * 60 + "\n\n")
                
                # 基本统计信息
                f.write("📊 基本统计信息\n")
                f.write("-" * 30 + "\n")
                f.write(f"总词数: {total_words}\n")
                f.write(f"独特词汇数: {unique_words}\n")
                f.write(f"句子数: {total_sentences}\n")
                f.write(f"段落数: {total_paragraphs}\n")
                f.write(f"词汇复用率: {((total_words - unique_words) / total_words * 100):.1f}%\n")
                f.write(f"平均词长: {avg_word_length:.1f} 字符\n")
                if total_sentences > 0:
                    f.write(f"平均句长: {total_words / total_sentences:.1f} 词\n")
                f.write("\n")
                
                # 词频分析
                f.write("🔢 词频分析\n")
                f.write("-" * 30 + "\n")
                f.write(f"单次出现词汇: {single_occurrence} 个 ({(single_occurrence/unique_words*100):.1f}%)\n")
                f.write(f"最高频率: {max(freq_values) if freq_values else 0}\n")
                f.write(f"平均频率: {sum(freq_values)/len(freq_values):.2f}\n")
                f.write("\n")
                
                # 高频词汇
                if most_frequent:
                    f.write("📈 高频词汇 (Top 20)\n")
                    f.write("-" * 30 + "\n")
                    for i, (word, freq) in enumerate(most_frequent, 1):
                        percentage = (freq / total_words) * 100
                        f.write(f"{i:2d}. {word:<15} {freq:>4} 次 ({percentage:.2f}%)\n")
                    f.write("\n")
                
                # 词长分布
                f.write("📏 词长分布\n")
                f.write("-" * 30 + "\n")
                for length in sorted(length_counter.keys())[:15]:  # 显示前15种词长
                    count = length_counter[length]
                    percentage = (count / unique_words) * 100
                    f.write(f"{length:2d} 字符: {count:>4} 词 ({percentage:.1f}%)\n")
                f.write("\n")
                
                # 频率分布
                f.write("📊 频率分布\n")
                f.write("-" * 30 + "\n")
                freq_ranges = [(1, 1), (2, 5), (6, 10), (11, 20), (21, 50), (51, float('inf'))]
                for min_freq, max_freq in freq_ranges:
                    if max_freq == float('inf'):
                        count = sum(1 for f in freq_values if f >= min_freq)
                        label = f"{min_freq}+ 次"
                    else:
                        count = sum(1 for f in freq_values if min_freq <= f <= max_freq)
                        if min_freq == max_freq:
                            label = f"{min_freq} 次"
                        else:
                            label = f"{min_freq}-{max_freq} 次"
                    
                    percentage = (count / unique_words) * 100 if unique_words > 0 else 0
                    f.write(f"{label:<10}: {count:>4} 词 ({percentage:.1f}%)\n")
                f.write("\n")
                
                # 词汇表匹配分析
                f.write("📚 词汇表匹配分析\n")
                f.write("-" * 30 + "\n")
                # 获取所有词汇表
                try:
                    wordlists = unified_adapter.get_all_wordlists()
                    if wordlists:
                        text_words = set(word_frequencies.keys())
                        for wl in wordlists:
                            wordlist_name = wl['name']
                            
                            # 获取词汇表中的所有词汇
                            wordlist_words = unified_adapter.get_wordlist_words(wordlist_name)
                            wordlist_word_set = set(word.lower() for word in wordlist_words)
                            
                            # 计算匹配
                            matched_words = text_words.intersection(wordlist_word_set)
                            match_count = len(matched_words)
                            coverage_percentage = (match_count / unique_words * 100) if unique_words > 0 else 0
                            
                            # 计算匹配词汇的总频率
                            matched_frequency = sum(word_frequencies[word] for word in matched_words)
                            frequency_percentage = (matched_frequency / total_words * 100) if total_words > 0 else 0
                            
                            f.write(f"📖 {wordlist_name}:\n")
                            f.write(f"   匹配词汇: {match_count}/{wl['word_count']} 个\n")
                            f.write(f"   覆盖率: {coverage_percentage:.1f}% (文本独特词汇)\n")
                            f.write(f"   频率覆盖: {frequency_percentage:.1f}% (总词频)\n")
                            if match_count > 0:
                                # 显示前10个匹配的高频词
                                matched_sorted = sorted(matched_words, key=lambda x: word_frequencies[x], reverse=True)
                                sample_words = matched_sorted[:10]
                                f.write(f"   匹配示例: {', '.join(sample_words)}\n")
                            f.write("\n")
                    else:
                        f.write("暂无加载的词汇表\n")
                except Exception as e:
                    f.write(f"获取词汇表信息失败: {e}\n")
                f.write("\n")
                
                # 单次出现词汇
                f.write("🔍 单次出现词汇列举\n")
                f.write("-" * 30 + "\n")
                
                # 获取只出现一次的词汇
                single_words = [word for word, freq in word_frequencies.items() if freq == 1]
                
                if single_words:
                    f.write(f"共有 {len(single_words)} 个词汇只出现过一次，占独特词汇的 {len(single_words)/unique_words*100:.1f}%\n\n")
                    
                    # 按字母顺序排列显示
                    sorted_single_words = sorted(single_words)
                    
                    # 分页显示，每行10个词，最多显示100个
                    display_count = min(len(sorted_single_words), 100)
                    for i in range(0, display_count, 10):
                        line_words = sorted_single_words[i:i+10]
                        f.write(f"  {', '.join(line_words)}\n")
                    
                    if len(sorted_single_words) > 100:
                        f.write(f"  ... 还有 {len(sorted_single_words) - 100} 个单次出现词汇\n")
                    f.write("\n")
                    
                    # 单次出现词汇的词长分析
                    single_word_lengths = [len(word) for word in single_words]
                    if single_word_lengths:
                        avg_single_length = sum(single_word_lengths) / len(single_word_lengths)
                        max_single_length = max(single_word_lengths)
                        min_single_length = min(single_word_lengths)
                        f.write(f"单次词汇统计: 平均长度 {avg_single_length:.1f} 字符，最长 {max_single_length} 字符，最短 {min_single_length} 字符\n")
                        
                        # 显示最长的单次出现词汇
                        longest_singles = [word for word in single_words if len(word) == max_single_length]
                        if longest_singles:
                            f.write(f"最长单次词汇: {', '.join(longest_singles[:5])}\n")
                else:
                    f.write("没有只出现一次的词汇\n")
                f.write("\n")
                
                # 报告尾部
                f.write("=" * 60 + "\n")
                f.write("分析报告生成完成\n")
                f.write("=" * 60 + "\n")
            
            print(f"📄 分析报告已保存到: {report_file}")
            return str(report_file)
            
        except Exception as e:
            print(f"❌ 生成分析报告失败: {e}")
            return None

# 向后兼容别名
FileProcessor = TextProcessor
