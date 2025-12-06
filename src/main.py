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


@cli.command(name='list')
@click.pass_context
def list_cmd(ctx):
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
@click.option('-i', '--inputs', '--input', 'inputs', required=True, help='输入数据（文本、文件路径、JSON 或 YAML）')
@click.option('--image', multiple=True, help='图像输入（可多次使用）')
@click.option('-o', '--output', help='输出文件路径（默认：<input-basename>-output.<ext>）')
@click.option('--format', 'format_type', default=None,
              type=click.Choice(['json', 'txt', 'yaml', 'md', 'markdown'], case_sensitive=False),
              help='输出格式（默认：从输出内容自动判断，无法判断时为 txt）')
@click.option('--save-images/--no-save-images', default=False,
              help='保存原始图像到本地（用于离线查看/人工核验，默认：否）')
@click.option('--cache/--no-cache', default=None,
              help='覆盖配置文件的缓存设置（用于临时控制缓存行为）')
@click.pass_context
def run(ctx, agent_name, inputs, image, output, format_type, save_images, cache):
    """
    运行 Agent

    AGENT_NAME: 要执行的 agent 名称

    示例:

    \b
    # JSON 输入
    python src/main.py run agent_name -i '{"text": "hello"}'

    \b
    # YAML 输入
    python src/main.py run agent_name -i 'text: hello\\ncontext: world'

    \b
    # JSON 文件输入
    python src/main.py run agent_name -i input.json

    \b
    # YAML 文件输入
    python src/main.py run agent_name --input input.yaml

    \b
    # 图像输入
    python src/main.py run agent_name --input '{}' --image photo.jpg --image photo2.jpg

    \b
    # 保存原始图像（用于离线查看）
    python src/main.py run image_captioner -i '{}' --image url.jpg --save-images

    \b
    # 临时禁用缓存
    python src/main.py run image_captioner -i input.json --no-cache

    \b
    # 指定输出格式
    python src/main.py run agent_name -i input.yaml --format yaml -o output.yaml
    python src/main.py run agent_name -i input.json --format markdown -o report.md
    """
    images = list(image) if image else None

    # 如果未指定格式，传递 None，让 run_command 自动判断
    exit_code = ctx.obj['commands'].run_command(
        agent_name=agent_name,
        inputs=inputs,
        images=images,
        output_file=output,
        format_type=format_type.lower() if format_type else None,
        save_images=save_images,
        cache_override=cache
    )

    sys.exit(exit_code)


def main():
    """主函数"""
    cli()


if __name__ == '__main__':
    main()
