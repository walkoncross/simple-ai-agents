"""
格式化器工厂

创建和管理不同格式的输出格式化器
"""
from typing import Dict, Type
from .base import BaseFormatter
from .json_formatter import JSONFormatter
from .txt_formatter import TXTFormatter
from .yaml_formatter import YAMLFormatter


class FormatterFactory:
    """格式化器工厂"""

    _formatters: Dict[str, Type[BaseFormatter]] = {
        'json': JSONFormatter,
        'txt': TXTFormatter,
        'yaml': YAMLFormatter,
    }

    @classmethod
    def create(cls, format_type: str) -> BaseFormatter:
        """
        创建格式化器实例

        Args:
            format_type: 格式类型 (json/txt/yaml)

        Returns:
            格式化器实例

        Raises:
            ValueError: 如果格式类型不支持
        """
        format_type = format_type.lower()

        if format_type not in cls._formatters:
            supported = ', '.join(cls._formatters.keys())
            raise ValueError(
                f"不支持的输出格式: '{format_type}'. "
                f"支持的格式: {supported}"
            )

        return cls._formatters[format_type]()

    @classmethod
    def get_supported_formats(cls) -> list[str]:
        """获取支持的格式列表"""
        return list(cls._formatters.keys())

    @classmethod
    def register(cls, format_type: str, formatter_class: Type[BaseFormatter]):
        """
        注册新的格式化器

        Args:
            format_type: 格式类型
            formatter_class: 格式化器类
        """
        cls._formatters[format_type.lower()] = formatter_class
