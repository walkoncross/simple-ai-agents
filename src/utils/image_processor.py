"""
图像处理器

处理 VLM 的图像输入：
- 本地文件和 URL 支持
- 图像压缩和调整大小
- Base64 编码
- 多图像输入
"""
import base64
import io
import re
from pathlib import Path
from typing import List, Dict, Any, Union
from urllib.parse import urlparse

import requests
from PIL import Image
from loguru import logger


class ImageProcessor:
    """图像处理器"""

    SUPPORTED_FORMATS = ['jpg', 'jpeg', 'png', 'webp', 'gif']

    def __init__(
        self,
        max_size: int = 2048,
        quality: int = 85,
        resize: bool = True
    ):
        """
        Args:
            max_size: 图像最大尺寸（像素）
            quality: JPEG 压缩质量 (1-100)
            resize: 是否调整图像大小
        """
        self.max_size = max_size
        self.quality = quality
        self.resize = resize

    def is_url(self, path_or_url: str) -> bool:
        """判断是否为 URL"""
        try:
            result = urlparse(path_or_url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def is_valid_image_file(self, file_path: Path) -> bool:
        """检查是否为有效的图像文件"""
        if not file_path.exists():
            return False

        suffix = file_path.suffix.lower().lstrip('.')
        return suffix in self.SUPPORTED_FORMATS

    def resize_image(self, image: Image.Image) -> Image.Image:
        """
        调整图像大小（保持宽高比）

        Args:
            image: PIL Image 对象

        Returns:
            调整大小后的图像
        """
        if not self.resize:
            return image

        width, height = image.size

        if width <= self.max_size and height <= self.max_size:
            return image

        # 计算缩放比例
        if width > height:
            new_width = self.max_size
            new_height = int(height * (self.max_size / width))
        else:
            new_height = self.max_size
            new_width = int(width * (self.max_size / height))

        logger.debug(f"调整图像大小: {width}x{height} -> {new_width}x{new_height}")

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def image_to_base64(self, image: Image.Image, format: str = 'JPEG') -> str:
        """
        将 PIL Image 转换为 base64 字符串

        Args:
            image: PIL Image 对象
            format: 图像格式 (JPEG, PNG, etc.)

        Returns:
            base64 编码的字符串
        """
        # 如果图像有透明通道，转换为 PNG
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            format = 'PNG'
        else:
            # 确保图像是 RGB 模式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            format = 'JPEG'

        buffer = io.BytesIO()
        if format == 'JPEG':
            image.save(buffer, format=format, quality=self.quality, optimize=True)
        else:
            image.save(buffer, format=format, optimize=True)

        buffer.seek(0)
        img_bytes = buffer.read()

        return base64.b64encode(img_bytes).decode('utf-8')

    def process_local_image(self, image_path: str) -> str:
        """
        处理本地图像文件

        Args:
            image_path: 本地图像文件路径

        Returns:
            base64 编码的图像数据（带 data URL 前缀）

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的图像格式
        """
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"图像文件不存在: {image_path}")

        if not self.is_valid_image_file(path):
            raise ValueError(
                f"不支持的图像格式: {path.suffix}. "
                f"支持的格式: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        try:
            # 打开图像
            image = Image.open(path)

            # 调整大小
            if self.resize:
                image = self.resize_image(image)

            # 转换为 base64
            base64_data = self.image_to_base64(image)

            # 检测 MIME 类型
            if image.format == 'PNG' or image.mode in ('RGBA', 'LA'):
                mime_type = 'image/png'
            else:
                mime_type = 'image/jpeg'

            logger.debug(f"处理本地图像: {image_path}, 大小: {image.size}")

            return f"data:{mime_type};base64,{base64_data}"

        except Exception as e:
            logger.error(f"处理本地图像失败 {image_path}: {e}")
            raise

    def process_url_image(self, image_url: str, download: bool = False) -> str:
        """
        处理 URL 图像

        Args:
            image_url: 图像 URL
            download: 是否下载并转换为 base64

        Returns:
            如果 download=True，返回 base64 数据 URL；否则返回原始 URL

        Raises:
            ValueError: URL 无效
            requests.RequestException: 下载失败
        """
        # 验证 URL
        if not self.is_url(image_url):
            raise ValueError(f"无效的 URL: {image_url}")

        # 如果不需要下载，直接返回 URL
        if not download:
            logger.debug(f"使用图像 URL: {image_url}")
            return image_url

        # 下载图像并转换为 base64
        try:
            logger.debug(f"下载图像: {image_url}")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # 打开图像
            image = Image.open(io.BytesIO(response.content))

            # 调整大小
            if self.resize:
                image = self.resize_image(image)

            # 转换为 base64
            base64_data = self.image_to_base64(image)

            # 检测 MIME 类型
            if image.format == 'PNG' or image.mode in ('RGBA', 'LA'):
                mime_type = 'image/png'
            else:
                mime_type = 'image/jpeg'

            logger.debug(f"下载并处理图像: {image_url}, 大小: {image.size}")

            return f"data:{mime_type};base64,{base64_data}"

        except Exception as e:
            logger.error(f"处理 URL 图像失败 {image_url}: {e}")
            raise

    def process_image(self, path_or_url: str, download_url: bool = False) -> str:
        """
        处理图像（自动判断本地文件或 URL）

        Args:
            path_or_url: 本地路径或 URL
            download_url: 是否下载 URL 图像

        Returns:
            处理后的图像数据（base64 或 URL）
        """
        if self.is_url(path_or_url):
            return self.process_url_image(path_or_url, download=download_url)
        else:
            return self.process_local_image(path_or_url)

    def process_images(
        self,
        images: List[str],
        download_url: bool = False
    ) -> List[Dict[str, Any]]:
        """
        批量处理图像，返回 OpenAI Vision API 格式

        Args:
            images: 图像路径或 URL 列表
            download_url: 是否下载 URL 图像

        Returns:
            OpenAI Vision API 格式的图像列表

        Example:
            [
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
                {"type": "image_url", "image_url": {"url": "https://example.com/img.jpg"}}
            ]
        """
        result = []

        for idx, image in enumerate(images):
            try:
                processed = self.process_image(image, download_url=download_url)
                result.append({
                    "type": "image_url",
                    "image_url": {"url": processed}
                })
                logger.info(f"成功处理图像 {idx + 1}/{len(images)}: {image}")

            except Exception as e:
                logger.error(f"处理图像失败 {idx + 1}/{len(images)}: {image}, 错误: {e}")
                raise

        return result
