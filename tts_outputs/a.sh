#!/bin/bash
# 创建文件列表
for f in *.wav; do
    echo "file '$f'" >> list.txt
done

# 合并文件
ffmpeg -f concat -safe 0 -i list.txt -c copy combined.wav

# 清理临时文件
rm list.txt

