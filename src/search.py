#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 搜索模块
实现全局搜索功能，支持应用程序和文件搜索
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QListWidget,
                             QListWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import os
from log import get_logger

logger = get_logger()
from settings import Settings # 导入 Settings

class SearchWindow(QWidget):
    """搜索主界面类"""

    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.init_ui()

    def init_ui(self):
        """初始化搜索界面"""
        self.setStyleSheet(
            "background-color: #2D2D30; color: white; border: 1px solid #3F3F46;"
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索应用、文件和设置")
        self.search_input.setStyleSheet(
            "QLineEdit {background-color: #3E3E42; border: 1px solid #555555;"
            "border-radius: 3px; padding: 8px;}"
            "QLineEdit:focus {border: 1px solid #0078D7;}"
        )
        main_layout.addWidget(self.search_input)

        # 连接信号
        self.search_input.textChanged.connect(self.perform_search)

        # 搜索结果列表
        self.result_list = QListWidget()
        self.result_list.setStyleSheet(
            "QListWidget {background-color: #1E1E1E; border: none;}"
            "QListWidget::item {height: 40px; padding: 5px;}"
            "QListWidget::item:hover {background-color: #3E3E42;}"
            "QListWidget::item:selected {background-color: #0078D7;}"
        )
        main_layout.addWidget(self.result_list)
        # 连接双击信号
        self.result_list.itemDoubleClicked.connect(self.open_item)

    def perform_search(self, query):
        """执行搜索操作"""
        self.result_list.clear()
        if not query:
            return

        self.logger.info(f"开始搜索: {query}")
        query_lower = query.lower()

        # 获取桌面路径 (优先从设置读取，否则使用默认路径)
        desktop_path = Settings.get_setting("desktop_path", os.path.expanduser("~\Desktop"))
        
        # 搜索桌面文件/文件夹
        try:
            if os.path.exists(desktop_path):
                for item_name in os.listdir(desktop_path):
                    if query_lower in item_name.lower():
                        item_path = os.path.join(desktop_path, item_name)
                        item = QListWidgetItem(item_name)
                        # 可以根据是文件还是文件夹设置不同图标
                        # icon_path = "icons/file_icon.svg" if os.path.isfile(item_path) else "icons/folder_icon.svg"
                        # item.setIcon(QIcon(icon_path)) # 需要准备相应图标文件
                        item.setIcon(QIcon("icons/search_icon.svg")) # 暂时使用通用图标
                        item.setData(Qt.UserRole, {"type": "file", "path": item_path}) # 存储类型和完整路径
                        self.result_list.addItem(item)
            else:
                self.logger.warning(f"桌面路径不存在: {desktop_path}")
        except Exception as e:
            self.logger.error(f"搜索桌面时出错: {e}")

        # 搜索应用程序 (开始菜单)
        start_menu_paths = [
            os.path.join(os.environ.get('PROGRAMDATA', 'C:\ProgramData'), 'Microsoft\Windows\Start Menu\Programs'),
            os.path.join(os.environ.get('APPDATA', ''), 'Microsoft\Windows\Start Menu\Programs')
        ]

        for path in start_menu_paths:
            if os.path.exists(path):
                try:
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if file.lower().endswith(('.lnk', '.url')) and query_lower in file.lower().replace('.lnk', '').replace('.url', ''):
                                app_name = os.path.splitext(file)[0]
                                app_path = os.path.join(root, file)
                                item = QListWidgetItem(app_name)
                                item.setIcon(QIcon("icons/search_icon.svg")) # 暂时使用通用图标, 后续可尝试提取快捷方式图标
                                item.setData(Qt.UserRole, {"type": "app", "path": app_path})
                                self.result_list.addItem(item)
                except Exception as e:
                    self.logger.error(f"搜索开始菜单 '{path}' 时出错: {e}")

    def open_item(self, item):
        """双击打开选中的项目"""
        item_data = item.data(Qt.UserRole)
        if item_data and 'path' in item_data:
            item_path = item_data['path']
            item_type = item_data.get('type', 'file') # 默认为文件
            self.logger.info(f"尝试打开 {item_type}: {item_path}")
            try:
                os.startfile(item_path)
                # self.close() # 打开后关闭搜索窗口 - Removed, closeEvent will handle signal
                # Instead of closing directly, let the OS handle the focus shift.
                # The window might close itself or the user might close it.
                # We rely on closeEvent to signal completion.
                pass # Keep the window open briefly
            except Exception as e:
                self.logger.error(f"打开 {item_path} 时出错: {e}")
        else:
            self.logger.warning("无法获取项目路径信息")