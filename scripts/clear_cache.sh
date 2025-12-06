#!/bin/bash

# 清理图像缓存脚本
# 用法：
#   ./scripts/clear_cache.sh              # 清理所有缓存
#   ./scripts/clear_cache.sh 7            # 清理 7 天前的缓存
#   ./scripts/clear_cache.sh 1h           # 清理 1 小时前的缓存
#   ./scripts/clear_cache.sh 30m          # 清理 30 分钟前的缓存

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CACHE_DIR="$PROJECT_ROOT/cache/images"

echo -e "${BLUE}🧹 图像缓存清理工具${NC}"
echo "缓存目录: $CACHE_DIR"
echo ""

# 检查缓存目录是否存在
if [ ! -d "$CACHE_DIR" ]; then
    echo -e "${YELLOW}📂 缓存目录不存在${NC}"
    exit 0
fi

# 解析时间参数
TIME_SECONDS=""
TIME_DESC=""
if [ $# -gt 0 ]; then
    INPUT="$1"
    
    # 解析时间单位
    if [[ "$INPUT" =~ ^([0-9]+)([smhd]?)$ ]]; then
        NUM="${BASH_REMATCH[1]}"
        UNIT="${BASH_REMATCH[2]}"
        
        case "$UNIT" in
            s|"")  # 秒（默认）或天数
                if [ -z "$UNIT" ]; then
                    # 无单位，视为天数
                    TIME_SECONDS=$((NUM * 86400))
                    TIME_DESC="$NUM 天"
                else
                    TIME_SECONDS=$NUM
                    TIME_DESC="$NUM 秒"
                fi
                ;;
            m)  # 分钟
                TIME_SECONDS=$((NUM * 60))
                TIME_DESC="$NUM 分钟"
                ;;
            h)  # 小时
                TIME_SECONDS=$((NUM * 3600))
                TIME_DESC="$NUM 小时"
                ;;
            d)  # 天
                TIME_SECONDS=$((NUM * 86400))
                TIME_DESC="$NUM 天"
                ;;
        esac
        echo -e "${YELLOW}⏰ 清理 $TIME_DESC 前的缓存${NC}"
    else
        echo -e "${RED}❌ 无效的时间格式: $INPUT${NC}"
        echo "用法示例："
        echo "  ./scripts/clear_cache.sh              # 清理所有缓存"
        echo "  ./scripts/clear_cache.sh 7            # 清理 7 天前的缓存"
        echo "  ./scripts/clear_cache.sh 1h           # 清理 1 小时前的缓存"
        echo "  ./scripts/clear_cache.sh 30m          # 清理 30 分钟前的缓存"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  将清理所有缓存${NC}"
fi

echo ""

# 统计当前缓存
JSON_COUNT=$(find "$CACHE_DIR" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
IMAGE_COUNT=$(find "$CACHE_DIR" \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.webp" -o -name "*.gif" \) 2>/dev/null | wc -l | tr -d ' ')
TOTAL_FILES=$((JSON_COUNT + IMAGE_COUNT))

if [ "$TOTAL_FILES" -eq 0 ]; then
    echo -e "${GREEN}✨ 缓存目录为空${NC}"
    exit 0
fi

# 计算总大小
TOTAL_SIZE=$(du -sk "$CACHE_DIR" 2>/dev/null | cut -f1)
SIZE_MB=$(echo "scale=2; $TOTAL_SIZE / 1024" | bc)

echo "📊 当前缓存统计："
echo "   - JSON 文件: $JSON_COUNT 个"
echo "   - 图像文件: $IMAGE_COUNT 个"
echo "   - 总计: $TOTAL_FILES 个文件"
echo "   - 总大小: ${SIZE_MB} MB"
echo ""

# 询问确认
if [ -n "$TIME_SECONDS" ]; then
    read -p "确认清理 $TIME_DESC 前的缓存? (y/n): " -n 1 -r
else
    read -p "⚠️  确认清理所有缓存? (y/n): " -n 1 -r
fi
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ 已取消${NC}"
    exit 0
fi

echo ""

# 执行清理
CLEARED_COUNT=0
CURRENT_TIME=$(date +%s)

if [ -n "$TIME_SECONDS" ]; then
    # 清理指定时间前的缓存
    echo "🗑️  清理中..."
    
    # 查找并删除过期的 JSON 文件
    while IFS= read -r -d '' file; do
        FILE_MTIME=$(stat -f %m "$file" 2>/dev/null || stat -c %Y "$file" 2>/dev/null)
        FILE_AGE=$((CURRENT_TIME - FILE_MTIME))
        
        if [ "$FILE_AGE" -gt "$TIME_SECONDS" ]; then
            # 删除 JSON 文件
            rm -f "$file"
            CLEARED_COUNT=$((CLEARED_COUNT + 1))
            
            # 删除对应的图像文件
            BASENAME="${file%.json}"
            for ext in jpg jpeg png webp gif; do
                IMAGE_FILE="${BASENAME}.${ext}"
                if [ -f "$IMAGE_FILE" ]; then
                    rm -f "$IMAGE_FILE"
                fi
            done
        fi
    done < <(find "$CACHE_DIR" -name "*.json" -print0)
else
    # 清理所有缓存
    echo "🗑️  清理所有文件..."
    CLEARED_COUNT=$JSON_COUNT
    rm -f "$CACHE_DIR"/*.json "$CACHE_DIR"/*.jpg "$CACHE_DIR"/*.jpeg "$CACHE_DIR"/*.png "$CACHE_DIR"/*.webp "$CACHE_DIR"/*.gif 2>/dev/null
fi

echo ""
echo -e "${GREEN}✅ 清理完成！删除了 $CLEARED_COUNT 个缓存项${NC}"

# 再次统计
JSON_COUNT_AFTER=$(find "$CACHE_DIR" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
IMAGE_COUNT_AFTER=$(find "$CACHE_DIR" \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.webp" -o -name "*.gif" \) 2>/dev/null | wc -l | tr -d ' ')
REMAINING=$((JSON_COUNT_AFTER + IMAGE_COUNT_AFTER))

if [ "$REMAINING" -gt 0 ]; then
    REMAINING_SIZE=$(du -sk "$CACHE_DIR" 2>/dev/null | cut -f1)
    REMAINING_MB=$(echo "scale=2; $REMAINING_SIZE / 1024" | bc)
    echo -e "📊 剩余缓存: $REMAINING 个文件 (${REMAINING_MB} MB)"
else
    echo -e "${GREEN}✨ 缓存目录已清空${NC}"
fi

echo ""
echo -e "${GREEN}✨ 缓存清理工具执行完毕${NC}"
