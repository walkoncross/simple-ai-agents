"""
YAML 格式化器
"""
import yaml
from typing import Dict, Any
from .base import BaseFormatter


class YAMLFormatter(BaseFormatter):
    """YAML 格式化器"""

    def __init__(self, default_flow_style: bool = False):
        """
        Args:
            default_flow_style: 是否使用流式风格
        """
        self.default_flow_style = default_flow_style

    def format(self, result: Dict[str, Any]) -> str:
        """格式化为 YAML"""
        return yaml.dump(
            result,
            allow_unicode=True,
            default_flow_style=self.default_flow_style,
            sort_keys=False
        )

    def get_extension(self) -> str:
        """返回扩展名"""
        return "yaml"
