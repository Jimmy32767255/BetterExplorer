#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 日志模块
负责处理应用程序的日志记录功能
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

class Logger:
    """日志处理类 - 单例模式"""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # 确保日志目录存在
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, 'app.log')
        
        # 确保日志文件存在
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                pass
        except Exception as e:
            print(f"无法创建日志文件: {e}")
            sys.exit(1)
        
        # 创建logger
        self.logger = logging.getLogger('BetterExplorer')
        self.logger.setLevel(logging.DEBUG)
        
        # 移除所有已存在的handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # 创建文件handler
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 创建控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.stream.reconfigure(encoding='utf-8')
        
        # 创建formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加handler到logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self._initialized = True
    
    def debug(self, message):
        """记录debug级别日志"""
        self.logger.debug(message)
    
    def info(self, message):
        """记录info级别日志"""
        self.logger.info(message)
    
    def warning(self, message):
        """记录warning级别日志"""
        self.logger.warning(message)
    
    def error(self, message):
        """记录error级别日志"""
        self.logger.error(message)
    
    def critical(self, message):
        """记录critical级别日志"""
        self.logger.critical(message)