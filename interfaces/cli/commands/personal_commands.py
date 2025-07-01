# 个人学习状态管理命令模块
# 路径: interfaces/cli/commands/personal_commands.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

import click
from pathlib import Path

@click.group()
def personal():
    """个人词汇学习状态管理
    
    管理个人对词汇的学习状态：new/learn/know/master
    """
    pass

@personal.command('set')
@click.argument('word')
@click.argument('status', type=click.Choice(['new', 'learn', 'know', 'master']))
def set_status(word, status):
    """设置单个词汇的学习状态"""
    try:
        from core.engines.vocabulary.personal_status_manager import PersonalStatusManager
        
        manager = PersonalStatusManager()
        success = manager.set_word_status(word, status)
        
        if success:
            click.secho(f"✅ 词汇状态已更新: {word} -> {status}", fg='green')
        else:
            click.secho(f"❌ 更新失败: {word}", fg='red')
            
    except Exception as e:
        click.secho(f"❌ 设置状态失败: {e}", fg='red', err=True)

@personal.command('stats')
def personal_stats():
    """显示个人词汇状态统计"""
    try:
        from core.engines.vocabulary.personal_status_manager import PersonalStatusManager
        
        manager = PersonalStatusManager()
        stats = manager.get_status_statistics()
        
        if not stats:
            click.echo("📚 暂无个人词汇记录")
            return
        
        click.echo("👤 个人词汇状态统计:")
        click.echo(f"   总词汇数: {stats['total']}")
        click.echo(f"   字典匹配: {stats['dictionary_matched']}")
        click.echo("   学习状态分布:")
        
        total_status = sum(stats[status] for status in ['new', 'learn', 'know', 'master'])
        for status in ['new', 'learn', 'know', 'master']:
            count = stats[status]
            percentage = count / total_status * 100 if total_status > 0 else 0
            status_icon = {'new': '🆕', 'learn': '📚', 'know': '✅', 'master': '🏆'}[status]
            click.echo(f"     {status_icon} {status}: {count} ({percentage:.1f}%)")
        
    except Exception as e:
        click.secho(f"❌ 获取统计信息失败: {e}", fg='red', err=True)

@personal.command('analyze')
@click.argument('document_id')
def analyze_difficulty(document_id):
    """分析文档的个人难度情况"""
    try:
        from core.engines.vocabulary.personal_status_manager import PersonalStatusManager
        
        manager = PersonalStatusManager()
        analysis = manager.analyze_document_difficulty(document_id)
        
        if not analysis:
            click.echo("❌ 未找到文档或分析失败")
            return
        
        click.echo(f"📊 文档难度分析 (ID: {document_id[:8]}...):")
        click.echo(f"   总词汇实例: {analysis['total_word_instances']}")
        click.echo(f"   整体难度评分: {analysis['overall_difficulty_score']}/100")
        
        click.echo("   状态分布:")
        for status, percentage in analysis['difficulty_percentage'].items():
            status_icon = {'new': '🆕', 'learn': '📚', 'know': '✅', 'master': '🏆'}[status]
            click.echo(f"     {status_icon} {status}: {percentage}%")
        
        if analysis['recommended_words']:
            click.echo("   推荐重点学习词汇 (高频+未掌握):")
            for word in analysis['recommended_words'][:10]:
                click.echo(f"     • {word['word']} (出现{word['frequency']}次)")
        
    except Exception as e:
        click.secho(f"❌ 分析失败: {e}", fg='red', err=True)

@personal.command('import')
@click.argument('vocab_file', type=click.Path(exists=True))
@click.option('--format', 'file_format', default='auto', 
              type=click.Choice(['auto', 'csv', 'txt', 'json']),
              help='文件格式 (auto=自动检测)')
@click.option('--default-status', default='new',
              type=click.Choice(['new', 'learn', 'know', 'master']),
              help='默认学习状态')
def import_personal_vocab(vocab_file, file_format, default_status):
    """导入个人词汇表和学习状态"""
    try:
        from core.engines.input.personal_wordlist_import import import_personal_wordlist
        
        click.echo(f"📥 开始导入个人词汇表: {vocab_file}")
        stats = import_personal_wordlist(
            file_path=vocab_file,
            file_format=file_format,
            default_status=default_status
        )
        
        # 导入结果会在导入函数中自动显示详细报告
        if stats['successfully_imported'] > 0:
            click.secho(f"✅ 个人词汇表导入完成! 成功导入 {stats['successfully_imported']} 个词汇", fg='green')
        else:
            click.secho("❌ 个人词汇表导入失败，没有词汇被成功导入", fg='red')
        
    except Exception as e:
        click.secho(f"❌ 个人词汇表导入失败: {e}", fg='red', err=True)

@personal.command('export')
@click.argument('output_file', type=click.Path())
@click.option('--format', 'file_format', default='csv',
              type=click.Choice(['csv', 'txt', 'json']),
              help='导出格式')
@click.option('--status', 'status_filter', multiple=True,
              type=click.Choice(['new', 'learn', 'know', 'master']),
              help='只导出指定状态的词汇 (可多选)')
def export_personal_vocab(output_file, file_format, status_filter):
    """导出个人词汇表"""
    try:
        from core.engines.input.personal_wordlist_import import export_personal_wordlist
        
        # 处理状态过滤器
        status_list = list(status_filter) if status_filter else None
        
        click.echo(f"📤 开始导出个人词汇表: {output_file}")
        success = export_personal_wordlist(
            output_path=output_file,
            file_format=file_format,
            status_filter=status_list
        )
        
        if success:
            click.secho(f"✅ 个人词汇表导出成功: {output_file}", fg='green')
        else:
            click.secho("❌ 个人词汇表导出失败", fg='red')
        
    except Exception as e:
        click.secho(f"❌ 个人词汇表导出失败: {e}", fg='red', err=True) 