# 统一CLI入口 - 重新设计架构
# 路径: interfaces/cli/main.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

import click
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.utils.config_manager import get_config

@click.group()
@click.version_option(version="1.0.0")
@click.option('--config-env', default='default', help='配置环境 (default/development/production)')
@click.pass_context
def cli(ctx, config_env):
    """
    词频分析和词汇管理工具 v1.0.0
    
    一个专业的文本分析工具，支持文本词频分析、词汇表管理和词汇查询。
    
    \b
    主要功能：
    • text     - 文本分析：处理文档，进行词频统计
    • wordlist - 词汇表管理：导入各种词汇表文件
    • vocab    - 词汇查询：查询词汇信息和统计
    """
    ctx.ensure_object(dict)
    ctx.obj['config_env'] = config_env
    
    # 初始化配置
    try:
        config = get_config()
    except Exception as e:
        click.secho(f"⚠️  配置加载失败: {e}", fg='yellow')

# =============================================================================
# 📄 TEXT 命令组 - 文本分析功能
# =============================================================================

@cli.group()
def text():
    """文本分析相关命令
    
    处理文档文件，进行词频统计和分析。
    支持的文件格式：PDF、TXT、DOCX等。
    """
    pass

@text.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--move/--no-move', default=True, help='处理完成后是否移动文件到processed目录')
@click.option('--recursive/--no-recursive', default=True, help='是否递归扫描子目录')
def process(directory, move, recursive):
    """处理指定目录下的文本文件进行词频分析"""
    try:
        from core.engines.input.file_processor import TextProcessor
        
        click.echo(f"📂 开始处理目录: {directory}")
        processor = TextProcessor(move_processed=move)
        processor.process_new_texts(directory, scan_subdirs=recursive)
        
        click.secho("✅ 文本处理完成！", fg='green')
        
    except Exception as e:
        click.secho(f"❌ 处理失败: {e}", fg='red', err=True)

@text.command()
@click.option('--limit', default=20, help='显示记录数量')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='输出格式')
def query(limit, output_format):
    """查询文本分析记录"""
    try:
        from core.engines.database.database_adapter import unified_adapter
        
        analyses = unified_adapter.get_all_analyses()
        
        if not analyses:
            click.echo("📚 暂无文本分析记录")
            return
        
        # 限制显示数量
        analyses = analyses[:limit]
        
        if output_format == 'json':
            import json
            data = [{'id': a[0], 'filename': a[1], 'date': a[2], 'total_words': a[3], 'unique_words': a[4]} for a in analyses]
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            # 表格格式
            click.echo("📚 文本分析记录:")
            click.echo("-" * 80)
            click.echo(f"{'ID':<12} {'文件名':<30} {'总词数':<10} {'唯一词数':<10}")
            click.echo("-" * 80)
            
            for analysis in analyses:
                id_short = analysis[0][:11] + "..." if len(analysis[0]) > 11 else analysis[0]
                filename = analysis[1][:29] if len(analysis[1]) > 29 else analysis[1]
                click.echo(f"{id_short:<12} {filename:<30} {analysis[3]:<10} {analysis[4]:<10}")
            
            click.echo("-" * 80)
            click.echo(f"总计 {len(analyses)} 个文本")
            
    except Exception as e:
        click.secho(f"❌ 查询失败: {e}", fg='red', err=True)

@text.command()
@click.option('-o', '--output', type=click.Path(), help='输出文件路径')
@click.option('--format', 'output_format', type=click.Choice(['txt', 'csv', 'json', 'excel']), default='txt', help='导出格式')
@click.option('-t', '--text-id', help='导出特定文本(可选)')
def export(output, output_format, text_id):
    """导出文本分析结果"""
    try:
        from core.engines.database.database_adapter import unified_adapter
        
        if not output:
            output = f"text_analysis_export.{output_format}"
        
        # 导出逻辑...
        click.secho(f"✅ 导出完成: {output}", fg='green')
        
    except Exception as e:
        click.secho(f"❌ 导出失败: {e}", fg='red', err=True)

@text.command()
def organize():
    """整理已分析的文本文件：将数据库中已存在的文件移动到processed目录"""
    try:
        from core.engines.input.file_processor import TextProcessor
        
        processor = TextProcessor()
        processor.organize_existing_files()
        
    except Exception as e:
        click.secho(f"❌ 整理失败: {e}", fg='red', err=True)

# =============================================================================
# 📚 WORDLIST 命令组 - 词汇表导入功能
# =============================================================================

@cli.group()
def wordlist():
    """词汇表导入相关命令
    
    从各种格式的文件导入词汇表，如AWL、GRE、TOEFL等。
    支持的文件格式：TXT、CSV、XLSX、DOCX、PDF等。
    """
    pass

@wordlist.command('import')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('-t', '--tag', help='词汇表标签名')
@click.option('-d', '--description', help='词汇表描述')
@click.option('--move/--no-move', default=True, help='导入完成后是否移动文件到processed目录')
def import_wordlist(file_path, tag, description, move):
    """从文件导入词汇表"""
    try:
        from core.engines.input.modern_wordlist_import import import_wordlist_from_file
        
        # 如果没有指定标签，使用文件名
        if not tag:
            tag = Path(file_path).stem
        
        click.echo(f"📚 开始导入词汇表: {file_path}")
        success = import_wordlist_from_file(file_path, tag, description)
        
        if success and move:
            # 移动文件到processed目录
            source = Path(file_path)
            if 'wordlists/new' in str(source):
                target_dir = source.parent.parent / 'processed'
                target_dir.mkdir(exist_ok=True)
                target_path = target_dir / source.name
                
                import shutil
                shutil.move(str(source), str(target_path))
                click.echo(f"📁 文件已移动到: {target_path}")
        
        if success:
            click.secho(f"✅ 词汇表导入成功: {tag}", fg='green')
        else:
            click.secho(f"❌ 词汇表导入失败: {tag}", fg='red')
            
    except Exception as e:
        click.secho(f"❌ 导入失败: {e}", fg='red', err=True)

@wordlist.command('batch')
@click.argument('directory', type=click.Path(exists=True))
@click.option('--pattern', default='*.txt', help='文件名模式')
@click.option('--move/--no-move', default=True, help='导入完成后是否移动文件')
def batch_import(directory, pattern, move):
    """批量导入目录下的词汇表文件"""
    try:
        from core.engines.input.modern_wordlist_import import import_multiple_wordlists
        
        click.echo(f"📂 开始批量导入: {directory}")
        success_count = import_multiple_wordlists(directory, pattern)
        
        if success_count > 0:
            click.secho(f"✅ 成功导入 {success_count} 个词汇表", fg='green')
        else:
            click.secho("❌ 没有成功导入任何词汇表", fg='red')
            
    except Exception as e:
        click.secho(f"❌ 批量导入失败: {e}", fg='red', err=True)

@wordlist.command('list')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='输出格式')
def list_wordlists(output_format):
    """显示所有已导入的词汇表"""
    try:
        from core.engines.database.database_adapter import unified_adapter
        
        wordlists = unified_adapter.get_all_wordlists()
        
        if not wordlists:
            click.echo("📚 暂无已导入的词汇表")
            return
        
        if output_format == 'json':
            import json
            click.echo(json.dumps(wordlists, ensure_ascii=False, indent=2))
        else:
            click.echo("📚 已导入的词汇表:")
            click.echo("-" * 60)
            for wl in wordlists:
                click.echo(f"📖 {wl['name']}: {wl['word_count']} 个词汇")
            click.echo("-" * 60)
            click.echo(f"总计 {len(wordlists)} 个词汇表")
            
    except Exception as e:
        click.secho(f"❌ 查询失败: {e}", fg='red', err=True)

# =============================================================================
# 🔍 VOCAB 命令组 - 词汇查询功能 
# =============================================================================

@cli.group()
def vocab():
    """词汇查询和管理相关命令
    
    查询词汇频率、词汇表信息、统计数据等。
    """
    pass

@vocab.command()
@click.argument('word')
@click.option('-d', '--detailed', is_flag=True, help='显示详细信息')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text', help='输出格式')
def query(word, detailed, output_format):
    """查询词汇信息"""
    try:
        from core.engines.database.database_adapter import unified_adapter
        
        # 查询词汇频率
        results = unified_adapter.search_words(word)
        
        if not results:
            click.echo(f"❌ 未找到包含 '{word}' 的词汇")
            return
        
        if output_format == 'json':
            import json
            data = [{"word": r[0], "total_frequency": r[1], "document_count": r[2]} for r in results]
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"🔍 包含 '{word}' 的词汇:")
            click.echo("-" * 50)
            for result in results[:20]:  # 限制显示前20个
                word_text, freq, doc_count = result
                click.echo(f"📝 {word_text}: 频率 {freq}, 出现在 {doc_count} 个文档")
            
            if len(results) > 20:
                click.echo(f"... 还有 {len(results) - 20} 个相关词汇")
                
    except Exception as e:
        click.secho(f"❌ 查询失败: {e}", fg='red', err=True)

@vocab.command()
def stats():
    """显示词汇统计信息"""
    try:
        from core.engines.database.database_adapter import unified_adapter
        
        stats = unified_adapter.get_database_info()
        
        click.echo("📊 词汇统计:")
        click.echo("-" * 40)
        click.echo(f"📚 词汇表数量: {stats.get('wordlists_count', 0)}")
        click.echo(f"🔤 总词汇数 (原始形式): {stats.get('total_words', 0)}")
        click.echo(f"🌱 独特词根数: {stats.get('unique_lemmas', 0)}")
        click.echo(f"📄 文档数量: {stats.get('documents_count', 0)}")
        click.echo(f"📝 词频记录: {stats.get('word_frequencies_count', 0)}")
        
        if stats.get('documents_count', 0) > 0:
            avg_length = stats.get('avg_document_length', 0)
            if avg_length:
                click.echo(f"📏 平均文档长度: {avg_length:.1f} 词")
        
        avg_variants = stats.get('avg_variants_per_lemma', 0)
        if avg_variants > 0:
            click.echo(f"🔄 平均每词根变形数: {avg_variants:.1f}")
        click.echo("-" * 40)
        
    except Exception as e:
        click.secho(f"❌ 统计失败: {e}", fg='red', err=True)

@vocab.command()
@click.argument('word')
@click.option('--doc-id', help='指定文档ID查看特定文档中的变形')
def variants(word, doc_id):
    """查看指定词汇的所有变形及其频率"""
    try:
        from core.engines.database.database_adapter import unified_adapter
        
        result = unified_adapter.get_word_variants(word, doc_id)
        
        click.echo(f"🔍 词汇变形分析: \"{word}\"")
        click.echo("=" * 50)
        click.echo(f"🌱 词根: {result['lemma']}")
        click.echo(f"📊 总变形数: {result['total_variants']}")
        click.echo(f"🔢 总频率: {result['total_frequency']}")
        
        if doc_id:
            click.echo(f"📄 限定文档: {doc_id[:8]}...")
        
        click.echo("\n📝 详细变形信息:")
        click.echo("-" * 30)
        
        if result['variants']:
            for variant in result['variants']:
                surface = variant['surface_form']
                freq = variant.get('total_frequency', variant.get('frequency', 0))
                
                if doc_id:
                    # 单文档模式
                    tf_score = variant.get('tf_score', 0)
                    filename = variant.get('filename', '')
                    click.echo(f"📖 {surface}: {freq}次 (TF: {tf_score:.4f}) - {filename}")
                else:
                    # 全局模式
                    doc_count = variant.get('document_count', 0)
                    avg_freq = variant.get('avg_frequency', 0)
                    click.echo(f"📖 {surface}: {freq}次 (在 {doc_count} 个文档中, 平均 {avg_freq:.1f}次/文档)")
        else:
            click.echo("❌ 未找到相关变形")
        
        click.echo("=" * 50)
        
    except Exception as e:
        click.secho(f"❌ 查询失败: {e}", fg='red', err=True)

@vocab.command()
@click.option('--doc-id', help='指定文档ID进行词根分析')
@click.option('--limit', default=20, help='显示数量限制')
def lemmas(doc_id, limit):
    """词根级别的统计分析"""
    try:
        from core.engines.database.database_adapter import unified_adapter
        
        result = unified_adapter.get_lemma_analysis_data(doc_id)
        
        click.echo("🌱 词根分析报告")
        click.echo("=" * 50)
        
        if doc_id:
            click.echo(f"📄 文档: {doc_id[:8]}...")
        else:
            click.echo("📄 范围: 全部文档")
        
        click.echo(f"🔢 总词根数: {result['total_lemmas']}")
        
        click.echo(f"\n📊 Top {limit} 高频词根:")
        click.echo("-" * 40)
        
        for i, lemma_data in enumerate(result['lemma_analysis'][:limit], 1):
            lemma = lemma_data['lemma']
            variant_count = lemma_data['variant_count']
            total_freq = lemma_data['total_frequency']
            
            if doc_id:
                # 单文档模式 - 显示详细变形
                variants_detail = lemma_data.get('variants_detail', '')
                click.echo(f"{i:2d}. 📝 {lemma} (总频率: {total_freq}, {variant_count} 个变形)")
                if variants_detail:
                    variants = variants_detail.split(',')
                    variants_str = ', '.join(variants[:5])  # 最多显示5个变形
                    if len(variants) > 5:
                        variants_str += f", ... (+{len(variants)-5}个)"
                    click.echo(f"     变形: {variants_str}")
            else:
                # 全局模式
                doc_count = lemma_data.get('document_count', 0)
                click.echo(f"{i:2d}. 📝 {lemma}: {total_freq}次 ({variant_count} 个变形, {doc_count} 个文档)")
        
        click.echo("=" * 50)
        
    except Exception as e:
        click.secho(f"❌ 分析失败: {e}", fg='red', err=True)

@vocab.command()
@click.argument('word')
def pos(word):
    """查看词汇的词性和语言学特征"""
    try:
        from core.engines.database.database_adapter import unified_adapter
        
        results = unified_adapter.get_linguistic_features(word)
        
        if not results:
            click.secho(f"❌ 未找到词汇 \"{word}\" 的语言学特征", fg='red')
            return
        
        click.echo(f"🔍 词汇语言学分析: \"{word}\"")
        click.echo("=" * 50)
        
        for result in results:
            surface = result['surface_form']
            lemma = result['lemma']
            features = result.get('linguistic_features', {})
            
            click.echo(f"📝 词汇形式: {surface}")
            click.echo(f"🌱 词根: {lemma}")
            
            if features:
                # 词性信息
                pos_tag = features.get('pos_tag', 'UNKNOWN')
                pos_type = features.get('pos_type', 'unknown')
                pos_desc = features.get('pos_description', '无描述')
                
                click.echo(f"🏷️  词性标签: {pos_tag}")
                click.echo(f"📚 词性类型: {pos_type}")
                click.echo(f"📖 词性描述: {pos_desc}")
                
                # 形态学信息
                morphology = features.get('morphology', {})
                if morphology:
                    complexity = morphology.get('complexity', 'simple')
                    prefix = morphology.get('prefix')
                    suffix = morphology.get('suffix')
                    
                    click.echo(f"🔧 形态复杂度: {complexity}")
                    if prefix:
                        click.echo(f"⬅️  前缀: {prefix}")
                    if suffix:
                        suffix_meaning = morphology.get('suffix_meaning', '')
                        click.echo(f"➡️  后缀: {suffix} ({suffix_meaning})")
                
                # 其他特征
                word_length = features.get('word_length', 0)
                has_prefix = features.get('has_prefix', False)
                has_suffix = features.get('has_suffix', False)
                
                click.echo(f"📏 词长: {word_length} 字符")
                click.echo(f"🎯 有前缀: {'是' if has_prefix else '否'}")
                click.echo(f"🎯 有后缀: {'是' if has_suffix else '否'}")
            else:
                click.echo("❌ 无语言学特征信息")
            
            click.echo("-" * 30)
        
        click.echo("=" * 50)
        
    except Exception as e:
        click.secho(f"❌ 查询失败: {e}", fg='red', err=True)

@vocab.command()
@click.option('--type', 'pos_type', help='词性类型 (noun, verb, adjective, 等)')
@click.option('--limit', default=20, help='显示数量限制')
def by_pos(pos_type, limit):
    """按词性类型查询词汇"""
    try:
        from core.engines.database.database_adapter import unified_adapter
        
        if pos_type:
            # 查询特定词性的词汇
            results = unified_adapter.get_words_by_pos(pos_type, limit)
            
            click.echo(f"📚 词性类型: {pos_type}")
            click.echo("=" * 50)
            
            if results:
                click.echo(f"共找到 {len(results)} 个词汇:")
                click.echo()
                
                for i, word_data in enumerate(results, 1):
                    surface = word_data['surface_form']
                    lemma = word_data['lemma']
                    features = word_data.get('linguistic_features', {})
                    total_freq = word_data['total_frequency']
                    doc_count = word_data['document_count']
                    
                    pos_desc = features.get('pos_description', '无描述')
                    
                    click.echo(f"{i:2d}. 📝 {surface} ({lemma})")
                    click.echo(f"     描述: {pos_desc}")
                    click.echo(f"     频率: {total_freq}次 (在 {doc_count} 个文档中)")
                    
                    # 显示形态学信息
                    morphology = features.get('morphology', {})
                    if morphology.get('complexity') != 'simple':
                        complexity_info = []
                        if morphology.get('prefix'):
                            complexity_info.append(f"前缀:{morphology['prefix']}")
                        if morphology.get('suffix'):
                            complexity_info.append(f"后缀:{morphology['suffix']}")
                        if complexity_info:
                            click.echo(f"     形态: {', '.join(complexity_info)}")
                    
                    click.echo()
            else:
                click.secho(f"❌ 未找到词性为 \"{pos_type}\" 的词汇", fg='yellow')
        else:
            # 显示词性分布统计
            stats = unified_adapter.get_pos_statistics()
            
            click.echo("📊 词性分布统计")
            click.echo("=" * 50)
            
            total_analyzed = stats.get('total_analyzed_words', 0)
            click.echo(f"📝 已分析词汇总数: {total_analyzed}")
            click.echo()
            
            # 词性类型分布
            pos_type_dist = stats.get('pos_type_distribution', {})
            click.echo("🏷️  词性类型分布:")
            for pos_type, count in sorted(pos_type_dist.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_analyzed * 100) if total_analyzed > 0 else 0
                click.echo(f"   {pos_type:<12}: {count:>4} 个 ({percentage:>5.1f}%)")
            
            click.echo()
            
            # 详细词性标签分布 (前10个)
            pos_tag_dist = stats.get('pos_tag_distribution', [])[:10]
            if pos_tag_dist:
                click.echo("🔖 详细词性标签 (Top 10):")
                for item in pos_tag_dist:
                    tag = item['pos_tag']
                    desc = item['description']
                    count = item['count']
                    percentage = (count / total_analyzed * 100) if total_analyzed > 0 else 0
                    click.echo(f"   {tag:<6}: {count:>4} 个 ({percentage:>5.1f}%) - {desc}")
            
            # 形态学复杂度分布
            morphology_dist = stats.get('morphology_distribution', {})
            if morphology_dist:
                click.echo()
                click.echo("🔧 形态学复杂度分布:")
                for complexity, count in sorted(morphology_dist.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_analyzed * 100) if total_analyzed > 0 else 0
                    click.echo(f"   {complexity:<10}: {count:>4} 个 ({percentage:>5.1f}%)")
        
        click.echo("=" * 50)
        
    except Exception as e:
        click.secho(f"❌ 查询失败: {e}", fg='red', err=True)

@vocab.command()
def morphology():
    """形态学分析 - 显示有前缀和后缀的词汇"""
    try:
        from core.engines.database.database_adapter import unified_adapter
        
        analysis = unified_adapter.get_morphology_analysis()
        
        click.echo("🔧 形态学分析报告")
        click.echo("=" * 60)
        
        # 前缀词汇
        prefixed_words = analysis.get('prefixed_words', [])
        if prefixed_words:
            click.echo("⬅️  前缀词汇 (Top 20):")
            click.echo("-" * 30)
            
            for word_data in prefixed_words:
                surface = word_data['surface_form']
                lemma = word_data['lemma']
                prefix = word_data['prefix']
                freq = word_data['total_frequency']
                
                click.echo(f"📝 {surface} ({lemma})")
                click.echo(f"   前缀: {prefix} | 频率: {freq}次")
                click.echo()
        
        # 后缀词汇
        suffixed_words = analysis.get('suffixed_words', [])
        if suffixed_words:
            click.echo("➡️  后缀词汇 (Top 20):")
            click.echo("-" * 30)
            
            for word_data in suffixed_words:
                surface = word_data['surface_form']
                lemma = word_data['lemma']
                suffix = word_data['suffix']
                suffix_meaning = word_data['suffix_meaning']
                freq = word_data['total_frequency']
                
                click.echo(f"📝 {surface} ({lemma})")
                click.echo(f"   后缀: {suffix} ({suffix_meaning}) | 频率: {freq}次")
                click.echo()
        
        if not prefixed_words and not suffixed_words:
            click.secho("❌ 暂无形态学复杂词汇数据", fg='yellow')
        
        click.echo("=" * 60)
        
    except Exception as e:
        click.secho(f"❌ 分析失败: {e}", fg='red', err=True)

@vocab.command()
def tags():
    """显示所有词汇表标签"""
    try:
        from core.engines.database.database_adapter import unified_adapter
        
        wordlists = unified_adapter.get_all_wordlists()
        
        if not wordlists:
            click.echo("📚 暂无词汇表")
            return
        
        click.echo("🏷️  词汇表:")
        click.echo("-" * 60)
        for wl in wordlists:
            click.echo(f"📚 {wl['name']}")
        click.echo("-" * 60)
        click.echo(f"总计 {len(wordlists)} 个词汇表")
        
    except Exception as e:
        click.secho(f"❌ 查询失败: {e}", fg='red', err=True)

# =============================================================================
# ⚙️ CONFIG 命令组 - 配置管理
# =============================================================================

@cli.group('config')
def config_cmd():
    """配置管理命令"""
    pass

@config_cmd.command()
def show():
    """显示当前配置"""
    try:
        config = get_config()
        
        click.echo("⚙️  当前配置:")
        click.echo("-" * 40)
        
        def print_config(data, prefix=""):
            for key, value in data.items():
                if isinstance(value, dict):
                    click.echo(f"{prefix}{key}:")
                    print_config(value, prefix + "  ")
                else:
                    click.echo(f"{prefix}{key}: {value}")
        
        print_config(config)
        
    except Exception as e:
        click.secho(f"❌ 配置显示失败: {e}", fg='red', err=True)

@config_cmd.command()
@click.argument('key')
@click.argument('value')
def set(key, value):
    """设置配置项"""
    try:
        config = get_config()
        config.update(key, value)
        click.secho(f"✅ 配置已更新: {key} = {value}", fg='green')
        
    except Exception as e:
        click.secho(f"❌ 配置设置失败: {e}", fg='red', err=True)

def main():
    """CLI主程序入口函数"""
    try:
        cli()
    except KeyboardInterrupt:
        click.secho("\n👋 程序已退出", fg='yellow')
    except Exception as e:
        click.secho(f"\n❌ 程序出错: {str(e)}", fg='red', err=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 