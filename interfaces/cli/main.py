# 统一CLI入口 - 模块化重构
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
    • personal - 个人学习：管理词汇学习状态
    • config   - 配置管理：系统配置设置
    """
    ctx.ensure_object(dict)
    ctx.obj['config_env'] = config_env
    
    # 初始化配置
    try:
        config = get_config()
    except Exception as e:
        click.secho(f"⚠️  配置加载失败: {e}", fg='yellow')

# 导入并注册各个命令组
def register_commands():
    """注册所有命令组到主CLI"""
    
    # 导入各个命令模块
    from .commands.text_commands import text
    from .commands.wordlist_commands import wordlist  
    from .commands.vocab_commands import vocab
    from .commands.personal_commands import personal
    from .commands.config_commands import config_cmd
    
    # 注册命令组
    cli.add_command(text)
    cli.add_command(wordlist)
    cli.add_command(vocab)
    cli.add_command(personal)
    cli.add_command(config_cmd)

def main():
    """CLI主程序入口函数"""
    try:
        # 注册所有命令
        register_commands()
        
        # 启动CLI
        cli()
    except KeyboardInterrupt:
        click.secho("\n👋 程序已退出", fg='yellow')
    except Exception as e:
        click.secho(f"\n❌ 程序出错: {str(e)}", fg='red', err=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 