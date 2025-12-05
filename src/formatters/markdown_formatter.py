"""
Markdown 格式化器
"""
from typing import Dict, Any
from .base import BaseFormatter


class MarkdownFormatter(BaseFormatter):
    """Markdown 格式化器 - 适合文档和报告"""

    def format(self, result: Dict[str, Any]) -> str:
        """格式化为 Markdown"""
        lines = []

        # 标题
        agent_name = result.get('agent', 'Agent')
        lines.append(f"# {agent_name} 执行结果\n")

        # 基本信息
        lines.append("## 基本信息\n")
        lines.append(f"- **状态**: {result.get('status', 'N/A')}")
        lines.append(f"- **时间**: {result.get('timestamp', 'N/A')}")

        if 'execution_time' in result:
            lines.append(f"- **耗时**: {result['execution_time']:.2f} 秒")

        lines.append("")

        # 输入数据
        if 'inputs' in result:
            lines.append("## 输入数据\n")
            inputs = result['inputs']
            if isinstance(inputs, dict):
                for key, value in inputs.items():
                    if isinstance(value, list):
                        lines.append(f"### {key}\n")
                        for item in value:
                            lines.append(f"- {item}")
                        lines.append("")
                    elif isinstance(value, str) and '\n' in value:
                        # 多行文本使用代码块
                        lines.append(f"### {key}\n")
                        lines.append("```")
                        lines.append(value)
                        lines.append("```\n")
                    else:
                        lines.append(f"**{key}**: {value}\n")
            else:
                lines.append(f"```\n{inputs}\n```\n")

        # 输出数据
        if 'outputs' in result:
            lines.append("## 输出结果\n")
            outputs = result['outputs']
            if isinstance(outputs, dict):
                for key, value in outputs.items():
                    if isinstance(value, (list, dict)):
                        lines.append(f"### {key}\n")
                        lines.append("```json")
                        import json
                        lines.append(json.dumps(value, ensure_ascii=False, indent=2))
                        lines.append("```\n")
                    elif isinstance(value, str) and '\n' in value:
                        # 多行文本
                        lines.append(f"### {key}\n")
                        lines.append(value)
                        lines.append("")
                    else:
                        lines.append(f"**{key}**: {value}\n")
            else:
                lines.append(f"```\n{outputs}\n```\n")

        # 验证信息
        if 'validation' in result:
            lines.append("## 验证信息\n")
            validation = result['validation']
            if isinstance(validation, dict):
                for key, value in validation.items():
                    lines.append(f"- **{key}**: {value}")
            lines.append("")

        # 错误信息
        if 'error' in result:
            lines.append("## ⚠️ 错误信息\n")
            error = result['error']
            if isinstance(error, dict):
                lines.append(f"**类型**: `{error.get('type', 'N/A')}`\n")
                lines.append(f"**消息**: {error.get('message', 'N/A')}\n")
                if 'details' in error:
                    lines.append("**详情**:")
                    lines.append("```")
                    lines.append(error['details'])
                    lines.append("```")
            else:
                lines.append(f"```\n{error}\n```")

        return "\n".join(lines)

    def get_extension(self) -> str:
        """返回扩展名"""
        return "md"
