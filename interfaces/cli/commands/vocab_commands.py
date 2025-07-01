# 词汇查询命令模块
# 路径: interfaces/cli/commands/vocab_commands.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

import click

@click.group()
def vocab():
    """词汇查询和管理相关命令
    
    查询词汇频率、词汇表信息、统计数据等。
    """
    pass

@vocab.command()
@click.argument('word')
@click.option('-d', '--detailed', is_flag=True, help='显示详细信息（包含词性、字典排名等）')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text', help='输出格式')
def query(word, detailed, output_format):
    """查询词汇信息"""
    try:
        from core.engines.database.database_adapter import unified_adapter
        
        # 查询词汇频率（使用detailed参数）
        results = unified_adapter.search_words(word, detailed=detailed)
        
        if not results:
            click.echo(f"❌ 未找到包含 '{word}' 的词汇")
            return
        
        if output_format == 'json':
            import json
            if detailed:
                data = [{
                    "word": r[0], 
                    "total_frequency": r[1], 
                    "document_count": r[2],
                    "pos_primary": r[3],
                    "dictionary_rank": r[4],
                    "personal_status": r[5],
                    "definition": r[6][:100] + "..." if r[6] and len(r[6]) > 100 else r[6]
                } for r in results]
            else:
                data = [{"word": r[0], "total_frequency": r[1], "document_count": r[2]} for r in results]
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            if detailed:
                click.echo(f"🔍 包含 '{word}' 的词汇 (详细模式):")
                click.echo("=" * 60)
                for result in results[:20]:  # 限制显示前20个
                    word_text, freq, doc_count, pos_primary, dict_rank, personal_status, definition = result
                    
                    # 格式化词性和排名信息
                    pos_info = f"({pos_primary})" if pos_primary else "(未知词性)"
                    rank_info = f"字典排名:{dict_rank}" if dict_rank else "未在字典中"
                    status_icon = {'new': '🆕', 'learn': '📚', 'know': '✅', 'master': '🏆'}.get(personal_status, '⚪')
                    status_info = f"{status_icon}{personal_status}" if personal_status else "⚪未设置"
                    
                    click.echo(f"📝 {word_text} {pos_info}")
                    click.echo(f"   📊 频率: {freq}, 文档: {doc_count}个")
                    click.echo(f"   📚 {rank_info} | 学习状态: {status_info}")
                    
                    if definition:
                        def_preview = definition[:80] + "..." if len(definition) > 80 else definition
                        click.echo(f"   💡 定义: {def_preview}")
                    
                    click.echo()  # 空行分隔
            else:
                click.echo(f"🔍 包含 '{word}' 的词汇:")
                click.echo("-" * 50)
                for result in results[:20]:  # 限制显示前20个
                    word_text, freq, doc_count = result
                    click.echo(f"📝 {word_text}: 频率 {freq}, 出现在 {doc_count} 个文档")
            
            if len(results) > 20:
                click.echo(f"... 还有 {len(results) - 20} 个相关词汇")
                click.echo("💡 使用 --detailed 查看更多信息")
                
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