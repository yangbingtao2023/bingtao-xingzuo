#!/bin/bash
# 星座运势数据管道：抓取 → 转换 → 入库
set -e

FETCHER_DIR="/Users/mac/Documents/我的知识库/工具/app/xiangyu-horoscope-fetcher"
PIPELINE_DIR="/Users/mac/Documents/我的知识库/业务/星座运势小程序/数据管道"
TIANAPI_KEY="${TIANAPI_KEY:-}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始运势数据管道..."

# Step 1: 抓取
echo "  📡 抓取运势..."
cd "$FETCHER_DIR"
.venv/bin/python fetch_daily_horoscope.py

# Step 2: 转换
echo "  🔄 转换格式..."
cd "$PIPELINE_DIR"
python3 transform_horoscope.py

# Step 3: 入库
echo "  💾 写入数据库..."
python3 upload_to_cloudbase.py

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 管道完成"
