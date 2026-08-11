#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性彻底删除 FTP 端 /companies 目录（含双 companies 残留）
执行后所有 JSON 今后只存在于 /data/
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# [DISABLED] Python FTP has been removed; this script is deprecated and will exit.

CONFIG_FTP = project_root / "config" / "ftp_config.json"

def load_ftp_config():
    with CONFIG_FTP.open(encoding="utf-8") as f:
        cfg = json.load(f)
    server = next(iter(cfg.values()))
    return {
        "host": server["host"],
        "port": server.get("port", 21),
        "username": server["user"],
        "password": server["pass"],
        "use_tls": server.get("tls", False),
    }

def main():
    print("[DISABLED] 该脚本已禁用：系统已彻底移除 Python 内置 FTP，同步与清理由 Windows 计划任务/运维脚本完成。")
    return

if __name__ == "__main__":
    main()