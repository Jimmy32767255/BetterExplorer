#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 快捷键管理模块
负责实现系统快捷键功能
"""

import sys
import psutil
from PyQt5.QtWidgets import QApplication, QShortcut
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

class HotkeyManager:
    """快捷键管理类，负责监听和处理系统快捷键"""
    
    def __init__(self, file_manager, settings, run_dialog=None):
        self.file_manager = file_manager
        self.settings = settings
        self.run_dialog = run_dialog
        
        # 创建应用程序实例
        self.app = QApplication.instance() or QApplication(sys.argv)
        
        # 设置快捷键
        self.setup_hotkeys()
    
    def is_explorer_running(self):
        """检查Windows资源管理器是否正在运行"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == 'explorer.exe':
                return True
        return False
        
    def setup_hotkeys(self):
        """设置系统快捷键"""
        # 如果Windows资源管理器正在运行，则不注册快捷键
        if self.is_explorer_running():
            return
            
        # Win+E 打开文件管理器
        self.win_e = QShortcut(QKeySequence("Win+E"), self.app.desktop())
        
        # Win+I 打开设置界面
        self.win_i = QShortcut(QKeySequence("Win+I"), self.app.desktop())
        
        # Win+R 打开运行窗口
        if self.run_dialog:
            self.win_r = QShortcut(QKeySequence("Win+R"), self.app.desktop())
            self.win_r.activated.connect(self.open_run_dialog)
        
        # 连接快捷键信号
        self.win_e.activated.connect(self.open_file_manager)
        self.win_i.activated.connect(self.open_settings)
    
    def open_file_manager(self):
        """打开文件管理器"""
        self.file_manager.show()
    
    def open_settings(self):
        """打开设置界面"""
        self.settings.show()
        
    def open_run_dialog(self):
        """打开运行对话框"""
        if self.run_dialog:
            self.run_dialog.show()

    def start(self):
        """启动快捷键监听"""
        self.app.exec_()