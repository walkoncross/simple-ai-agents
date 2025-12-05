"""
JSON 格式化器
"""
import json
from typing import Dict, Any
from .base import BaseFormatter


class JSONFormatter(BaseFormatter):
    """JSON 格式化器"""

    def __init__(self, indent: int = 2):
        """
        Args:
            indent: JSON 缩进空格数
        """
        self.indent = indent

    def format(self, result: Dict[str, Any]) -> str:
        """格式化为 JSON"""
        return json.dumps(result, ensure_ascii=False, indent=self.indent)

    def get_extension(self) -> str:
        """返回扩展名"""
        return "json"
