#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 开始菜单模块
负责实现开始菜单功能，包括程序列表、搜索框和电源选项
"""

import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QLineEdit, QScrollArea, QFrame, QGridLayout, 
                             QToolButton, QMenu, QAction, QApplication)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QCursor
from PyQt5.QtSvg import QSvgRenderer
from icons import file_manager_icon, settings_icon, power_icon
from PyQt5.QtWidgets import QFileIconProvider
from log import get_logger

logger = get_logger()
from uwp_app_menu import get_uwp_apps, launch_uwp_app
from file_manager import FileManager
from settings import Settings
from search import SearchWindow

class StartMenu(QWidget):
    """开始菜单类，提供开始菜单功能"""
    
    def __init__(self, display_manager, parent=None):
        super().__init__(parent)
        self.display_manager = display_manager
        self.is_visible = False
        self.taskbar = parent  # 保存任务栏引用
        
        # 初始化日志记录器
        self.logger = logger
        self.logger.info("开始菜单初始化")
        
        # 设置窗口属性
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化默认路径和当前路径
        self.default_start_menu_path = os.path.join(os.environ.get('ProgramData', 'C:\ProgramData'),
                                                  'Microsoft\Windows\Start Menu\Programs')
        self.current_path = self.default_start_menu_path
        
        # 初始化UI
        # 创建搜索窗口实例
        self.search_window = SearchWindow(self)
        self.search_window.hide()
        self.search_window.closed_signal.connect(self.handle_search_window_closed) # Connect the signal
        
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置菜单大小
        self.setFixedSize(400, 500)
        
        # 设置菜单样式
        self.setStyleSheet(
            "background-color: #2D2D30; color: white; border: 1px solid #3F3F46;"
        )
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 添加搜索框
        search_layout = QHBoxLayout()
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("搜索应用、设置和文档")
        search_edit.setStyleSheet(
            "QLineEdit {background-color: #3E3E42; border: 1px solid #555555; border-radius: 3px; padding: 8px;}"
            "QLineEdit:focus {border: 1px solid #0078D7;}"
        )
        search_layout.addWidget(search_edit)
        main_layout.addLayout(search_layout)
        
        # 连接搜索信号
        search_edit.textChanged.connect(self.search_window.perform_search)
        # search_edit.focusInEvent = lambda e: self.search_window.show() # Original
        # search_edit.focusOutEvent = lambda e: self.search_window.hide() # Original
        search_edit.focusInEvent = lambda e, le=search_edit: self.handle_search_focus_in(le, e)
        search_edit.focusOutEvent = lambda e, le=search_edit: self.handle_search_focus_out(le, e)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #3F3F46;")
        main_layout.addWidget(separator)

        # 添加顶部按钮区域 (返回和 UWP)
        top_button_layout = QHBoxLayout()
        top_button_layout.setSpacing(10)

        # 添加返回按钮 (如果不在根目录)
        if self.current_path != self.default_start_menu_path:
            self.back_button = QToolButton()
            self.back_button.setText('返回上级')
            self.back_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'back.svg')))
            self.back_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            self.back_button.setStyleSheet(
                "QToolButton {background-color: #3E3E42; color: white; border: none; border-radius: 3px; padding: 8px;}"
                "QToolButton:hover {background-color: #505054;}"
            )
            self.back_button.clicked.connect(self.go_back)
            top_button_layout.addWidget(self.back_button)
        else:
            # 添加占位符以保持 UWP 按钮位置
            top_button_layout.addStretch(1)

        # 添加UWP应用入口按钮
        self.uwp_button = QPushButton("UWP 应用")
        self.uwp_button.setStyleSheet(
            "QPushButton {background-color: #3E3E42; color: white; border: none; border-radius: 3px; padding: 8px;}"
            "QPushButton:hover {background-color: #505054;}"
        )
        self.uwp_button.clicked.connect(self.show_uwp_apps)
        top_button_layout.addWidget(self.uwp_button)
        top_button_layout.addStretch(1) # 添加弹性空间将按钮推向两侧

        main_layout.addLayout(top_button_layout) # 将顶部按钮布局添加到主布局
        
        # 添加程序列表区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            "QScrollArea {border: none; background-color: transparent;}"
            "QScrollBar:vertical {background-color: #2D2D30; width: 10px;}"
            "QScrollBar::handle:vertical {background-color: #3E3E42; border-radius: 5px;}"
            "QScrollBar::handle:vertical:hover {background-color: #505054;}"
        )
        
        # 创建程序列表容器
        program_widget = QWidget()
        program_layout = QGridLayout(program_widget)
        program_layout.setContentsMargins(0, 0, 0, 0)
        program_layout.setSpacing(10)
        
        # 添加UWP应用入口
        uwp_button = QPushButton("UWP 应用")
        uwp_button.setStyleSheet(
            "QPushButton {background-color: #3E3E42; color: white; border: none; border-radius: 3px; padding: 8px;}"
            "QPushButton:hover {background-color: #505054;}"
        )
        uwp_button.clicked.connect(self.show_uwp_apps)
        # 添加返回按钮
        if self.current_path != os.path.expanduser('~'):
            back_button = QToolButton()
            back_button.setText('返回上级')
            back_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'back.svg')))
            back_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            back_button.setStyleSheet(
                "QToolButton {background-color: #3E3E42; color: white; border: none; border-radius: 3px; padding: 8px;}"
                "QToolButton:hover {background-color: #505054;}"
            )
            back_button.clicked.connect(self.go_back)
            program_layout.addWidget(back_button, 0, 0, 1, 3)
        if self.current_path == os.path.expanduser('~'):
            program_layout.addWidget(uwp_button, 0, 0, 1, 3)
        
        # 从当前目录读取程序列表
        row = 1 # UWP按钮占用了第0行
        col = 0
        max_cols = 3
        
        # 检查是否需要添加返回按钮（虽然初始化时通常不需要，但保持逻辑一致性）
        if self.current_path != self.default_start_menu_path:
            back_button = QPushButton("返回上一级")
            back_button.setStyleSheet(
                "QPushButton {background-color: #3E3E42; color: white; border: none; border-radius: 3px; padding: 8px;}"
                "QPushButton:hover {background-color: #505054;}"
            )
            back_button.clicked.connect(self.go_back_in_start_menu)
            # 将返回按钮放在UWP按钮之前
            program_layout.addWidget(back_button, 0, 0, 1, 3)
            # UWP按钮向下移动一行
            program_layout.addWidget(uwp_button, 1, 0, 1, 3)
            row = 2 # 程序列表从第二行开始

        try:
            items = os.listdir(self.current_path)
        except FileNotFoundError:
            self.logger.warning(f"开始菜单路径不存在或无法访问: {self.current_path}")
            items = []
        except PermissionError:
            self.logger.warning(f"没有权限访问开始菜单路径: {self.current_path}")
            items = []

        for item in items:
            item_path = os.path.join(self.current_path, item)
            name = os.path.splitext(item)[0]

            # 跳过名为 "UWP 应用" 的项，因为它已在顶部按钮栏
            if name == "UWP 应用":
                continue
            
            # 判断是文件夹还是程序
            icon_type = "folder" if os.path.isdir(item_path) else "program"
            
            # 添加按钮
            self.add_program_button(program_layout, row, col, name, icon_type, item_path)
            
            # 更新行列位置
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        scroll_area.setWidget(program_widget)
        main_layout.addWidget(scroll_area, 1)  # 占据大部分空间
        
        # 添加底部区域
        bottom_layout = QHBoxLayout()
        
        # 添加用户信息区域
        user_layout = QHBoxLayout()
        # 获取用户头像路径
        avatar_path = os.path.join(os.environ.get('USERPROFILE'), 'AppData\\Roaming\\Microsoft\\Windows\\AccountPictures\\user-200-200.png')
        
        # 创建用户头像
        user_avatar = QLabel()
        user_avatar.setFixedSize(32, 32)
        
        # 检查头像文件是否存在
        if os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            user_avatar.setPixmap(pixmap)
        else:
            # 使用默认头像
            user_avatar.setStyleSheet(
                "background-color: #3E3E42; border-radius: 16px;"
            )
        user_name = QLabel(os.environ.get('USERNAME'))
        user_name.setStyleSheet("font-size: 14px; padding-left: 10px;")
        # 设置用户头像和名称的右键菜单
        user_avatar.setContextMenuPolicy(Qt.CustomContextMenu)
        user_avatar.customContextMenuRequested.connect(self.show_user_menu)
        user_name.setContextMenuPolicy(Qt.CustomContextMenu)
        user_name.customContextMenuRequested.connect(self.show_user_menu)
        
        user_layout.addWidget(user_avatar)
        user_layout.addWidget(user_name)
        user_layout.addStretch()
        
        # 添加底部按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        # 文件管理器按钮
        file_manager_button = QPushButton()
        file_manager_button.setFixedSize(32, 32)
        file_manager_button.setStyleSheet(
            "QPushButton {background-color: transparent; border: none; color: white;}"
            "QPushButton:hover {background-color: #3E3E42; border-radius: 3px;}"
            "QPushButton:pressed {background-color: #0078D7;}"
        )
        self.set_svg_icon(file_manager_button, file_manager_icon)
        file_manager_button.clicked.connect(lambda: self.on_program_clicked("文件管理器", os.path.join(os.path.dirname(os.path.abspath(__file__)), "file_manager.py")))
        
        # 设置按钮
        settings_button = QPushButton()
        settings_button.setFixedSize(32, 32)
        settings_button.setStyleSheet(
            "QPushButton {background-color: transparent; border: none; color: white;}"
            "QPushButton:hover {background-color: #3E3E42; border-radius: 3px;}"
            "QPushButton:pressed {background-color: #0078D7;}"
        )
        self.set_svg_icon(settings_button, settings_icon)
        settings_button.clicked.connect(lambda: self.on_program_clicked("设置", os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.py")))
        
        # 电源按钮
        power_button = QPushButton()
        power_button.setFixedSize(32, 32)
        power_button.setStyleSheet(
            "QPushButton {background-color: transparent; border: none; color: white;}"
            "QPushButton:hover {background-color: #3E3E42; border-radius: 3px;}"
            "QPushButton:pressed {background-color: #0078D7;}"
        )
        self.set_svg_icon(power_button, power_icon)
        power_button.clicked.connect(self.show_power_menu)
        
        button_layout.addWidget(file_manager_button)
        button_layout.addWidget(settings_button)
        button_layout.addWidget(power_button)
        
        bottom_layout.addLayout(user_layout)
        bottom_layout.addLayout(button_layout)
        
        main_layout.addLayout(bottom_layout)
    
    def add_program_button(self, layout, row, col, name, icon_type, item_path):
        """添加程序按钮到网格布局"""
        button = QToolButton()
        button.setText(name)
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setFixedSize(100, 80)
        
        # 创建文件图标提供器
        icon_provider = QFileIconProvider()
        
        # 根据类型设置图标
        if icon_type == "folder":
            button.setIcon(icon_provider.icon(QFileIconProvider.Folder))
        else:
            # 特殊处理系统应用图标
            if name == "文件管理器":
                self.set_svg_icon(button, file_manager_icon)
            elif name == "设置":
                self.set_svg_icon(button, settings_icon)
            else:
                button.setIcon(icon_provider.icon(QFileIconProvider.File))
        
        # 保持原有样式设置
        button.setStyleSheet(
            "QToolButton {background-color: transparent; color: white; border: none; text-align: center;}"
            "QToolButton:hover {background-color: #3E3E42; border-radius: 5px;}"
            "QToolButton:pressed {background-color: #0078D7;}"
        )
        
        # 连接点击事件
        button.clicked.connect(lambda checked, name=name, path=item_path: self.on_program_clicked(name, path))
        
        layout.addWidget(button, row, col)
        return button
    
    def show_uwp_apps(self):
        """显示UWP应用列表"""
        apps = get_uwp_apps()
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu {background-color: #2D2D30; color: white; border: 1px solid #3F3F46;}"
            "QMenu::item {padding: 5px 20px;}"
            "QMenu::item:selected {background-color: #3E3E42;}"
        )
        
        for app in apps:
            action = QAction(app['name'], self)
            action.triggered.connect(lambda checked, a=app: launch_uwp_app(a['appid']))
            menu.addAction(action)
        
        menu.exec_(QCursor.pos())

    def go_back(self):
        """返回上级目录"""
        self.current_path = os.path.dirname(self.current_path)
        self.refresh_program_list()

    def on_program_clicked(self, program_name, item_path):
        """处理程序点击事件"""
        # 判断是否是文件夹
        if os.path.isdir(item_path):
            # 更新当前路径并刷新界面
            self.current_path = item_path
            self.logger.debug(f"进入文件夹: {item_path}")
            self.refresh_program_list()
            return
        
        self.logger.info(f"启动程序: {program_name}")
        
        # 根据程序名称执行不同操作
        if program_name == "文件管理器":
            # 导入并创建文件管理器实例
            
            file_manager = FileManager()
            file_manager.show()
            
            # 保存文件管理器实例，防止被垃圾回收
            self.file_manager_instance = file_manager
        elif program_name == "设置":
            # 导入并创建设置实例
            
            settings_window = Settings()
            settings_window.show()
            
            # 保存设置实例，防止被垃圾回收
            self.settings_instance = settings_window
        else:
            # 处理其他程序
            try:
                if os.path.isfile(item_path):
                    os.startfile(item_path)
                elif os.path.isdir(item_path):
                    os.startfile(item_path)
            except Exception as e:
                self.logger.error(f"启动程序失败: {e}")
        
        # 点击后隐藏开始菜单
        self.hide()
    
    def show_power_menu(self):
        """显示电源菜单"""
        power_menu = QMenu(self)
        power_menu.setStyleSheet(
            "QMenu {background-color: #2D2D30; color: white; border: 1px solid #3F3F46;}"
            "QMenu::item {padding: 5px 20px;}"
            "QMenu::item:selected {background-color: #3E3E42;}"
        )
        
        # 添加电源选项
        sleep_action = QAction("睡眠", self)
        hibernate_action = QAction("休眠", self)
        shutdown_action = QAction("关机", self)
        restart_action = QAction("重启", self)
        
        # 连接动作信号
        sleep_action.triggered.connect(self.system_sleep)
        hibernate_action.triggered.connect(self.system_hibernate)
        shutdown_action.triggered.connect(self.system_shutdown)
        restart_action.triggered.connect(self.system_restart)
        
        # 添加动作到菜单
        power_menu.addAction(sleep_action)
        power_menu.addAction(hibernate_action)
        power_menu.addAction(shutdown_action)
        power_menu.addAction(restart_action)
        
        # 显示菜单
        power_menu.exec_(self.mapToGlobal(QPoint(self.width() - 100, self.height() - 40)))
    
    def system_sleep(self):
        """系统睡眠"""
        self.logger.info("系统睡眠")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        
    def system_hibernate(self):
        """系统休眠"""
        self.logger.info("系统休眠")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 1,1,0")
    
    def system_shutdown(self):
        """系统关机"""
        self.logger.info("系统关机")
        os.system("shutdown /s /t 0")
    
    def system_restart(self):
        """系统重启"""
        self.logger.info("系统重启")
        os.system("shutdown /r /t 0")
        
    def show_user_menu(self, pos):
        """显示用户上下文菜单"""
        user_menu = QMenu(self)
        user_menu.setStyleSheet(
            "QMenu {background-color: #2D2D30; color: white; border: 1px solid #3F3F46;}"
            "QMenu::item {padding: 5px 20px;}"
            "QMenu::item:selected {background-color: #3E3E42;}"
        )
        
        # 添加菜单选项
        lock_action = QAction("锁定", self)
        sign_out_action = QAction("注销", self)
        
        # 连接动作信号
        lock_action.triggered.connect(self.system_lock)
        sign_out_action.triggered.connect(self.system_sign_out)
        
        # 添加动作到菜单
        user_menu.addAction(lock_action)
        user_menu.addAction(sign_out_action)
        
        # 显示菜单
        user_menu.exec_(self.mapToGlobal(pos))
    
    def system_lock(self):
        """锁定系统"""
        self.logger.info("锁定系统")
        os.system("rundll32.exe user32.dll,LockWorkStation")
    
    def system_sign_out(self):
        """注销用户"""
        self.logger.info("注销用户")
        os.system("shutdown /l")
    
    def system_lock(self):
        """锁定系统"""
        self.logger.info("锁定系统")
        os.system("rundll32.exe user32.dll,LockWorkStation")
    
    def system_sign_out(self):
        """注销用户"""
        self.logger.info("注销用户")
        os.system("shutdown /l")
    
    def go_back_in_start_menu(self):
        """在开始菜单程序列表中返回上一级目录"""
        parent_path = os.path.dirname(self.current_path)
        # 确保父路径有效且不低于默认起始路径
        if parent_path and parent_path != self.current_path and parent_path.startswith(self.default_start_menu_path):
            self.current_path = parent_path
            self.logger.debug(f"返回到文件夹: {self.current_path}")
            self.refresh_program_list()
        elif parent_path == self.default_start_menu_path:
             # 如果父路径就是默认路径，也允许返回
            self.current_path = parent_path
            self.logger.debug(f"返回到顶层文件夹: {self.current_path}")
            self.refresh_program_list()
        else:
            self.logger.warning(f"无法返回上一级，当前路径: {self.current_path}, 父路径: {parent_path}")

    def toggle_visibility(self, button_pos):
        """切换开始菜单的可见性"""
        if self.is_visible:
            self.hide()
            self.is_visible = False
            self.logger.debug("隐藏开始菜单")
        else:
            # 重置当前路径为默认路径
            self.current_path = self.default_start_menu_path
            self.refresh_program_list()
            
            # 获取主屏幕
            primary_screen = self.display_manager.get_primary_screen()
            
            # 计算菜单位置（在开始按钮正上方）
            x = button_pos.x()
            y = primary_screen['y'] + primary_screen['height'] - self.height() - self.taskbar.taskbar_height
            
            self.move(x, y)
            self.show()
            self.is_visible = True
            self.logger.debug("显示开始菜单")
    
    def hideEvent(self, event):
        """处理隐藏事件"""
        self.is_visible = False
        super().hideEvent(event)

    def find_program_list_scroll_area(self):
        """Helper function to find the QScrollArea containing the program list."""
        # Iterate through main layout items to find the QScrollArea
        if self.layout(): # Ensure layout exists
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item:
                    widget = item.widget()
                    if isinstance(widget, QScrollArea):
                        # Heuristic: Assume the first QScrollArea found in the main layout is the program list
                        return widget
        return None

    def handle_search_focus_in(self, line_edit, event):
        """Handle focus in event for the search edit."""
        scroll_area = self.find_program_list_scroll_area()
        if scroll_area:
            scroll_area.hide()
            self.logger.debug("Program list scroll area hidden.")
        else:
            self.logger.warning("Could not find program list scroll area to hide.")
        self.search_window.show()
        # Call original focusInEvent if needed, though QLineEdit's default is likely fine
        QLineEdit.focusInEvent(line_edit, event)


    def handle_search_focus_out(self, line_edit, event):
        """Handle focus out event for the search edit."""
        # Check if focus is moving to the search window itself or one of its children
        focused_widget = QApplication.focusWidget()
        if focused_widget and (focused_widget == self.search_window or self.search_window.isAncestorOf(focused_widget)):
             self.logger.debug("Focus moved to search window, not hiding list yet.")
             QLineEdit.focusOutEvent(line_edit, event) # Let default handler run
             return # Don't hide search window or show list yet

        self.logger.debug("Search edit lost focus to something other than search window.")
        self.search_window.hide()
        scroll_area = self.find_program_list_scroll_area()
        if scroll_area:
            scroll_area.show()
            self.logger.debug("Program list scroll area shown.")
        else:
             self.logger.warning("Could not find program list scroll area to show.")
        # Call original focusOutEvent if needed
        QLineEdit.focusOutEvent(line_edit, event)

    def handle_search_window_closed(self):
        """Handle the search window being closed explicitly."""
        self.logger.debug("Search window closed signal received.")
        scroll_area = self.find_program_list_scroll_area()
        if scroll_area and not scroll_area.isVisible():
            scroll_area.show()
            self.logger.debug("Program list scroll area shown due to search window close.")
        # Ensure focus returns to the start menu or taskbar appropriately
        # This might need more sophisticated focus management depending on desired UX
        self.activateWindow() # Try to bring focus back to start menu
    
    def refresh_program_list(self):
        """刷新程序列表"""
        # 清除旧的程序列表
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QScrollArea):
                # 找到程序列表区域，重新创建内容
                scroll_area = widget
                
                # 创建包含滚动区域和顶部按钮的新容器
                content_widget = QWidget()
                content_layout = QVBoxLayout(content_widget)
                content_layout.setContentsMargins(0, 0, 0, 0)
                content_layout.setSpacing(10)

                # 添加顶部按钮区域 (返回和 UWP)
                top_button_layout = QHBoxLayout()
                top_button_layout.setSpacing(10)

                # 添加返回按钮 (如果不在根目录)
                if self.current_path != self.default_start_menu_path:
                    self.back_button = QToolButton()
                    self.back_button.setText('返回上级')
                    self.back_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'back.svg')))
                    self.back_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
                    self.back_button.setStyleSheet(
                        "QToolButton {background-color: #3E3E42; color: white; border: none; border-radius: 3px; padding: 8px;}"
                        "QToolButton:hover {background-color: #505054;}"
                    )
                    self.back_button.clicked.connect(self.go_back)
                    top_button_layout.addWidget(self.back_button)
                else:
                     # 添加占位符以保持 UWP 按钮位置
                    top_button_layout.addStretch(1)

                top_button_layout.addStretch(1) # 添加弹性空间将按钮推向两侧

                content_layout.addLayout(top_button_layout)  # 将顶部按钮布局添加到内容布局

                # 创建新的程序列表网格
                program_widget = QWidget()
                program_layout = QGridLayout(program_widget)
                program_layout.setContentsMargins(0, 0, 0, 0)
                program_layout.setSpacing(10)

                # 添加UWP应用入口
                uwp_button = QPushButton("UWP 应用")
                uwp_button.setStyleSheet(
                    "QPushButton {background-color: #3E3E42; color: white; border: none; border-radius: 3px; padding: 8px;}"
                    "QPushButton:hover {background-color: #505054;}"
                )
                uwp_button.clicked.connect(self.show_uwp_apps)
                # 添加返回按钮
                if self.current_path != os.path.expanduser('~'):
                    back_button = QToolButton()
                    back_button.setText('返回上级')
                    back_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'back.svg')))
                    back_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
                    back_button.setStyleSheet(
                        "QToolButton {background-color: #3E3E42; color: white; border: none; border-radius: 3px; padding: 8px;}"
                        "QToolButton:hover {background-color: #505054;}"
                    )
                    back_button.clicked.connect(self.go_back)
                    program_layout.addWidget(back_button, 0, 0, 1, 3)
                else:
                    program_layout.addWidget(uwp_button, 0, 0, 1, 3)
                
                # 遍历当前目录 - 从第0行开始
                row = 0
                col = 0
                max_cols = 3
                
                for item in os.listdir(self.current_path):
                    item_path = os.path.join(self.current_path, item)
                    name = os.path.splitext(item)[0]
                    
                    # 跳过名为 "UWP 应用" 的项，因为它已在顶部按钮栏
                    if name == "UWP 应用":
                        continue
                    
                    # 判断是文件夹还是程序
                    icon_type = "folder" if os.path.isdir(item_path) else "program"
                    
                    # 添加按钮
                    self.add_program_button(program_layout, row, col, name, icon_type, item_path)
                    
                    # 更新行列位置
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                
                program_widget.setLayout(program_layout)
                
                # 创建新的滚动区域并设置其内容
                new_scroll_area = QScrollArea()
                new_scroll_area.setWidgetResizable(True)
                new_scroll_area.setStyleSheet(
                    "QScrollArea {border: none; background-color: transparent;}"
                    "QScrollBar:vertical {background-color: #2D2D30; width: 10px;}"
                    "QScrollBar::handle:vertical {background-color: #3E3E42; border-radius: 5px;}"
                    "QScrollBar::handle:vertical:hover {background-color: #505054;}"
                )
                new_scroll_area.setWidget(program_widget)
                
                content_layout.addWidget(new_scroll_area) # 将滚动区域添加到内容布局
                
                # 替换旧的滚动区域的 widget
                scroll_area.setWidget(content_widget)
                break # 找到并处理完滚动区域后退出循环
        
    def set_svg_icon(self, button, svg_content):
        """设置SVG图标并保持高分辨率渲染"""
        try:
            # 将SVG内容转换为字节数据
            svg_data = svg_content.encode('utf-8')
            
            # 创建SVG渲染器
            renderer = QSvgRenderer(svg_data)
            
            # 创建适配设备像素比的pixmap
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.transparent)
            
            # 高质量抗锯齿渲染
            painter = QPainter(pixmap)
            painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
            renderer.render(painter)
            painter.end()
            
            # 创建图标并设置
            icon = QIcon(pixmap)
            button.setIcon(icon)
            button.setIconSize(QSize(32, 32))
        except Exception as e:
            self.logger.error(f"SVG图标加载失败: {str(e)}")
            # 回退到系统图标
            button.setIcon(QFileIconProvider().icon(QFileIconProvider.File))