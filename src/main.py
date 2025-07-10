#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 一个增强型文件资源管理器
主入口文件，负责初始化应用程序并调用其他模块
"""

import sys
import signal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QPushButton # 导入 QPushButton
from desktop import Desktop
from file_manager import FileManager
from alt_tab import AltTabSwitcher
from display_manager import DisplayManager
from taskbar import TaskBar
from start_menu import StartMenu
from hotkey import HotkeyManager
from log import get_logger

from settings import Settings





class BetterExplorer:
    """主应用程序类，负责初始化和协调各个模块"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("BetterExplorer")
        
        # 初始化日志记录器
        self.logger = get_logger()
        self.logger.info("BetterExplorer 应用程序启动")
        
        # 设置Ctrl+C信号处理器
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # 初始化显示器管理器
        self.display_manager = DisplayManager()
        
        # 初始化桌面
        self.desktop = Desktop(self.display_manager)
        
        # 初始化文件管理器
        self.file_manager = FileManager()
        
        # 初始化Alt+Tab切换器
        self.alt_tab = AltTabSwitcher()
        
        # 初始化任务栏
        self.taskbar = TaskBar(self.display_manager)
        
        # 设置桌面的任务栏引用
        self.desktop.set_taskbar(self.taskbar)
        
        # 初始化开始菜单
        self.start_menu = StartMenu(self.display_manager, self.taskbar)


        
        # 连接任务栏开始按钮和开始菜单
        for taskbar_info in self.taskbar.taskbar_widgets:
            start_button = taskbar_info['start_button']
            start_button.clicked.connect(
                lambda checked=False, btn=start_button: 
                self.start_menu.toggle_visibility(btn.mapToGlobal(btn.rect().topLeft()))
            )
            # 连接搜索按钮
            search_button = taskbar_info['widget'].findChild(QPushButton, 'searchButton')
            if search_button:
                search_button.clicked.connect(lambda: self.start_menu.show_and_focus_search())
        
        # 连接任务栏的通知方法到桌面的调整大小方法
        self.taskbar.notify_desktop_resize = self.desktop.adjust_desktop_size
        
        # 初始化快捷键管理器
        self.hotkey_manager = HotkeyManager(self.file_manager, Settings())
        self.hotkey_manager.setup_hotkeys()
        
    def run(self):
        """运行应用程序"""
        # 显示桌面
        self.desktop.show()
        
        # 显示任务栏
        self.taskbar.show()
        
        # 启动Alt+Tab监听
        self.alt_tab.start_monitoring()
        
        # 连接应用程序退出信号
        self.app.aboutToQuit.connect(self.cleanup)
        
        # 运行应用程序主循环
        return self.app.exec_()
    
    def cleanup(self):
        """程序退出时的清理工作"""
        # 如果系统资源管理器被关闭，则重新启动它
        if Settings.get_setting("disable_system_explorer", False):
            file_manager = FileManager()
            file_manager.start_system_explorer()
    
    def signal_handler(self, signum, frame):
        """处理Ctrl+C信号"""
        logger.info("\n正在退出程序...")
        self.cleanup()
        self.app.quit()


if __name__ == "__main__":
    # 创建并运行应用程序
    explorer = BetterExplorer()
    sys.exit(explorer.run())