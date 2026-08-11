#!/usr/bin/env bash
# 一键重启并实时观察上传结果
cd /d/project/qr-system
pkill -f "python main.py"
python main.py &
sleep 5
tail -f logs/auto_sync.log