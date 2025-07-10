#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 运行窗口模块
实现类似Windows的Win+R运行窗口功能
"""

from PyQt5.QtWidgets import QApplication, QInputDialog
from log import get_logger

logger = get_logger()

class RunDialog:
    """运行对话框类，提供命令行输入功能"""
    
    def __init__(self):
        self.app = QApplication.instance() or QApplication([])
    
    def show(self):
        """显示运行对话框"""
        text, ok = QInputDialog.getText(None, '运行', '输入命令或路径:')
        if ok and text:
            logger.info(f"执行命令: {text}")
            return text
        return None

    def start(self):
        """启动应用程序"""
        self.app.exec_()