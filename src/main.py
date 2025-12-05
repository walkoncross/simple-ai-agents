"""
Simple AI Agents - 主程序入口

一个轻量级的 AI Agent 工厂框架
"""
import sys
import click
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger
from src.cli.commands import Commands


@click.group()
@click.option('--config', '-c', default=None, help='配置文件路径（默认：config.local.yaml 或 config.yaml）')
@click.pass_context
def cli(ctx, config):
    """Simple AI Agents - AI Agent 工厂框架"""
    # 确定配置文件路径
    if config is None:
        # 未指定配置文件，按优先级查找
        if Path('config.local.yaml').exists():
            config = 'config.local.yaml'
            click.echo(f"使用本地配置: {config}")
        else:
            config = 'config.yaml'

    # 加载配置
    try:
        config_loader = ConfigLoader(config)
        config_obj = config_loader.load()

        # 初始化日志
        setup_logger(
            level=config_obj.logging.level,
            log_file=config_obj.logging.file,
            log_format=config_obj.logging.format
        )

        # 保存到上下文
        ctx.ensure_object(dict)
        ctx.obj['config_loader'] = config_loader
        ctx.obj['commands'] = Commands(config_loader)

    except Exception as e:
        click.echo(f"❌ 加载配置失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def list(ctx):
    """列举所有 models 和 agents"""
    ctx.obj['commands'].list_command()


@cli.command()
@click.pass_context
def stat(ctx):
    """统计 models 和 agents"""
    ctx.obj['commands'].stat_command()


@cli.command()
@click.argument('name')
@click.pass_context
def info(ctx, name):
    """
    打印 model 或 agent 的详细信息

    NAME: model 或 agent 名称
    """
    ctx.obj['commands'].info_command(name)


@cli.command()
@click.argument('agent_name')
@click.option('-i', '--inputs', help='输入数据（文本、文件路径或 JSON）')
@click.option('--image', multiple=True, help='图像输入（可多次使用）')
@click.option('-o', '--output', help='输出文件路径')
@click.option('--format', 'format_type', default='json',
              type=click.Choice(['json', 'txt', 'yaml'], case_sensitive=False),
              help='输出格式')
@click.pass_context
def run(ctx, agent_name, inputs, image, output, format_type):
    """
    运行 Agent

    AGENT_NAME: 要执行的 agent 名称

    示例:

    \b
    # 文本输入
    python src/main.py run agent_name -i '{"text": "hello"}'

    \b
    # 文件输入
    python src/main.py run agent_name -i input.json

    \b
    # 图像输入
    python src/main.py run agent_name --image photo.jpg --image photo2.jpg

    \b
    # 指定输出格式
    python src/main.py run agent_name -i input.json --format yaml -o output.yaml
    """
    images = list(image) if image else None

    exit_code = ctx.obj['commands'].run_command(
        agent_name=agent_name,
        inputs=inputs,
        images=images,
        output_file=output,
        format_type=format_type.lower()
    )

    sys.exit(exit_code)


def main():
    """主函数"""
    cli(obj={})


if __name__ == '__main__':
    main()
