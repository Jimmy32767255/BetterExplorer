#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 文件管理模块
负责实现文件浏览、复制、移动、删除等基本文件操作功能
"""

import os
import shutil
import psutil
import subprocess
from PyQt5.QtWidgets import (QMainWindow, QTreeView, QListView, QFileSystemModel,
                             QVBoxLayout, QHBoxLayout, QWidget, QToolBar, 
                             QAction, QMenu, QInputDialog, QMessageBox, QFileDialog,
                             QComboBox)
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QIcon


class FileManager(QMainWindow):
    """文件管理器类，提供文件浏览和操作功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = os.path.expanduser("~")
        
        # 初始化日志记录器
        from log import Logger
        self.logger = Logger()
        self.logger.info("文件管理器初始化")
        
        # 检查是否需要关闭系统资源管理器
        from settings import Settings
        if Settings.get_setting("disable_system_explorer", False):
            self.stop_system_explorer()
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("BetterExplorer - 文件管理器")
        self.resize(800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建驱动器选择组件
        self.drive_combo = QComboBox()
        self.update_drive_list()
        self.drive_combo.currentTextChanged.connect(self.on_drive_changed)
        
        # 创建文件系统模型
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.model.setOption(QFileSystemModel.DontUseCustomDirectoryIcons)
        self.model.setOption(QFileSystemModel.DontWatchForChanges)
        
        # 创建列表视图
        self.list_view = QListView()
        self.list_view.setModel(self.model)
        self.list_view.setRootIndex(self.model.index(self.current_path))
        self.list_view.doubleClicked.connect(self.on_list_view_double_clicked)
        
        # 设置右键菜单
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)
        
        # 添加组件到布局
        main_layout.addWidget(self.drive_combo)
        main_layout.addWidget(self.list_view)
        
        # 创建工具栏
        self.create_toolbar()

    def update_drive_list(self):
        """更新驱动器列表"""
        self.drive_combo.clear()
        for drive in QDir.drives():
            self.drive_combo.addItem(drive.absolutePath())

    def on_drive_changed(self, drive):
        """处理驱动器切换事件"""
        if drive:
            self.navigate_to(drive)
            self.list_view.setRootIndex(self.model.index(drive))
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("文件操作")
        self.addToolBar(toolbar)
        
        # 后退按钮
        back_action = QAction("后退", self)
        back_action.triggered.connect(self.go_back)
        toolbar.addAction(back_action)
        
        # 前进按钮
        forward_action = QAction("前进", self)
        forward_action.triggered.connect(self.go_forward)
        toolbar.addAction(forward_action)
        
        # 上级目录按钮
        up_action = QAction("上级目录", self)
        up_action.triggered.connect(self.go_up)
        toolbar.addAction(up_action)
        
        # 刷新按钮
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh)
        toolbar.addAction(refresh_action)
        
    def on_list_view_double_clicked(self, index):
        """处理列表视图双击事件"""
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.navigate_to(path)
        else:
            # 打开文件（这里可以根据文件类型选择不同的打开方式）
            os.startfile(path)
    
    def navigate_to(self, path):
        """导航到指定路径"""
        self.current_path = path
        self.list_view.setRootIndex(self.model.index(path))
        self.setWindowTitle(f"BetterExplorer - {path}")
    
    def go_back(self):
        """返回上一个访问的目录"""
        # 这里需要实现历史记录功能
        pass
    
    def go_forward(self):
        """前进到下一个访问的目录"""
        # 这里需要实现历史记录功能
        pass
    
    def go_up(self):
        """返回上级目录"""
        parent_path = os.path.dirname(self.current_path)
        if parent_path:
            self.navigate_to(parent_path)
    
    def refresh(self):
        """刷新当前视图"""
        self.list_view.setRootIndex(self.model.index(self.current_path))
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        index = self.list_view.indexAt(position)
        if not index.isValid():
            return
        
        file_path = self.model.filePath(index)
        
        context_menu = QMenu()
        
        # 添加菜单项
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
        
        # 将动作添加到菜单
        context_menu.addAction(open_action)
        context_menu.addSeparator()
        context_menu.addAction(copy_action)
        context_menu.addAction(cut_action)
        context_menu.addAction(paste_action)
        context_menu.addSeparator()
        context_menu.addAction(delete_action)
        context_menu.addAction(rename_action)
        
        # 显示菜单
        context_menu.exec_(self.list_view.mapToGlobal(position))
    
    def open_file(self, file_path):
        """打开文件或目录"""
        if os.path.isdir(file_path):
            self.navigate_to(file_path)
        else:
            try:
                os.startfile(file_path)
                self.logger.info(f"打开文件: {file_path}")
            except Exception as e:
                self.logger.error(f"打开文件失败: {file_path}, 错误: {str(e)}")
    
    def copy_file(self, file_path):
        """复制文件"""
        self.clipboard_file = file_path
        self.clipboard_action = "copy"
    
    def cut_file(self, file_path):
        """剪切文件"""
        self.clipboard_file = file_path
        self.clipboard_action = "cut"
    
    def paste_file(self):
        """粘贴文件"""
        if not hasattr(self, 'clipboard_file') or not hasattr(self, 'clipboard_action'):
            return
        
        source_path = self.clipboard_file
        file_name = os.path.basename(source_path)
        target_path = os.path.join(self.current_path, file_name)
        
        try:
            if self.clipboard_action == "copy":
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, target_path)
                else:
                    shutil.copy2(source_path, target_path)
            elif self.clipboard_action == "cut":
                shutil.move(source_path, target_path)
                self.clipboard_file = None
                self.clipboard_action = None
            
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"操作失败: {str(e)}")
    
    def delete_file(self, file_path):
        """删除文件"""
        reply = QMessageBox.question(self, "确认删除", 
                                    f"确定要删除 {os.path.basename(file_path)} 吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                self.logger.info(f"删除文件: {file_path}")
                self.refresh()
            except Exception as e:
                self.logger.error(f"删除文件失败: {file_path}, 错误: {str(e)}")
                QMessageBox.warning(self, "错误", f"删除失败: {str(e)}")
    
    def rename_file(self, file_path):
        """重命名文件"""
        old_name = os.path.basename(file_path)
        new_name, ok = QInputDialog.getText(self, "重命名", "新名称:", text=old_name)
        
        if ok and new_name:
            try:
                new_path = os.path.join(os.path.dirname(file_path), new_name)
                os.rename(file_path, new_path)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"重命名失败: {str(e)}")
    
    def stop_system_explorer(self):
        """停止系统资源管理器进程"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == 'explorer.exe':
                    proc.kill()
            self.logger.info("系统资源管理器已停止")
        except Exception as e:
            self.logger.error(f"停止系统资源管理器时出错: {str(e)}")
    
    def start_system_explorer(self):
        """启动系统资源管理器进程"""
        try:
            subprocess.Popen('explorer.exe')
            self.logger.info("系统资源管理器已启动")
        except Exception as e:
            self.logger.error(f"启动系统资源管理器时出错: {str(e)}")