"""
TXT 格式化器
"""
from typing import Dict, Any
from .base import BaseFormatter


class TXTFormatter(BaseFormatter):
    """TXT 格式化器 - 人类可读的文本格式"""

    def format(self, result: Dict[str, Any]) -> str:
        """格式化为 TXT"""
        lines = []

        # 基本信息
        lines.append(f"Agent: {result.get('agent', 'N/A')}")
        lines.append(f"Timestamp: {result.get('timestamp', 'N/A')}")
        lines.append(f"Status: {result.get('status', 'N/A')}")

        if 'execution_time' in result:
            lines.append(f"Execution Time: {result['execution_time']:.2f}s")

        lines.append("")

        # 输入数据
        if 'inputs' in result:
            lines.append("=== Inputs ===")
            inputs = result['inputs']
            if isinstance(inputs, dict):
                for key, value in inputs.items():
                    if isinstance(value, list):
                        lines.append(f"{key}:")
                        for item in value:
                            lines.append(f"  - {item}")
                    else:
                        lines.append(f"{key}: {value}")
            else:
                lines.append(str(inputs))
            lines.append("")

        # 输出数据
        if 'outputs' in result:
            lines.append("=== Outputs ===")
            outputs = result['outputs']
            if isinstance(outputs, dict):
                for key, value in outputs.items():
                    if isinstance(value, (list, dict)):
                        lines.append(f"{key}:")
                        lines.append(f"  {value}")
                    else:
                        lines.append(f"{key}: {value}")
            else:
                lines.append(str(outputs))
            lines.append("")

        # 验证信息
        if 'validation' in result:
            lines.append("=== Validation ===")
            validation = result['validation']
            if isinstance(validation, dict):
                for key, value in validation.items():
                    lines.append(f"{key}: {value}")
            lines.append("")

        # 错误信息
        if 'error' in result:
            lines.append("=== Error ===")
            error = result['error']
            if isinstance(error, dict):
                lines.append(f"Type: {error.get('type', 'N/A')}")
                lines.append(f"Message: {error.get('message', 'N/A')}")
                if 'details' in error:
                    lines.append(f"Details: {error['details']}")
            else:
                lines.append(str(error))

        return "\n".join(lines)

    def get_extension(self) -> str:
        """返回扩展名"""
        return "txt"
