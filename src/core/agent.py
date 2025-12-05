"""
Agent 基类

执行 Agent 的核心逻辑
"""
import re
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from loguru import logger

from ..utils.config_loader import AgentConfig, ModelConfig, Config
from ..utils.image_processor import ImageProcessor
from .model_client import ModelClient
from .validator import Validator


class Agent:
    """Agent 基类"""

    def __init__(
        self,
        name: str,
        agent_config: AgentConfig,
        prompts: Dict[str, str],
        model_config: ModelConfig,
        validation_config,
        api_config
    ):
        """
        Args:
            name: Agent 名称
            agent_config: Agent 配置
            prompts: Prompts 字典 {'system': ..., 'user': ...}
            model_config: 模型配置
            validation_config: 验证配置
            api_config: API 配置
        """
        self.name = name
        self.agent_config = agent_config
        self.prompts = prompts
        self.model_config = model_config

        # 初始化组件
        self.model_client = ModelClient(
            model_config,
            max_retries=api_config.max_retries,
            retry_delay=api_config.retry_delay,
            timeout=api_config.timeout
        )

        self.image_processor = ImageProcessor(
            max_size=model_config.max_image_size,
            quality=model_config.image_quality,
            resize=model_config.resize_image_for_api
        )

        self.validator = Validator(validation_config)

        logger.info(f"初始化 Agent: {name}, 类型: {agent_config.type}")

    def render_prompt(self, template: str, inputs: Dict[str, Any]) -> str:
        """
        渲染 prompt 模板（替换 {{field}} 为实际值）

        Args:
            template: Prompt 模板
            inputs: 输入数据字典

        Returns:
            渲染后的 prompt
        """
        def replace_field(match):
            field_name = match.group(1)
            value = inputs.get(field_name, f"{{{{不存在的字段: {field_name}}}}}")

            # 如果值是列表或字典，转换为 JSON
            if isinstance(value, (list, dict)):
                return json.dumps(value, ensure_ascii=False, indent=2)

            return str(value)

        pattern = r'\{\{(\w+)\}\}'
        rendered = re.sub(pattern, replace_field, template)

        return rendered

    def prepare_input_data(
        self,
        input_str_or_dict: Any,
        images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        准备输入数据

        Args:
            input_str_or_dict: 输入（字符串、字典或 None）
            images: 图像列表（可选）

        Returns:
            输入数据字典
        """
        # 处理文本输入
        if input_str_or_dict is None:
            input_data = {}
        elif isinstance(input_str_or_dict, dict):
            input_data = input_str_or_dict
        elif isinstance(input_str_or_dict, str):
            # 尝试解析为 JSON
            try:
                input_data = json.loads(input_str_or_dict)
                if not isinstance(input_data, dict):
                    # 如果解析结果不是字典，包装为字典
                    input_data = {"input": input_data}
            except json.JSONDecodeError:
                # 如果不是 JSON，直接作为文本
                if self.agent_config.inputs:
                    # 如果定义了 inputs，需要 JSON 格式
                    raise ValueError(
                        f"输入格式不正确。期望 JSON 格式的输入，例如: "
                        f"{{{', '.join([f'\"{field}\": \"...\"' for field in self.agent_config.inputs])}}}\n"
                        f"实际收到: {input_str_or_dict[:100]}"
                    )
                else:
                    # 没有定义 inputs，作为纯文本
                    input_data = {"input": input_str_or_dict}
        else:
            input_data = {"input": str(input_str_or_dict)}

        # 添加图像路径（如果有）
        if images:
            input_data['images'] = images

        return input_data

    def run(
        self,
        input_data: Dict[str, Any],
        images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        执行 Agent

        Args:
            input_data: 输入数据字典
            images: 图像路径列表（可选）

        Returns:
            执行结果字典
        """
        start_time = time.time()

        result = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "inputs": input_data.copy(),
            "status": "success"
        }

        try:
            # 1. Prompt 模板验证
            logger.info("步骤 1/5: 验证 Prompt 模板")
            valid, missing_refs = self.validator.validate_prompt_templates(
                self.agent_config,
                self.prompts['system'],
                self.prompts['user']
            )
            if not valid:
                raise ValueError(f"Prompt 模板验证失败，未引用字段: {missing_refs}")

            # 2. 输入数据验证
            logger.info("步骤 2/5: 验证输入数据")
            valid, missing_fields = self.validator.validate_input_data(
                self.agent_config,
                input_data
            )
            if not valid:
                raise ValueError(f"输入数据验证失败，缺少字段: {missing_fields}")

            if missing_fields:
                result['validation'] = {'missing_input_fields': missing_fields}

            # 3. 处理图像（如果有）
            processed_images = None
            if images and len(images) > 0:
                logger.info(f"步骤 3/5: 处理 {len(images)} 张图像")
                processed_images = self.image_processor.process_images(images)
                result['inputs']['images'] = images
            else:
                logger.info("步骤 3/5: 无图像输入，跳过")

            # 4. 渲染 Prompts
            logger.info("步骤 4/5: 渲染 Prompts")
            system_prompt = self.render_prompt(self.prompts['system'], input_data)
            user_prompt = self.render_prompt(self.prompts['user'], input_data) if self.prompts['user'] else ""

            # 5. 调用模型
            logger.info(f"步骤 5/5: 调用模型 {self.model_config.model}")
            response = self.model_client.call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                images=processed_images
            )

            # 6. 验证输出
            valid, missing_output_fields, parsed_output = self.validator.validate_output_data(
                self.agent_config,
                response
            )

            if parsed_output is not None:
                result['outputs'] = parsed_output
            else:
                result['outputs'] = {"raw_response": response}

            if missing_output_fields:
                if 'validation' not in result:
                    result['validation'] = {}
                result['validation']['missing_output_fields'] = missing_output_fields
                result['status'] = 'partial_success'

        except Exception as e:
            logger.error(f"Agent 执行失败: {e}")
            result['status'] = 'error'
            result['error'] = {
                'type': type(e).__name__,
                'message': str(e)
            }

        finally:
            execution_time = time.time() - start_time
            result['execution_time'] = execution_time
            logger.info(f"Agent 执行完成，耗时: {execution_time:.2f}秒，状态: {result['status']}")

        return result
