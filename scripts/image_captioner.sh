#!/bin/bash
# Image Captioner Agent - 图像描述生成
# Usage: ./scripts/image_captioner.sh <image_path> [question]

IMAGE_PATH=${1:"https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg"}
QUESTION=${2:-"请详细描述这张图片的内容"}

if [ -z "$IMAGE_PATH" ]; then
    echo "错误: 请提供图像文件路径"
    echo "用法: $0 <image_path> [question]"
    echo "示例: $0 photo.jpg"
    echo "示例: $0 photo.jpg '图片中有哪些物体？'"
    exit 1
fi

if [ ! -f "$IMAGE_PATH" ]; then
    echo "错误: 图像文件不存在: $IMAGE_PATH"
    exit 1
fi

python src/main.py run image_captioner \
    --image "$IMAGE_PATH" \
    --input "{\"question\": \"$QUESTION\"}"
