# 现代化词汇表导入模块
# 路径: core/engines/input/modern_wordlist_import.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

from pathlib import Path
from datetime import datetime
from ..database.database_adapter import unified_adapter
from typing import List, Tuple, Dict

def save_import_report(output_file: str, filepath: str, tag_name: str, stats: dict, skipped_lines: dict, processing_details: dict):
    """保存导入报告到文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        # 报告头部
        f.write("=" * 60 + "\n")
        f.write("          词汇表导入报告\n")
        f.write("=" * 60 + "\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"源文件: {filepath}\n")
        f.write(f"词汇表标签: {tag_name}\n")
        f.write(f"文件大小: {stats['file_size']} bytes\n")
        f.write(f"总字符数: {stats['char_count']}\n")
        f.write(f"总行数: {stats['total_lines']}\n")
        f.write("-" * 60 + "\n\n")
        
        # 处理结果概览
        f.write("📊 处理结果概览\n")
        f.write("-" * 30 + "\n")
        f.write(f"有效词汇数: {stats['valid_words_count']}\n")
        f.write(f"成功导入: {stats['imported_count']}\n")
        f.write(f"已存在词汇: {stats['existing_count']}\n")
        f.write(f"总跳过行数: {stats['total_skipped']}\n")
        f.write(f"导入成功率: {stats['success_rate']:.1f}%\n")
        f.write(f"词汇提取率: {stats['extraction_rate']:.1f}%\n\n")
        
        # 跳过统计详情
        f.write("🚫 跳过统计详情\n")
        f.write("-" * 30 + "\n")
        f.write(f"空行数量: {len(skipped_lines['empty'])}\n")
        f.write(f"标题行数量: {len(skipped_lines['title'])}\n")
        f.write(f"无效词汇数量: {len(skipped_lines['invalid'])}\n")
        f.write(f"清理失败数量: {len(skipped_lines['clean_failed'])}\n")
        f.write(f"格式错误数量: {len(skipped_lines['format_error'])}\n")
        f.write(f"已存在词汇数量: {len(skipped_lines['already_exists'])}\n")
        f.write(f"导入失败数量: {len(skipped_lines['import_failed'])}\n\n")
        
        # 处理示例
        f.write("🔍 处理示例\n")
        f.write("-" * 30 + "\n")
        if processing_details['cleaned_examples']:
            f.write("词汇清理示例:\n")
            for original, cleaned in processing_details['cleaned_examples'][:10]:
                f.write(f"  '{original}' → '{cleaned}'\n")
            f.write("\n")
        
        # 详细错误信息
        if skipped_lines['title']:
            f.write("📋 标题行详情:\n")
            for line_num, line in skipped_lines['title'][:20]:  # 限制显示数量
                f.write(f"  第 {line_num} 行: {line}\n")
            f.write("\n")
        
        if skipped_lines['invalid']:
            f.write("❌ 无效词汇详情:\n")
            for line_num, original_word, reason in skipped_lines['invalid'][:20]:
                f.write(f"  第 {line_num} 行: '{original_word}' - {reason}\n")
            f.write("\n")
        
        if skipped_lines['clean_failed']:
            f.write("🧹 清理失败详情:\n")
            for line_num, original_word in skipped_lines['clean_failed'][:20]:
                f.write(f"  第 {line_num} 行: '{original_word}'\n")
            f.write("\n")
        
        if skipped_lines['format_error']:
            f.write("⚠️  格式错误详情:\n")
            for line_num, line, error in skipped_lines['format_error'][:20]:
                f.write(f"  第 {line_num} 行: {line}\n")
                f.write(f"    错误: {error}\n")
            f.write("\n")
        
        if skipped_lines['already_exists']:
            f.write("🔄 重复词汇详情:\n")
            for line_num, word, reason in skipped_lines['already_exists'][:50]:
                f.write(f"  第 {line_num} 行: '{word}' - {reason}\n")
            if len(skipped_lines['already_exists']) > 50:
                f.write(f"  ... 还有 {len(skipped_lines['already_exists']) - 50} 个重复词汇\n")
            f.write("\n")
        
        if skipped_lines['import_failed']:
            f.write("💥 导入失败详情:\n")
            f.write(f"总计 {len(skipped_lines['import_failed'])} 个词汇导入失败\n\n")
            
            # 按错误类型分组显示
            error_groups = {}
            for line_num, word, error in skipped_lines['import_failed']:
                if error not in error_groups:
                    error_groups[error] = []
                error_groups[error].append((line_num, word))
            
            for error_type, failed_items in error_groups.items():
                f.write(f"错误类型: {error_type}\n")
                f.write(f"影响词汇数: {len(failed_items)}\n")
                f.write("失败词汇列表:\n")
                for line_num, word in failed_items[:50]:  # 限制显示数量避免报告过长
                    f.write(f"  第 {line_num} 行: '{word}'\n")
                if len(failed_items) > 50:
                    f.write(f"  ... 还有 {len(failed_items) - 50} 个词汇\n")
                f.write("\n")
            
            # 完整失败词汇清单
            f.write("📋 完整失败词汇清单:\n")
            all_failed_words = [word for _, word, _ in skipped_lines['import_failed']]
            for i, word in enumerate(all_failed_words, 1):
                f.write(f"  {i:3d}. {word}\n")
                if i % 20 == 0 and i < len(all_failed_words):
                    f.write("      ...\n")
            f.write("\n")
        
        # 成功导入的词汇样本
        if processing_details['imported_examples']:
            f.write("✅ 成功导入词汇样本:\n")
            for word in processing_details['imported_examples'][:30]:
                f.write(f"  - {word}\n")
            f.write("\n")
        
        # 报告尾部
        f.write("=" * 60 + "\n")
        f.write("报告生成完成\n")
        f.write("=" * 60 + "\n")

def import_wordlist_from_file(filepath: str, tag_name: str = None, description: str = None, 
                            generate_report: bool = True) -> bool:
    """
    从文件导入词汇表到统一数据库（带详细报告）
    
    Args:
        filepath: 词汇表文件路径
        tag_name: 词汇表标签名（如果不提供则使用文件名）
        description: 词汇表描述
        generate_report: 是否生成导入报告
        
    Returns:
        bool: 导入是否成功
    """
    try:
        filepath = Path(filepath)
        
        # 如果没有提供标签名，使用文件名
        if not tag_name:
            tag_name = filepath.stem
        
        # 初始化统计信息
        skipped_lines = {
            'empty': [],           # 空行
            'title': [],           # 标题行 (line_num, line)
            'invalid': [],         # 无效词汇 (line_num, original_word, reason)
            'clean_failed': [],    # 清理失败 (line_num, original_word)
            'format_error': [],    # 格式错误 (line_num, line, error)
            'already_exists': [],  # 已存在 (line_num, word)
            'import_failed': []    # 导入失败 (line_num, word, error)
        }
        
        processing_details = {
            'cleaned_examples': [],    # 清理示例 (original, cleaned)
            'imported_examples': []    # 导入成功的词汇样本
        }
        
        # 读取文件基本信息
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            file_size = len(content.encode('utf-8'))
            char_count = len(content)
        
        # 处理词汇文件
        words_to_import = []
        total_lines = 0
        word_line_mapping = {}  # 追踪词汇首次出现的行号
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                total_lines += 1
                original_line = line
                line = line.strip()
                
                # 空行处理
                if not line:
                    skipped_lines['empty'].append(line_num)
                    continue
                
                try:
                    # 支持多种格式处理
                    # 1. 制表符分隔格式（如AWL）：取第一列
                    if '\t' in line:
                        word = line.split('\t')[0].strip()
                    # 2. 逗号分隔格式：处理所有词汇
                    elif ',' in line and '\t' not in line:
                        line_words = [w.strip() for w in line.split(',') if w.strip()]
                        for word in line_words:
                            processed = _process_single_word(word, line_num, skipped_lines, processing_details)
                            if processed:
                                # 检查重复词汇
                                if processed in word_line_mapping:
                                    skipped_lines['already_exists'].append((line_num, processed, f"重复词汇，首次出现在第{word_line_mapping[processed]}行"))
                                else:
                                    word_line_mapping[processed] = line_num
                                    words_to_import.append((processed, line_num))
                        continue
                    # 3. 每行一个词格式
                    else:
                        word = line.split()[0] if line.split() else ''
                    
                    if not word:
                        skipped_lines['empty'].append(line_num)
                        continue
                    
                    processed = _process_single_word(word, line_num, skipped_lines, processing_details)
                    if processed:
                        # 检查重复词汇
                        if processed in word_line_mapping:
                            skipped_lines['already_exists'].append((line_num, processed, f"重复词汇，首次出现在第{word_line_mapping[processed]}行"))
                        else:
                            word_line_mapping[processed] = line_num
                            words_to_import.append((processed, line_num))
                            
                except Exception as e:
                    skipped_lines['format_error'].append((line_num, original_line.strip(), str(e)))
                    continue
        
        # 计算统计信息
        valid_words_count = len(words_to_import)
        total_skipped = sum(len(v) for v in skipped_lines.values())
        
        if not words_to_import:
            print(f"❌ 文件 {filepath} 中未找到有效词汇")
            return False
        
        print(f"📚 从 {filepath.name} 读取到 {valid_words_count} 个有效词汇")
        print(f"📊 跳过 {total_skipped} 行无效内容")
        
        # 导入到数据库 - 改进版：跟踪每个词汇的导入状态
        words_only = [word for word, _ in words_to_import]
        import_result, failed_words = _import_words_with_tracking(tag_name, words_to_import)
        
        # 统计导入结果
        success = import_result.get('success', False)
        imported_count = import_result.get('new_associations', 0)
        existing_count = import_result.get('existing_associations', 0)
        
        # 记录失败的词汇
        for failed_word, line_num, error in failed_words:
            skipped_lines['import_failed'].append((line_num, failed_word, error))
        
        # 收集导入成功的词汇样本
        if success and imported_count > 0:
            processing_details['imported_examples'] = [word for word, _ in words_to_import 
                                                     if word not in [fw[0] for fw in failed_words]][:30]
        
        # 计算最终统计信息
        stats = {
            'file_size': file_size,
            'char_count': char_count,
            'total_lines': total_lines,
            'valid_words_count': valid_words_count,
            'imported_count': imported_count,
            'existing_count': existing_count,
            'total_skipped': total_skipped,
            'success_rate': (imported_count / valid_words_count * 100) if valid_words_count > 0 else 0,
            'extraction_rate': (valid_words_count / total_lines * 100) if total_lines > 0 else 0
        }
        
        # 生成导入报告
        if generate_report:
            # 确保exports目录存在
            exports_dir = Path("data/exports")
            exports_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成报告文件名：词汇表名_导入报告_时间戳.txt
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"{tag_name}_import_report_{timestamp}.txt"
            report_file = exports_dir / report_filename
            
            save_import_report(str(report_file), str(filepath), tag_name, stats, skipped_lines, processing_details)
            print(f"📄 导入报告已保存到: {report_file}")
        
        if success:
            print(f"✅ 成功导入词汇表 '{tag_name}' ({imported_count} 个词汇)")
            print(f"📊 提取率: {stats['extraction_rate']:.1f}%, 成功率: {stats['success_rate']:.1f}%")
            return True
        else:
            print(f"❌ 导入词汇表 '{tag_name}' 失败")
            return False
            
    except FileNotFoundError:
        print(f"❌ 找不到文件: {filepath}")
        return False
    except Exception as e:
        print(f"❌ 导入过程出错: {e}")
        return False

def _process_single_word(word: str, line_num: int, skipped_lines: dict, processing_details: dict) -> str:
    """处理单个词汇并更新统计信息"""
    original_word = word
    
    # 检查是否是标题行
    if any(phrase in word.lower() for phrase in ['word', 'list', 'part', 'unit', 'lesson']):
        if word.lower().startswith('word') or word.isdigit():
            skipped_lines['title'].append((line_num, word))
            return ''
    
    # 清理词汇
    clean_word = _clean_vocabulary_word(word)
    
    if not clean_word:
        skipped_lines['clean_failed'].append((line_num, original_word))
        return ''
    
    if len(clean_word) <= 1:
        skipped_lines['invalid'].append((line_num, original_word, "词汇太短"))
        return ''
    
    # 记录清理示例
    if original_word != clean_word and len(processing_details['cleaned_examples']) < 20:
        processing_details['cleaned_examples'].append((original_word, clean_word))
    
    return clean_word.lower()

def import_multiple_wordlists(directory: str, pattern: str = "*.txt", generate_reports: bool = True) -> int:
    """
    批量导入目录下的词汇表文件
    
    Args:
        directory: 词汇表文件目录
        pattern: 文件名模式
        generate_reports: 是否为每个文件生成导入报告
        
    Returns:
        int: 成功导入的词汇表数量
    """
    directory = Path(directory)
    
    if not directory.exists():
        print(f"❌ 目录不存在: {directory}")
        return 0
    
    wordlist_files = list(directory.glob(pattern))
    
    if not wordlist_files:
        print(f"❌ 目录 {directory} 中未找到匹配 {pattern} 的文件")
        return 0
    
    print(f"🔍 找到 {len(wordlist_files)} 个词汇表文件")
    
    success_count = 0
    total_reports = []
    
    for file_path in wordlist_files:
        print(f"\n处理文件: {file_path.name}")
        if import_wordlist_from_file(str(file_path), generate_report=generate_reports):
            success_count += 1
            if generate_reports:
                # 记录报告文件（在exports目录中）
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_name = f"{file_path.stem}_import_report_{timestamp}.txt"
                total_reports.append(f"data/exports/{report_name}")
    
    print(f"\n📊 批量导入完成: {success_count}/{len(wordlist_files)} 个词汇表导入成功")
    if generate_reports and total_reports:
        print(f"📄 生成了 {len(total_reports)} 个导入报告，保存在 data/exports/ 目录")
    
    return success_count

def get_available_wordlists() -> list:
    """获取可用的词汇表列表"""
    return unified_adapter.get_all_wordlists()

def get_wordlist_stats() -> dict:
    """获取词汇表统计信息"""
    return unified_adapter.get_database_info()

# 向后兼容的函数名
def import_wordlist_to_database(db, words, tag_name="Imported"):
    """向后兼容的导入函数"""
    print(f"⚠️  使用向后兼容模式导入 {len(words)} 个词汇到标签 '{tag_name}'")
    return unified_adapter.add_words_to_wordlist(tag_name, words)

def _clean_vocabulary_word(word: str) -> str:
    """清理词汇表中的词汇，移除标记符号但保留有效内容"""
    
    # 跳过明显的标题行
    if any(phrase in word.lower() for phrase in ['word', 'list', 'part', 'unit', 'lesson']):
        if word.lower().startswith('word') or word.isdigit():
            return ''
    
    # 基本清理：移除前后空格
    clean_word = word.strip()
    
    # 跳过纯数字词汇
    if clean_word.isdigit():
        return ''
    
    # 跳过包含数字的词汇（除了特定年代格式如1920s）
    if any(c.isdigit() for c in clean_word):
        # 允许年代格式（如1920s, 1990s）
        if not (clean_word.endswith('s') and clean_word[:-1].isdigit() and len(clean_word) >= 5):
            return ''
    
    # 移除常见的标记符号
    clean_word = clean_word.rstrip('*')  # 移除尾部星号
    clean_word = clean_word.strip('[](){}')  # 移除括号
    clean_word = clean_word.strip('"\'')  # 移除引号
    
    # 跳过过短的词汇（少于2个字符，除了"I"和"a"）
    if len(clean_word) < 2 and clean_word.lower() not in ['i', 'a']:
        return ''
    
    # 跳过过长的词汇（超过30个字符，可能是错误数据）
    if len(clean_word) > 30:
        return ''
    
    # 处理连字符词汇 - 保守处理，保留完整词汇
    if '-' in clean_word:
        # 移除明显的前缀标记（如编号或格式标记）
        if clean_word.startswith('-') or clean_word.endswith('-'):
            clean_word = clean_word.strip('-')
        # 跳过看起来像编号的词汇（如 "1-2", "a-z"）
        if len(clean_word.split('-')) == 2:
            parts = clean_word.split('-')
            if all(len(part) <= 2 for part in parts):
                return ''
    
    # 验证是否为有效词汇
    # 允许字母、连字符、撇号（如don't, it's）
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-'")
    if clean_word and len(clean_word) >= 2 and all(c in allowed_chars for c in clean_word):
        # 确保不是纯符号
        if any(c.isalpha() for c in clean_word):
            return clean_word
    
    return ''

def _import_words_with_tracking(tag_name: str, words_with_lines: List[Tuple[str, int]]) -> Tuple[Dict, List[Tuple[str, int, str]]]:
    """
    逐个导入词汇并跟踪失败情况
    
    Args:
        tag_name: 词汇表标签名
        words_with_lines: 词汇及其行号的列表 [(word, line_num), ...]
        
    Returns:
        Tuple[Dict, List]: (导入结果统计, 失败词汇列表 [(word, line_num, error), ...])
    """
    
    # 创建词汇到行号的映射
    word_to_line = {word: line_num for word, line_num in words_with_lines}
    
    # 尝试批量导入
    words_only = [word for word, _ in words_with_lines]
    try:
        import_result = unified_adapter.add_words_to_wordlist(tag_name, words_only)
        
        # 检查是否有验证失败的词汇
        failed_words = []
        if 'invalid_words' in import_result:
            for word, error in import_result['invalid_words']:
                line_num = word_to_line.get(word, 0)
                failed_words.append((word, line_num, error))
        
        if import_result.get('success', False):
            # 导入成功（可能是部分成功）
            return import_result, failed_words
        else:
            # 批量导入完全失败，逐个验证找出问题词汇
            return _fallback_individual_import(tag_name, words_with_lines, import_result.get('error', '批量导入失败'))
            
    except Exception as e:
        # 批量导入异常，逐个验证
        return _fallback_individual_import(tag_name, words_with_lines, str(e))

def _fallback_individual_import(tag_name: str, words_with_lines: List[Tuple[str, int]], batch_error: str) -> Tuple[Dict, List[Tuple[str, int, str]]]:
    """
    当批量导入失败时，逐个导入词汇以确定具体失败原因
    
    Args:
        tag_name: 词汇表标签名
        words_with_lines: 词汇及其行号的列表
        batch_error: 批量导入的错误信息
        
    Returns:
        Tuple[Dict, List]: (导入结果统计, 失败词汇列表)
    """
    
    successful_imports = 0
    existing_words = 0
    failed_words = []
    
    print(f"⚠️  批量导入失败 ({batch_error})，正在逐个验证词汇...")
    
    for word, line_num in words_with_lines:
        try:
            # 逐个导入词汇
            individual_result = unified_adapter.add_words_to_wordlist(tag_name, [word])
            
            if individual_result.get('success', False):
                new_count = individual_result.get('new_associations', 0)
                existing_count = individual_result.get('existing_associations', 0)
                
                successful_imports += new_count
                existing_words += existing_count
            else:
                error_msg = individual_result.get('error', '未知错误')
                failed_words.append((word, line_num, error_msg))
                
        except Exception as e:
            failed_words.append((word, line_num, str(e)))
    
    # 构建结果统计
    total_words = len(words_with_lines)
    result_stats = {
        'total_words': total_words,
        'new_associations': successful_imports,
        'existing_associations': existing_words,
        'failed_imports': len(failed_words),
        'success': len(failed_words) < total_words  # 只要有部分成功就算成功
    }
    
    print(f"✅ 逐个验证完成: {successful_imports}个新增, {existing_words}个已存在, {len(failed_words)}个失败")
    
    return result_stats, failed_words
