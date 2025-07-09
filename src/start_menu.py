#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 开始菜单模块
负责实现开始菜单功能，包括程序列表、搜索框和电源选项
"""

import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QScrollArea, QFrame, QGridLayout,
                             QToolButton, QMenu, QAction, QApplication, QStackedLayout)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QCursor
from PyQt5.QtSvg import QSvgRenderer
from icons import file_manager_icon, settings_icon, power_icon, back_icon, uwp_icon
from PyQt5.QtWidgets import QFileIconProvider
from log import get_logger

logger = get_logger()
from uwp_app_menu import UWPAppFetcher, launch_uwp_app
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
        self.is_showing_uwp_apps = False # 新增状态变量，表示当前是否正在显示UWP应用
        
        # 初始化UI
        # 创建搜索组件实例
        self.search_widget = SearchWindow(self)
        
        # 初始化 UWP 应用获取器
        self.uwp_app_fetcher = UWPAppFetcher()
        self.uwp_app_fetcher.finished.connect(self.on_uwp_apps_fetched)
        self.uwp_app_fetcher.error.connect(self.on_uwp_apps_error)

        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置菜单大小
        self.setFixedSize(775, 730)
        
        # 设置菜单样式
        self.setStyleSheet(
            "background-color: #2D2D30; color: white; border: 1px solid #3F3F46;"
        )
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 添加搜索组件到主布局
        main_layout.addWidget(self.search_widget)
        # 设置搜索组件的占位符文本
        self.search_widget.search_input.setPlaceholderText("搜索应用、文件和设置")
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #3F3F46;")
        main_layout.addWidget(separator)

        # 添加顶部按钮区域 (返回和 UWP)
        top_button_layout = QHBoxLayout()
        top_button_layout.setSpacing(10)

        # 创建返回按钮 (不立即添加到布局)
        self.back_button = QToolButton()
        self.back_button.setText('返回上级')
        self.back_button.setIcon(QIcon(back_icon))
        self.back_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.back_button.setStyleSheet(
            "QToolButton {background-color: #3E3E42; color: white; border: none; border-radius: 3px; padding: 8px;}"
            "QToolButton:hover {background-color: #505054;}"
        )
        self.back_button.clicked.connect(self.go_back)
        top_button_layout.addWidget(self.back_button)
        self.back_button.setVisible(False)
        
        # 添加 UWP 应用入口按钮
        self.uwp_button = QToolButton()
        self.uwp_button.setText('UWP 应用')
        self.uwp_button.setIcon(QIcon(uwp_icon))
        self.uwp_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.uwp_button.setStyleSheet(
            "QToolButton {background-color: #3E3E42; color: white; border: none; border-radius: 3px; padding: 8px;}"
            "QToolButton:hover {background-color: #505054;}"
        )
        self.uwp_button.clicked.connect(self.show_uwp_apps)
        top_button_layout.addWidget(self.uwp_button)

        top_button_layout.addStretch(1)
        self.top_button_layout = top_button_layout # 保存引用
        main_layout.addLayout(self.top_button_layout)

        # 创建程序列表容器
        self.program_widget = QWidget()

        self.program_layout = QGridLayout(self.program_widget)
        self.program_layout.setContentsMargins(0, 0, 0, 0)
        self.program_layout.setSpacing(10)
        
        # 添加程序列表区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            "QScrollArea {border: none; background-color: transparent;}"
            "QScrollBar:vertical {background-color: #2D2D30; width: 10px;}"
            "QScrollBar::handle:vertical {background-color: #3E3E42; border-radius: 5px;}"
            "QScrollBar::handle:vertical:hover {background-color: #505054;}"
        )
        
        self.scroll_area.setWidget(self.program_widget)
        
        # 创建一个堆叠布局来管理程序列表和搜索结果列表
        self.stacked_layout = QStackedLayout()
        self.stacked_layout.addWidget(self.scroll_area) # 索引 0: 程序列表
        self.stacked_layout.addWidget(self.search_widget.result_list) # 索引 1: 搜索结果列表
        
        main_layout.addLayout(self.stacked_layout, 1) # 占据大部分空间
        
        # 默认显示程序列表
        self.stacked_layout.setCurrentIndex(0)

        # 连接搜索组件的输入框焦点事件
        self.search_widget.search_input.textChanged.connect(self.search_widget.perform_search)
        self.search_widget.search_input.focusInEvent = lambda e, le=self.search_widget.search_input: self.handle_search_focus_in(le, e)
        self.search_widget.search_input.focusOutEvent = lambda e, le=self.search_widget.search_input: self.handle_search_focus_out(le, e)


        
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
        # 添加用户上下文菜单
        user_menu = QMenu(self)
        lock_action = QAction("锁定", self)
        sign_out_action = QAction("注销", self)
        user_menu.addAction(lock_action)
        user_menu.addAction(sign_out_action)
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
        
        self.bottom_layout = bottom_layout # 保存引用以便后续操作
        main_layout.addLayout(self.bottom_layout)
    
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
        """显示UWP应用列表或返回普通开始菜单"""
        if self.is_showing_uwp_apps:
            # 如果当前正在显示UWP应用，则返回普通开始菜单
            self.logger.info("返回普通开始菜单...")
            self.is_showing_uwp_apps = False
            self.refresh_program_list()
            self.uwp_button.setText("UWP 应用")
            self.uwp_button.clicked.disconnect()
            self.uwp_button.clicked.connect(self.show_uwp_apps)
            self.uwp_button.setEnabled(True)
        else:
            # 如果当前显示普通开始菜单，则显示UWP应用列表
            self.logger.info("开始获取UWP应用列表...")
            self.is_showing_uwp_apps = True
            # 启动异步获取
            self.uwp_app_fetcher.start()
            # 暂时禁用UWP按钮，防止重复点击
            self.uwp_button.setEnabled(False)
            self.uwp_button.setText("正在加载UWP应用...")

    def on_uwp_apps_fetched(self, apps):
        """处理UWP应用列表获取完成"""
        self.logger.info(f"成功获取到 {len(apps)} 个UWP应用。")
        self.uwp_button.setEnabled(True)
        self.uwp_button.setText("关闭 UWP 应用菜单")
        # 确保点击事件连接到show_uwp_apps，以便下次点击时可以返回普通菜单
        self.uwp_button.clicked.disconnect()
        self.uwp_button.clicked.connect(self.show_uwp_apps)
        
        # 确保滚动区域存在
        if not self.scroll_area:
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setStyleSheet(
                "QScrollArea {border: none; background-color: transparent;}"
                "QScrollBar:vertical {background-color: #2D2D30; width: 10px;}"
                "QScrollBar::handle:vertical {background-color: #3E3E42; border-radius: 5px;}"
                "QScrollBar::handle:vertical:hover {background-color: #505054;}"
            )
            
        # 清除现有程序列表
        self.clear_program_buttons()
        
        # 强制重新创建 program_widget 和 program_layout 以确保正确初始化
        self.program_widget = QWidget()
        self.program_layout = QGridLayout(self.program_widget)
        self.program_layout.setContentsMargins(0, 0, 0, 0)
        self.program_layout.setSpacing(10)
        
        # 将新的 program_widget 设置到滚动区域中
        self.scroll_area.setWidget(self.program_widget)
        
        self.logger.info(f"UWP应用程序列表布局已重新初始化")
        
        # 将UWP应用添加到程序列表
        self.add_uwp_apps_to_program_list(apps)

    def clear_program_buttons(self):
        """清除所有程序按钮"""
        # 直接使用 self.program_layout 清除按钮
        if self.program_layout:
            while self.program_layout.count():
                item = self.program_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def on_uwp_apps_error(self, error_message):
        """处理UWP应用列表获取错误"""
        self.logger.error(f"获取UWP应用失败: {error_message}")
        self.is_showing_uwp_apps = False # 重置状态
        self.uwp_button.setEnabled(True)
        self.uwp_button.setText("UWP 应用") # 恢复文本
        self.uwp_button.clicked.disconnect() # 断开旧连接
        self.uwp_button.clicked.connect(self.show_uwp_apps) # 重新连接到show_uwp_apps
        # 刷新程序列表，确保显示的是普通开始菜单内容
        self.refresh_program_list()

    def add_uwp_apps_to_program_list(self, apps):
        """将UWP应用添加到程序列表"""
        # 直接使用 self.program_layout
        if self.program_layout is None:
            self.logger.error("程序列表布局未初始化。")
            return
        
        self.logger.info(f"开始添加 {len(apps)} 个UWP应用到程序列表")

        # 初始化行和列
        row = 0
        col = 0
        max_cols = 5  # 每行显示5个应用

        for app in apps:
            # 为每个UWP应用创建一个按钮
            button = QToolButton()
            button.setText(app['name'])
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setFixedSize(100, 80)
            # TODO: 为UWP应用设置图标，可能需要额外的逻辑来获取UWP应用的图标
            # button.setIcon(QIcon("path/to/uwp_icon.png"))
            button.setStyleSheet(
                "QToolButton {background-color: transparent; color: white; border: none; text-align: center;}"
                "QToolButton:hover {background-color: #3E3E42; border-radius: 5px;}"
                "QToolButton:pressed {background-color: #0078D7;}"
            )
            button.setProperty('is_uwp_app', True)
            button.clicked.connect(lambda checked, app_id=app['appid']: launch_uwp_app(app_id))

            self.program_layout.addWidget(button, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # 刷新布局以显示新添加的按钮
        self.program_layout.update()

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
            file_manager = FileManager()
            file_manager.show()
            self.file_manager_instance = file_manager # 防止被垃圾回收
        elif program_name == "设置":
            settings_window = Settings()
            settings_window.show()
            self.settings_instance = settings_window # 防止被垃圾回收
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

    def show_and_focus_search(self):
        """显示开始菜单并让搜索框获得焦点"""
        self.logger.info("显示开始菜单并让搜索框获得焦点")
        # 如果开始菜单没有显示，则显示它
        if not self.isVisible():
            # 获取任务栏的位置信息，以便将开始菜单显示在正确的位置
            # 这里需要根据实际任务栏的位置来调整，例如，如果任务栏在底部
            # 则开始菜单应该从屏幕底部向上弹出
            screen_rect = QApplication.desktop().screenGeometry()
            taskbar_height = self.taskbar.height() if self.taskbar else 0
            # 计算开始菜单的显示位置
            x = 0 # 假设从屏幕左侧开始
            y = screen_rect.height() - taskbar_height - self.height() # 菜单在任务栏上方
            self.move(x, y)
            self.show()
            self.is_visible = True
        
        # 确保搜索组件的输入框获得焦点
        self.search_widget.search_input.setFocus()
        # 模拟搜索框获得焦点事件，以触发隐藏其他元素和显示搜索结果列表的逻辑
        self.handle_search_focus_in(self.search_widget.search_input, None) # None for event as it's simulated
    
    def show_power_menu(self):
        """显示电源菜单"""
        power_menu = QMenu(self)
        power_menu.setStyleSheet("QMenu {background-color: #2D2D30; color: white; border: 1px solid #3F3F46;}QMenu::item {padding: 5px 20px;}QMenu::item:selected {background-color: #3E3E42;}")
        
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

    def system_lock(self):
        """系统锁定"""
        self.logger.info("系统锁定")
        os.system("rundll32.exe user32.dll,LockWorkStation")
        
    def system_sign_out(self):
        """系统注销"""
        self.logger.info("系统注销")
        os.system("shutdown /l")

    def show_user_menu(self, pos):
        """显示用户上下文菜单"""
        user_menu = QMenu(self)
        user_menu.setStyleSheet("QMenu {background-color: #2D2D30; color: white; border: 1px solid #3F3F46;}QMenu::item {padding: 5px 20px;}QMenu::item:selected {background-color: #3E3E42;}")
        
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
    
    def go_back_in_start_menu(self):
        """在开始菜单程序列表中返回上一级目录"""
        parent_path = os.path.dirname(self.current_path)
        # 确保父路径有效且不低于默认起始路径
        if parent_path and parent_path != self.current_path and parent_path.startswith(self.default_start_menu_path):
            self.current_path = parent_path
            self.logger.debug(f"返回到文件夹: {self.current_path}")
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
            
            # 计算菜单位置(在开始按钮正上方)
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
        """查找程序列表的滚动区域"""
        # 假设滚动区域是 main_layout 的第二个部件
        # 这是一个比较脆弱的方法，如果布局结构改变，可能需要调整
        # 更好的方法是在 init_ui 中保存 scroll_area 的引用
        return self.scroll_area

    def handle_search_focus_in(self, search_edit, event):
        """处理搜索框获得焦点事件"""
        self.logger.debug("搜索框获得焦点")
        # 隐藏开始菜单的其他部分
        for i in range(self.bottom_layout.count()):
            widget = self.bottom_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        for i in range(self.top_button_layout.count()):
            widget = self.top_button_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        # 显示搜索结果列表
        self.stacked_layout.setCurrentIndex(1)
        # 确保搜索组件的输入框获得焦点
        search_edit.setFocus()
        event.accept()

    def handle_search_focus_out(self, search_edit, event):
        """处理搜索框失去焦点事件"""
        # 检查焦点是否转移到搜索组件内部
        if not self.search_widget.geometry().contains(QCursor.pos()):
            # 隐藏搜索结果列表，显示程序列表
            self.stacked_layout.setCurrentIndex(0)
            # 恢复开始菜单的其他部分
            for i in range(self.bottom_layout.count()):
                widget = self.bottom_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
            for i in range(self.top_button_layout.count()):
                widget = self.top_button_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
        event.accept()
    
    def refresh_program_list(self):
        """刷新程序列表"""
        # 清除旧的程序列表
        self.clear_program_buttons()

        # 根据当前路径判断是否显示返回按钮
        if self.current_path == self.default_start_menu_path:
            self.back_button.setVisible(False)
        else:
            self.back_button.setVisible(True)

        # 确保 program_layout 已初始化
        if not self.program_layout:
            self.program_widget = QWidget()
            self.program_layout = QGridLayout(self.program_widget)
            self.program_widget.setLayout(self.program_layout)
            self.program_layout.setContentsMargins(0, 0, 0, 0)
            self.program_layout.setSpacing(10)
            
            # 找到程序列表区域，并设置其内容
            scroll_area = self.find_program_list_scroll_area()
            if scroll_area:
                scroll_area.setWidget(self.program_widget)
            else:
                self.logger.error("未找到程序列表滚动区域。")

        # 遍历当前目录
        row = 0
        col = 0
        max_cols = 5 # Consistent with UWP app display

        for item in os.listdir(self.current_path):
            item_path = os.path.join(self.current_path, item)
            name = os.path.splitext(item)[0]
            
            # 跳过名为 "UWP 应用" 的项，因为它已在顶部按钮栏
            if name == "UWP 应用":
                continue
            
            # 判断是文件夹还是程序
            icon_type = "folder" if os.path.isdir(item_path) else "program"
            
            # 添加按钮
            self.add_program_button(self.program_layout, row, col, name, icon_type, item_path)
            
            # 更新行列位置
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # 确保显示程序列表
        self.stacked_layout.setCurrentIndex(0)
        
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