#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 桌面管理模块
负责实现基础桌面功能，包括桌面图标显示、右键菜单等
"""

import os
from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QVBoxLayout, 
                             QWidget, QLabel, QMenu, QAction, QFileDialog,
                             QListView, QMessageBox)
from PyQt5.QtCore import Qt, QSize, QPoint, QRect, QDir
from PyQt5.QtGui import QIcon, QPixmap, QCursor
from PyQt5.QtWidgets import QFileSystemModel


class Desktop(QMainWindow):
    """桌面管理类，负责显示和管理桌面"""
    
    def __init__(self, display_manager):
        super().__init__()
        self.display_manager = display_manager
        self.screens = self.display_manager.get_screens()
        self.desktop_widgets = []
        self.file_models = []  # 存储每个屏幕的文件系统模型
        self.file_views = []   # 存储每个屏幕的文件视图
        self.taskbar = None  # 将在main.py中设置
        self.last_taskbar_hidden_state = None  # 记录上一次任务栏隐藏状态
        self.last_taskbar_height = None  # 记录上一次任务栏高度
        
        # 初始化日志记录器
        from log import Logger
        self.logger = Logger()
        self.logger.info("桌面管理器初始化")
        
        # 初始化桌面
        self.init_desktop()
        
    def init_desktop(self):
        """初始化桌面界面"""
        # 设置窗口标题
        self.setWindowTitle("BetterExplorer Desktop")
        
        # 获取桌面路径
        self.desktop_path = os.path.join(os.environ.get('USERPROFILE'), 'Desktop')
        
        # 确保桌面路径存在
        if not os.path.exists(self.desktop_path):
            self.desktop_path = os.path.join(os.environ.get('USERPROFILE'), '桌面')
        
        # 为每个显示器创建桌面窗口
        for screen_index, screen in enumerate(self.screens):
            desktop_widget = QWidget()
            desktop_widget.setWindowFlags(Qt.FramelessWindowHint)
            desktop_widget.setGeometry(QRect(screen['x'], screen['y'], screen['width'], screen['height']))
            
            # 设置桌面背景
            layout = QVBoxLayout(desktop_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # 创建文件系统模型
            file_model = QFileSystemModel()
            file_model.setRootPath(self.desktop_path)
            file_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
            self.file_models.append(file_model)
            
            # 创建文件视图
            file_view = QListView()
            file_view.setModel(file_model)
            file_view.setRootIndex(file_model.index(self.desktop_path))
            file_view.setViewMode(QListView.IconMode)
            file_view.setIconSize(QSize(48, 48))
            file_view.setSpacing(20)
            file_view.setResizeMode(QListView.Adjust)
            file_view.setWrapping(True)
            file_view.setSelectionMode(QListView.ExtendedSelection)
            file_view.setContextMenuPolicy(Qt.CustomContextMenu)
            file_view.customContextMenuRequested.connect(self.show_context_menu)
            self.file_views.append(file_view)
            
            layout.addWidget(file_view)
            self.desktop_widgets.append(desktop_widget)
    
    def show(self):
        """显示所有桌面窗口"""
        for widget in self.desktop_widgets:
            widget.show()
        
        # 如果任务栏已设置，根据任务栏状态调整桌面大小
        if self.taskbar:
            self.adjust_desktop_size()
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        context_menu = QMenu()
        
        # 添加菜单项
        new_folder_action = QAction("新建文件夹", self)
        new_folder_action.triggered.connect(self.create_new_folder)
        
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh_desktop)
        
        open_file_manager_action = QAction("打开文件管理器", self)
        open_file_manager_action.triggered.connect(self.open_file_manager)
        
        # 将动作添加到菜单
        context_menu.addAction(new_folder_action)
        context_menu.addAction(refresh_action)
        context_menu.addAction(open_file_manager_action)
        
        # 显示菜单
        context_menu.exec_(QCursor.pos())
    
    def create_new_folder(self):
        """创建新文件夹"""
        # 获取当前用户桌面路径
        desktop_path = self.desktop_path
        
        # 弹出对话框获取文件夹名称
        folder_name, ok = QFileDialog.getSaveFileName(self, "新建文件夹", 
                                                  desktop_path, 
                                                  "文件夹")
        
        if ok and folder_name:
            try:
                # 创建新文件夹
                os.makedirs(folder_name, exist_ok=True)
                self.logger.info(f"创建新文件夹: {folder_name}")
                self.refresh_desktop()
            except Exception as e:
                self.logger.error(f"创建文件夹失败: {str(e)}")
                QMessageBox.warning(self, "错误", f"创建文件夹失败: {str(e)}")
    
    def refresh_desktop(self):
        """刷新桌面"""
        # 重新加载桌面图标和背景
        for i, widget in enumerate(self.desktop_widgets):
            # 刷新文件系统模型
            self.file_models[i].setRootPath(self.desktop_path)
            # 刷新视图
            self.file_views[i].setRootIndex(self.file_models[i].index(self.desktop_path))
            widget.update()
        self.logger.debug("刷新桌面")
    
    def open_file_manager(self):
        """打开文件管理器"""
        # 创建文件管理器实例
        from file_manager import FileManager
        file_manager = FileManager()
        
        # 显示文件管理器窗口
        file_manager.show()
        
        # 保存文件管理器实例，防止被垃圾回收
        self.file_manager_instance = file_manager
    
    def set_taskbar(self, taskbar):
        """设置任务栏引用"""
        self.taskbar = taskbar
    
    def adjust_desktop_size(self):
        """根据任务栏状态调整桌面大小"""
        if not self.taskbar:
            return
            
        # 获取任务栏高度和是否隐藏的状态
        taskbar_height = self.taskbar.taskbar_height
        is_taskbar_hidden = self.taskbar.is_taskbar_hidden()
        
        # 只在任务栏隐藏状态或高度发生变化时更新桌面大小
        if self.last_taskbar_hidden_state != is_taskbar_hidden or self.last_taskbar_height != taskbar_height:
            self.last_taskbar_hidden_state = is_taskbar_hidden
            self.last_taskbar_height = taskbar_height
            
            for i, screen in enumerate(self.screens):
                desktop_widget = self.desktop_widgets[i]
                
                # 计算桌面高度
                if is_taskbar_hidden:
                    # 如果任务栏隐藏，桌面占据整个屏幕
                    desktop_height = screen['height']
                else:
                    # 如果任务栏显示，桌面高度需要减去任务栏高度
                    desktop_height = screen['height'] - taskbar_height
                
                # 调整桌面大小
                desktop_widget.setGeometry(QRect(
                    screen['x'],
                    screen['y'],
                    screen['width'],
                    desktop_height
                ))
                
                # 刷新桌面
                desktop_widget.update()
            self.logger.info(f"调整桌面大小: 任务栏{'隐藏' if is_taskbar_hidden else '显示'}, 高度={taskbar_height}")