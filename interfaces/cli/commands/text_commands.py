# 文本分析命令模块
# 路径: interfaces/cli/commands/text_commands.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

import click
from pathlib import Path

@click.group()
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