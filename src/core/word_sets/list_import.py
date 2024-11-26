from pathlib import Path
import sqlite3
import traceback


def clean_word(word):
    """清理单词，去除特殊字符"""
    if '*' in word:
        word = word.replace('*', '')
    return ''.join(c for c in word if c.isalpha())

def save_import_report(output_file, stats, skipped_lines, existing_words):
    """保存导入报告到文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== 处理结果详情 ===\n")
        
        f.write("\n【跳过情况】\n")
        f.write(f"空行数量: {len(skipped_lines['empty'])}\n")
        f.write(f"标题行数量: {len(skipped_lines['title'])}\n")
        f.write(f"无效单词数量: {len(skipped_lines['invalid'])}\n")
        f.write(f"格式错误数量: {len(skipped_lines['format_error'])}\n")
        f.write(f"已有标签数量: {len(skipped_lines['already_tagged'])}\n")
        f.write(f"数据库错误数量: {len(skipped_lines['db_error'])}\n")
        
        f.write("\n【导入情况】\n")
        f.write(f"新增单词: {stats['added_count']}\n")
        f.write(f"已存在单词(已添加新标签): {len(existing_words)}\n")
        
        # 详细信息
        if skipped_lines['invalid']:
            f.write("\n无效单词详情:\n")
            for line_num, line in skipped_lines['invalid']:
                f.write(f"第 {line_num} 行: {line}\n")
        
        if skipped_lines['format_error']:
            f.write("\n格式错误详情:\n")
            for line_num, line, error in skipped_lines['format_error']:
                f.write(f"第 {line_num} 行: {line}\n")
                f.write(f"错误信息: {error}\n")
        
        if skipped_lines['already_tagged']:
            f.write("\n已有标签的单词:\n")
            for line_num, word in skipped_lines['already_tagged']:
                f.write(f"第 {line_num} 行: {word}\n")
        
        if skipped_lines['db_error']:
            f.write("\n数据库操作失败详情:\n")
            for line_num, word, error in skipped_lines['db_error']:
                f.write(f"第 {line_num} 行 '{word}' - 错误: {error}\n")
        
        if existing_words:
            f.write(f"\n已存在的单词(已添加新标签):\n")
            for word in existing_words:
                f.write(f"- {word}\n")

def import_wordlist_to_database(db, filepath):
    """从文件导入词表到数据库"""
    try:
        # 获取文件名作为标签
        tag_name = Path(filepath).stem
        
        # 读取并处理文件
        words = []
        total_lines = 0
        
        skipped_lines = {
            'empty': [],
            'title': [],
            'invalid': [],
            'format_error': [],
            'already_tagged': [],  # 已有该标签的词（包含行号信息）
            'db_error': [],        # 数据库错误
            'other_error': []      # 其他错误
        }
        
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            file_size = len(content.encode('utf-8'))
            char_count = len(content)
            
            file.seek(0)
            for line_num, line in enumerate(file, 1):
                total_lines += 1
                line = line.strip()
                
                if not line:
                    skipped_lines['empty'].append(line_num)
                    continue
                    
                if "Word List" in line:
                    skipped_lines['title'].append((line_num, line))
                    continue
                
                try:
                    parts = line.split()
                    if not parts:
                        skipped_lines['empty'].append(line_num)
                        continue
                        
                    word = clean_word(parts[0].lower())
                    
                    if not word or not word.isalpha():
                        skipped_lines['invalid'].append((line_num, line))
                        continue
                    
                    words.append((word, line_num))  # 保存单词和行号
                    
                except Exception as e:
                    skipped_lines['format_error'].append((line_num, line, str(e)))
                    continue
        
        if not words:
            print("未找到需要导入的有效单词")
            return False
            
        # 打印文件统计信息
        print(f"\n文件统计信息:")
        print(f"文件大小: {file_size} bytes")
        print(f"总字符数: {char_count}")
        print(f"总行数: {total_lines}")
        print(f"需要处理的单词数: {len(words)}")
        print(f"将使用标签: {tag_name}")
        
        # 导入数据库
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                tag_id = db.add_tag(tag_name)
                added_count = 0
                existing_words = []
                word_lemma_pairs = []
                
                for word, line_num in words:
                    try:
                        word_info = db.get_word_info(word)

                        if word_info:
                            # 检查单词是否已经有这个标签
                            if tag_name in word_info['tags']:
                                skipped_lines['already_tagged'].append((line_num, word))
                            else:
                                # 单词存在但没有这个标签，添加标签关联
                                existing_words.append(word)
                                word_lemma_pairs.append((word_info['lemma_id'], tag_id))
                        else:
                            # 单词不存在，添加新单词并创建标签关联
                            lemma_id = db.add_word(word)
                            if lemma_id:
                                word_lemma_pairs.append((lemma_id, tag_id))
                                added_count += 1
                            else:
                                skipped_lines['db_error'].append((line_num, word, "无法获取或创建 lemma_id"))
                    
                    except Exception as e:
                        error_msg = f"错误类型: {type(e).__name__}, 详细信息: {str(e)}"
                        skipped_lines['db_error'].append((line_num, word, error_msg))
                        continue

                # 批量添加标签关联
                valid_pairs = [(lid, tid) for lid, tid in word_lemma_pairs if lid is not None]
                if valid_pairs:
                    try:
                        conn.executemany('''
                            INSERT OR IGNORE INTO lemma_tags (lemma_id, tag_id) 
                            VALUES (?, ?)
                        ''', valid_pairs)
                    except sqlite3.Error as e:
                        print(f"标签关联插入错误: {e}")
                        raise
                
                conn.commit()
                
                # 保存导入统计信息
                stats = {
                    'added_count': added_count,
                    'existing_count': len(existing_words),
                    'file_size': file_size,
                    'char_count': char_count,
                    'total_lines': total_lines,
                    'processed_words': len(words)
                }
                
                # 保存报告
                report_file = f"{filepath}_import_report.txt"
                save_import_report(report_file, stats, skipped_lines, existing_words)
                
                print(f"\n导入完成:")
                print(f"新增单词数: {added_count}")
                print(f"已存在单词数: {len(existing_words)}")
                print(f"导入报告已保存到: {report_file}")
                
                return True
                
            except Exception as e:
                conn.rollback()
                print(f"导入过程出错: {e}")
                traceback.print_exc()
                return False

    except FileNotFoundError:
        print(f"找不到文件: {filepath}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        traceback.print_exc()
        return False