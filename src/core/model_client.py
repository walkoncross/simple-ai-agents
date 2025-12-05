"""
模型客户端

使用 OpenAI SDK 调用兼容 OpenAI API 的模型服务
支持 LLM 和 VLM
"""
from typing import List, Dict, Any, Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger

from ..utils.config_loader import ModelConfig


class ModelClient:
    """模型客户端"""

    def __init__(
        self,
        model_config: ModelConfig,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        timeout: int = 60
    ):
        """
        Args:
            model_config: 模型配置
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            timeout: 超时时间（秒）
        """
        self.config = model_config
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base,
            timeout=timeout
        )

        logger.debug(
            f"初始化模型客户端: {self.config.type}, "
            f"model={self.config.model}, api_base={self.config.api_base}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _call_api(self, messages: List[Dict[str, Any]]) -> str:
        """
        调用 API（带重试）

        Args:
            messages: 消息列表

        Returns:
            模型响应文本
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            content = response.choices[0].message.content

            # 记录token使用情况
            if hasattr(response, 'usage'):
                logger.debug(
                    f"Token usage: "
                    f"prompt={response.usage.prompt_tokens}, "
                    f"completion={response.usage.completion_tokens}, "
                    f"total={response.usage.total_tokens}"
                )

            return content

        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            raise

    def call_llm(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """
        调用 LLM

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            模型响应
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info(f"调用 LLM: {self.config.model}")
        logger.debug(f"System prompt 长度: {len(system_prompt)}")
        logger.debug(f"User prompt 长度: {len(user_prompt)}")

        return self._call_api(messages)

    def call_vlm(
        self,
        system_prompt: str,
        user_prompt: str,
        images: List[Dict[str, Any]]
    ) -> str:
        """
        调用 VLM（Vision Language Model）

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            images: 图像列表（OpenAI Vision API 格式）

        Returns:
            模型响应
        """
        # 构建 user content（文本 + 图像）
        user_content = [
            {"type": "text", "text": user_prompt}
        ]
        user_content.extend(images)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        logger.info(
            f"调用 VLM: {self.config.model}, "
            f"图像数量: {len(images)}"
        )
        logger.debug(f"System prompt 长度: {len(system_prompt)}")
        logger.debug(f"User prompt 长度: {len(user_prompt)}")

        return self._call_api(messages)

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        images: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        通用调用接口（自动判断 LLM 或 VLM）

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            images: 图像列表（可选，VLM 需要）

        Returns:
            模型响应
        """
        if images and len(images) > 0:
            # 有图像，使用 VLM
            if self.config.type != 'vlm':
                logger.warning(
                    f"模型类型为 '{self.config.type}'，但提供了图像输入。"
                    f"将尝试作为 VLM 调用。"
                )
            return self.call_vlm(system_prompt, user_prompt, images)
        else:
            # 无图像，使用 LLM
            return self.call_llm(system_prompt, user_prompt)
