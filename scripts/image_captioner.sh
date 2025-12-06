#!/bin/bash
# Image Captioner Agent - 图像描述生成
# Usage: ./scripts/image_captioner.sh [image_path_or_url] [question]
#
# 支持本地图片文件和网络 URL
# 如果不提供参数，使用默认的示例图片 URL

# 默认使用 Qwen-VL 官方示例图片
DEFAULT_IMAGE="https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg"

IMAGE_PATH=${1:-$DEFAULT_IMAGE}
QUESTION=${2:-"请详细描述这张图片的内容"}

# 检查是否是 URL（以 http:// 或 https:// 开头）
if [[ "$IMAGE_PATH" =~ ^https?:// ]]; then
    echo "📷 使用网络图片: $IMAGE_PATH"
else
    # 本地文件，检查是否存在
    if [ ! -f "$IMAGE_PATH" ]; then
        echo "❌ 错误: 图像文件不存在: $IMAGE_PATH"
        echo ""
        echo "用法: $0 [image_path_or_url] [question]"
        echo ""
        echo "示例:"
        echo "  $0                                    # 使用默认示例图片"
        echo "  $0 photo.jpg                          # 本地图片"
        echo "  $0 https://example.com/photo.jpg      # 网络图片"
        echo "  $0 photo.jpg '图片中有哪些物体？'      # 自定义问题"
        exit 1
    fi
    echo "📷 使用本地图片: $IMAGE_PATH"
fi

echo "❓ 问题: $QUESTION"
echo ""

python src/main.py run image_captioner \
    --image "$IMAGE_PATH" \
    -i "{\"question\": \"$QUESTION\"}"
