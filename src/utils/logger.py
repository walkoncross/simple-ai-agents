"""
日志工具

初始化和配置日志系统
"""
import sys
from pathlib import Path
from loguru import logger


def setup_logger(level: str = "INFO", log_file: str = "./logs/agent.log",
                log_format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"):
    """
    设置日志系统

    Args:
        level: 日志级别
        log_file: 日志文件路径
        log_format: 日志格式
    """
    # 移除默认的 handler
    logger.remove()

    # 添加控制台输出
    logger.add(
        sys.stderr,
        format=log_format,
        level=level,
        colorize=True
    )

    # 添加文件输出
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        format=log_format,
        level=level,
        rotation="10 MB",  # 日志文件达到 10MB 时轮转
        retention="7 days",  # 保留 7 天的日志
        compression="zip"  # 压缩旧日志
    )

    logger.info(f"日志系统已初始化，级别: {level}")
