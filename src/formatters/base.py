"""
输出格式化器基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseFormatter(ABC):
    """输出格式化器基类"""

    @abstractmethod
    def format(self, result: Dict[str, Any]) -> str:
        """
        将结果格式化为字符串

        Args:
            result: 执行结果字典

        Returns:
            格式化后的字符串
        """
        pass

    @abstractmethod
    def get_extension(self) -> str:
        """
        返回文件扩展名

        Returns:
            文件扩展名（不带点）
        """
        pass
