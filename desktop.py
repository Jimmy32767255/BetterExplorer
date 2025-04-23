#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 桌面管理模块
负责实现基础桌面功能，包括桌面图标显示、右键菜单等
"""

import os
import shutil
from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QVBoxLayout, 
                             QWidget, QLabel, QMenu, QAction, QFileDialog,
                             QListView, QMessageBox, QInputDialog)
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
        
        # 从设置中获取桌面路径
        from settings import Settings
        self.desktop_path = Settings.get_setting("desktop_path", "")
        
        # 如果未设置或路径不存在，使用默认路径
        if not self.desktop_path or not os.path.exists(self.desktop_path):
            self.desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            if not os.path.exists(self.desktop_path):
                self.desktop_path = os.path.join(os.path.expanduser('~'), '桌面')
                if not os.path.exists(self.desktop_path):
                    self.desktop_path = os.path.expanduser('~')
        
        # 为每个显示器创建桌面窗口
        for screen_index, screen in enumerate(self.screens):
            desktop_widget = QWidget()
            desktop_widget.setWindowFlags(Qt.WindowFlags(Qt.FramelessWindowHint))
            desktop_widget.setGeometry(QRect(screen['x'], screen['y'], screen['width'], screen['height']))
            
            # 设置桌面背景
            layout = QVBoxLayout(desktop_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # 创建文件系统模型
            file_model = QFileSystemModel()
            file_model.setRootPath(self.desktop_path)
            file_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
            file_model.setOption(QFileSystemModel.DontUseCustomDirectoryIcons)
            file_model.setOption(QFileSystemModel.DontWatchForChanges)
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
            file_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
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
        # 获取触发右键菜单的QListView实例
        view = self.sender()
        if not isinstance(view, QListView):
            return
            
        # 使用QListView的itemAt方法获取当前位置的项
        item = view.indexAt(position)
        file_path = view.model().filePath(item) if item.isValid() else None if item.isValid() else None
        
        context_menu = QMenu()
        
        if file_path:
            # 文件/文件夹右键菜单
            open_action = QAction("打开", self)
            open_action.triggered.connect(lambda: self.open_file(file_path))
            
            copy_action = QAction("复制", self)
            copy_action.triggered.connect(lambda: self.copy_file(file_path))
            
            cut_action = QAction("剪切", self)
            cut_action.triggered.connect(lambda: self.cut_file(file_path))
            
            paste_action = QAction("粘贴", self)
            paste_action.triggered.connect(self.paste_file)
            
            delete_action = QAction("删除", self)
            delete_action.triggered.connect(lambda: self.delete_file(file_path))
            
            rename_action = QAction("重命名", self)
            rename_action.triggered.connect(lambda: self.rename_file(file_path))
            
            context_menu.addAction(open_action)
            context_menu.addAction(copy_action)
            context_menu.addAction(cut_action)
            context_menu.addAction(paste_action)
            context_menu.addAction(delete_action)
            context_menu.addAction(rename_action)
        else:
            # 空白处右键菜单
            new_folder_action = QAction("新建文件夹", self)
            new_folder_action.triggered.connect(self.create_new_folder)
            
            refresh_action = QAction("刷新", self)
            refresh_action.triggered.connect(self.refresh_desktop)
            
            open_file_manager_action = QAction("打开文件管理器", self)
            open_file_manager_action.triggered.connect(self.open_file_manager)
            
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

    def copy_file(self, file_path):
        """复制文件到剪贴板"""
        self.clipboard_file = file_path
        self.clipboard_action = "copy"
        self.logger.info(f"已复制文件: {file_path}")

    def cut_file(self, file_path):
        """剪切文件到剪贴板"""
        self.clipboard_file = file_path
        self.clipboard_action = "cut"
        self.logger.info(f"已剪切文件: {file_path}")

    def open_file(self, file_path):
        """打开文件或文件夹"""
        if os.path.isdir(file_path):
            # 创建文件管理器实例并打开目标路径
            from file_manager import FileManager
            file_manager = FileManager()
            file_manager.navigate_to(file_path)
            file_manager.show()
            self.file_manager_instance = file_manager
        else:
            try:
                os.startfile(file_path)
                self.logger.info(f"打开文件: {file_path}")
            except Exception as e:
                self.logger.error(f"打开文件失败: {file_path}, 错误: {str(e)}")
                QMessageBox.warning(self, "错误", f"无法打开文件: {str(e)}")

    def delete_file(self, file_path):
        """删除文件"""
        reply = QMessageBox.question(self, "确认删除", f"确定要删除 {os.path.basename(file_path)} 吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                self.refresh_desktop()
                self.logger.info(f"删除成功: {file_path}")
            except Exception as e:
                self.logger.error(f"删除失败: {str(e)}")
                QMessageBox.warning(self, "错误", f"删除失败: {str(e)}")

    def rename_file(self, file_path):
        """重命名文件"""
        old_name = os.path.basename(file_path)
        new_name, ok = QInputDialog.getText(self, "重命名", "新名称:", text=old_name)
        if ok and new_name:
            try:
                new_path = os.path.join(os.path.dirname(file_path), new_name)
                os.rename(file_path, new_path)
                self.refresh_desktop()
                self.logger.info(f"重命名成功: {old_name} -> {new_name}")
            except Exception as e:
                self.logger.error(f"重命名失败: {str(e)}")
                QMessageBox.warning(self, "错误", f"重命名失败: {str(e)}")

    def paste_file(self):
        """粘贴剪贴板中的文件"""
        if not hasattr(self, 'clipboard_file') or not hasattr(self, 'clipboard_action'):
            return

        try:
            file_name = os.path.basename(self.clipboard_file)
            target_path = os.path.join(self.desktop_path, file_name)

            if self.clipboard_action == "copy":
                if os.path.isdir(self.clipboard_file):
                    shutil.copytree(self.clipboard_file, target_path)
                else:
                    shutil.copy2(self.clipboard_file, target_path)
            elif self.clipboard_action == "cut":
                shutil.move(self.clipboard_file, target_path)
                # 清空剪贴板
                self.clipboard_file = None
                self.clipboard_action = None

            self.refresh_desktop()
            self.logger.info(f"文件粘贴成功: {target_path}")
        except Exception as e:
            self.logger.error(f"文件粘贴失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"粘贴操作失败: {str(e)}")