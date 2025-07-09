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
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

# 移除默认的handler
logger.remove()

# 添加文件handler
logger.add(
    log_file,
    rotation="1 MB",  # 日志文件达到1MB时轮转
    retention="5 days", # 最多保留5天的日志文件
    compression="zip",  # 压缩旧的日志文件
    encoding='utf-8',   # 设置编码
    level="DEBUG"       # 设置日志级别
)

# 添加控制台handler
logger.add(
    sys.stdout,
    colorize=True,      # 启用彩色输出
    format="<green>{time}</green> <level>{level}</level> <cyan>{message}</cyan>",
    level="INFO"        # 设置日志级别
)

# 定义一个全局可用的logger实例
def get_logger():
    return logger