#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 日志模块
负责处理应用程序的日志记录功能
"""

from loguru import logger
import os
import sys

# 配置日志
log_dir = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'log.txt')

# 添加文件handler
logger.add(
    log_file,
    rotation="1 MB",  # 日志文件达到1MB时轮转
    retention="7 days", # 最多保留5天的日志文件
    compression="zip",  # 压缩旧的日志文件
    encoding='utf-8',   # 设置编码
    level="DEBUG"       # 设置日志级别
)

# 添加控制台handler
if sys.stdout is not None:
    logger.add(
        sys.stdout,
        colorize=True,      # 启用彩色输出
        level="INFO"        # 设置日志级别
    )

# 定义一个全局可用的logger实例
def get_logger():
    return logger