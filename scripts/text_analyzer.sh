#!/bin/bash
# Text Analyzer Agent - 文本分析
# Usage: ./scripts/text_analyzer.sh [text_or_file] [analysis_type]
#
# 支持直接输入文本或从文件读取
# 如果不提供参数，使用默认的示例文本

# 默认使用示例文本
DEFAULT_TEXT="今天天气真好，阳光明媚，心情也非常愉快！我很期待周末的户外活动。"

TEXT=${1:-$DEFAULT_TEXT}
ANALYSIS_TYPE=${2:-"全面分析"}

# 检查是否是文件路径
if [ -f "$TEXT" ]; then
    echo "📄 从文件读取文本: $TEXT"
    TEXT_CONTENT=$(cat "$TEXT")
    echo "📝 文本内容预览: ${TEXT_CONTENT:0:100}..."
else
    TEXT_CONTENT="$TEXT"
    echo "📝 分析文本: ${TEXT_CONTENT:0:100}..."
fi

echo "🔍 分析类型: $ANALYSIS_TYPE"
echo ""

python src/main.py run text_analyzer \
    --input "{\"text\": \"$TEXT_CONTENT\"}"
