"""
参数验证器

实现三层验证机制：
1. Prompt 模板验证
2. 输入数据验证
3. 输出数据验证
"""
import re
import json
from typing import Dict, Any, List, Tuple, Optional
from loguru import logger

from ..utils.config_loader import AgentConfig, ValidationConfig


class Validator:
    """参数验证器"""

    def __init__(self, validation_config: ValidationConfig):
        """
        Args:
            validation_config: 验证配置
        """
        self.config = validation_config

    def validate_prompt_templates(
        self,
        agent_config: AgentConfig,
        system_prompt: str,
        user_prompt: str
    ) -> Tuple[bool, List[str]]:
        """
        验证 prompt 模板是否引用了所有输入字段

        Args:
            agent_config: Agent 配置
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            (是否通过, 未引用的字段列表)
        """
        if not self.config.prompt_template_validation:
            return True, []

        if not agent_config.inputs:
            # 没有定义 inputs，跳过验证
            return True, []

        required_fields = set(agent_config.inputs)

        # 从 prompts 中提取所有 {{field}} 引用
        pattern = r'\{\{(\w+)\}\}'
        referenced_fields = set()

        for prompt in [system_prompt, user_prompt]:
            if prompt:
                matches = re.findall(pattern, prompt)
                referenced_fields.update(matches)

        # 检查是否所有输入字段都被引用
        missing_refs = required_fields - referenced_fields

        if missing_refs:
            logger.warning(f"⚠️  Prompt 模板未引用以下输入字段: {list(missing_refs)}")
            logger.warning(f"建议在 system_prompt 或 user_prompt 中添加 {{{{{', '.join(missing_refs)}}}}} 引用")

            if self.config.prompt_template_strict:
                logger.error("Prompt 模板验证失败（strict 模式）")
                return False, list(missing_refs)

        return True, list(missing_refs)

    def validate_input_data(
        self,
        agent_config: AgentConfig,
        input_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        验证输入数据是否包含所有必需字段

        Args:
            agent_config: Agent 配置
            input_data: 输入数据字典

        Returns:
            (是否通过, 缺失的字段列表)
        """
        if not self.config.input_validation:
            return True, []

        if not agent_config.inputs:
            # 没有定义 inputs，跳过验证
            return True, []

        required_fields = set(agent_config.inputs)
        provided_fields = set(input_data.keys())

        missing_fields = required_fields - provided_fields

        if missing_fields:
            print(f"❌ 错误: 输入数据缺少以下必需字段: {list(missing_fields)}")
            print(f"必需字段: {list(required_fields)}")
            print(f"已提供字段: {list(provided_fields)}")

            if self.config.input_strict:
                logger.error("输入数据验证失败（strict 模式）")
                return False, list(missing_fields)

            # 询问用户是否继续
            try:
                response = input("\n是否继续执行? (y/n): ").strip().lower()
                if response != 'y':
                    logger.info("用户取消执行")
                    return False, list(missing_fields)
            except (EOFError, KeyboardInterrupt):
                logger.info("用户取消执行")
                return False, list(missing_fields)

            logger.warning("用户选择继续执行，尽管缺少部分输入字段")

        return True, list(missing_fields)

    def validate_output_data(
        self,
        agent_config: AgentConfig,
        output_data: Any
    ) -> Tuple[bool, List[str], Optional[Dict]]:
        """
        验证输出数据是否包含所有期望字段

        Args:
            agent_config: Agent 配置
            output_data: 输出数据（字符串或字典）

        Returns:
            (是否通过, 缺失的字段列表, 解析后的输出字典)
        """
        if not self.config.output_validation:
            # 尝试解析但不验证
            parsed = self._parse_output(output_data)
            return True, [], parsed

        if not agent_config.outputs:
            # 没有定义 outputs，跳过验证
            parsed = self._parse_output(output_data)
            return True, [], parsed

        # 尝试解析 JSON 输出
        parsed_output = self._parse_output(output_data)

        if parsed_output is None:
            logger.warning("⚠️  Agent 输出不是有效的 JSON 格式，无法验证字段")
            if self.config.output_strict:
                return False, list(agent_config.outputs), None
            return True, list(agent_config.outputs), None

        required_fields = set(agent_config.outputs)
        provided_fields = set(parsed_output.keys())
        missing_fields = required_fields - provided_fields

        if missing_fields:
            logger.warning(f"⚠️  Agent 输出缺少以下字段: {list(missing_fields)}")
            logger.warning(f"期望字段: {list(required_fields)}")
            logger.warning(f"实际字段: {list(provided_fields)}")

            if self.config.output_strict:
                logger.error("输出数据验证失败（strict 模式）")
                return False, list(missing_fields), parsed_output

            logger.info("继续执行并保存部分结果...")

            # 填充缺失字段为 null
            if self.config.output_fill_missing:
                for field in missing_fields:
                    parsed_output[field] = None

        return True, list(missing_fields), parsed_output

    def _parse_output(self, output_data: Any) -> Optional[Dict]:
        """
        尝试解析输出为 JSON 字典

        Args:
            output_data: 输出数据

        Returns:
            解析后的字典，如果解析失败则返回 None
        """
        if isinstance(output_data, dict):
            return output_data

        if isinstance(output_data, str):
            # 尝试解析 JSON
            try:
                # 尝试直接解析
                parsed = json.loads(output_data)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

            # 尝试提取 JSON（可能在 markdown 代码块中）
            try:
                # 匹配 ```json ... ``` 或 ``` ... ```
                json_pattern = r'```(?:json)?\s*\n(.*?)\n```'
                matches = re.findall(json_pattern, output_data, re.DOTALL)
                if matches:
                    parsed = json.loads(matches[0])
                    if isinstance(parsed, dict):
                        return parsed
            except json.JSONDecodeError:
                pass

        return None
