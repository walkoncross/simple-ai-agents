"""
Agent 基类

执行 Agent 的核心逻辑
"""
import re
import json
import time
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

import requests
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
        self.api_config = api_config  # 保存 API 配置（用于获取 output_dir 等）

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
            resize=model_config.resize_image_for_api,
            cache_enabled=model_config.image_cache_enabled,
            cache_dir=api_config.cache_dir if hasattr(api_config, 'cache_dir') else None,
            cache_ttl=model_config.image_cache_ttl
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

    def _save_original_images(self, images: List[str]) -> List[str]:
        """
        保存原始图像到本地（用于离线查看/人工核验）

        Args:
            images: 图像路径或 URL 列表

        Returns:
            保存后的本地路径列表
        """
        from ..utils.config_loader import ConfigLoader

        # 获取输出目录
        output_dir = Path(self.api_config.output_dir if hasattr(self.api_config, 'output_dir') else './output')

        # 创建图像保存目录：output/<agent_name>-images/
        images_dir = output_dir / f"{self.name}-images"
        images_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for idx, image_path in enumerate(images):
            try:
                if self.image_processor.is_url(image_path):
                    # URL 图像：下载原图
                    logger.debug(f"下载原始图像: {image_path}")
                    response = requests.get(image_path, timeout=30)
                    response.raise_for_status()

                    # 从 URL 推测文件扩展名
                    from urllib.parse import urlparse
                    parsed_url = urlparse(image_path)
                    url_path = parsed_url.path
                    ext = Path(url_path).suffix or '.jpg'

                    # 保存文件
                    filename = f"{timestamp}-{idx+1}{ext}"
                    save_path = images_dir / filename
                    save_path.write_bytes(response.content)

                    logger.info(f"已保存 URL 图像: {save_path}")
                else:
                    # 本地文件：直接复制
                    source_path = Path(image_path)
                    if not source_path.exists():
                        logger.warning(f"源图像不存在: {image_path}")
                        continue

                    filename = f"{timestamp}-{idx+1}{source_path.suffix}"
                    save_path = images_dir / filename
                    shutil.copy2(source_path, save_path)

                    logger.info(f"已复制本地图像: {save_path}")

                saved_paths.append(str(save_path))

            except Exception as e:
                logger.warning(f"保存原始图像失败 {image_path}: {e}")
                continue

        return saved_paths

    def run(
        self,
        input_data: Dict[str, Any],
        images: Optional[List[str]] = None,
        save_images: bool = False
    ) -> Dict[str, Any]:
        """
        执行 Agent

        Args:
            input_data: 输入数据字典
            images: 图像路径列表（可选）
            save_images: 是否保存原始图像到本地（用于离线查看/人工核验）

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
                # download_url 参数由 image_cache_enabled 控制
                # cache_enabled=True: 下载并缓存 URL 图像
                # cache_enabled=False: 直接使用 URL（不下载）
                download_url = self.image_processor.cache_enabled
                processed_images = self.image_processor.process_images(
                    images,
                    download_url=download_url
                )
                result['inputs']['images'] = images

                # 保存原始图像到本地（用于离线查看/人工核验）
                if save_images:
                    saved_paths = self._save_original_images(images)
                    result['saved_images'] = saved_paths
                    logger.info(f"已保存 {len(saved_paths)} 张原始图像到本地")
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
