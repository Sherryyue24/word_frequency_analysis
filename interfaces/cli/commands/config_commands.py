# 配置管理命令模块
# 路径: interfaces/cli/commands/config_commands.py
# 项目名称: Word Frequency Analysis
# 作者: Sherryyue

import click

@click.group('config')
def config_cmd():
    """配置管理命令"""
    pass

@config_cmd.command()
def show():
    """显示当前配置"""
    try:
        from core.utils.config_manager import get_config
        
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
        from core.utils.config_manager import get_config
        
        config = get_config()
        config.update(key, value)
        click.secho(f"✅ 配置已更新: {key} = {value}", fg='green')
        
    except Exception as e:
        click.secho(f"❌ 配置设置失败: {e}", fg='red', err=True) 