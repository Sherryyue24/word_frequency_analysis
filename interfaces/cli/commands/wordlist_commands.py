# 词汇表管理命令模块
# 路径: interfaces/cli/commands/wordlist_commands.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

import click
from pathlib import Path

@click.group()
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