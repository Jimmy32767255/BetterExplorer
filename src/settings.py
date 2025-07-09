#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 设置模块
负责实现系统设置功能，包括界面设置、行为设置等
"""

import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QCheckBox, QTabWidget,
                             QGroupBox, QMessageBox, QApplication, QLineEdit)
from PyQt5.QtCore import Qt
from log import get_logger

logger = get_logger()



class Settings(QWidget):
    """设置类，提供系统设置功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BetterExplorer 设置")
        self.resize(600, 400)
        
        # 初始化日志记录器
        self.logger = logger
        self.logger.info("设置模块初始化")
        
        # 设置文件路径
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        
        # 加载设置
        self.load_settings()
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口样式
        self.setStyleSheet(
            "background-color: #2D2D30; color: white;"
        )
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建选项卡部件
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(
            "QTabWidget::pane {border: 1px solid #3F3F46; background-color: #2D2D30;}"
            "QTabBar::tab {background-color: #3E3E42; color: white; padding: 8px 16px; margin-right: 2px;}"
            "QTabBar::tab:selected {background-color: #0078D7;}"
            "QTabBar::tab:hover:!selected {background-color: #505054;}"
        )
        
        # 创建界面设置选项卡
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)
        ui_layout.setContentsMargins(10, 10, 10, 10)
        ui_layout.setSpacing(15)
        
        # 创建任务栏设置组
        taskbar_group = QGroupBox("任务栏设置")
        taskbar_group.setStyleSheet(
            "QGroupBox {border: 1px solid #3F3F46; border-radius: 5px; margin-top: 10px; padding-top: 10px;}"
            "QGroupBox::title {subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px;}"
        )
        taskbar_layout = QVBoxLayout(taskbar_group)
        
        # 添加开始按钮居中选项
        self.center_start_button_checkbox = QCheckBox("左侧按钮组居中显示")
        self.center_start_button_checkbox.setChecked(self.settings.get("center_start_button", False))
        self.center_start_button_checkbox.setStyleSheet(
            "QCheckBox {padding: 5px;}"
            "QCheckBox::indicator {width: 15px; height: 15px;}"
            "QCheckBox::indicator:unchecked {background-color: #3E3E42; border: 1px solid #555555;}"
            "QCheckBox::indicator:checked {background-color: #0078D7; border: 1px solid #0078D7;}"
        )
        taskbar_layout.addWidget(self.center_start_button_checkbox)
        
        # 添加任务栏自动隐藏选项
        self.auto_hide_taskbar_checkbox = QCheckBox("任务栏自动隐藏")
        self.auto_hide_taskbar_checkbox.setChecked(self.settings.get("auto_hide_taskbar", False))
        self.auto_hide_taskbar_checkbox.setStyleSheet(
            "QCheckBox {padding: 5px;}"
            "QCheckBox::indicator {width: 15px; height: 15px;}"
            "QCheckBox::indicator:unchecked {background-color: #3E3E42; border: 1px solid #555555;}"
            "QCheckBox::indicator:checked {background-color: #0078D7; border: 1px solid #0078D7;}"
        )
        taskbar_layout.addWidget(self.auto_hide_taskbar_checkbox)
        
        # 添加更多任务栏设置选项（可以根据需要扩展）
        
        ui_layout.addWidget(taskbar_group)
        
        # 添加更多设置组（可以根据需要扩展）
        
        # 添加弹性空间
        ui_layout.addStretch(1)
        
        
        # 添加选项卡添加到选项卡部件
        tab_widget.addTab(ui_tab, "界面设置")
        
        # 添加按钮区域到主布局
        main_layout.addWidget(tab_widget)
        
        # 创建系统设置选项卡
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        system_layout.setContentsMargins(10, 10, 10, 10)
        system_layout.setSpacing(15)
        
        # 创建系统设置组
        system_group = QGroupBox("系统设置")
        system_group.setStyleSheet(
            "QGroupBox {border: 1px solid #3F3F46; border-radius: 5px; margin-top: 10px; padding-top: 10px;}"
            "QGroupBox::title {subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px;}"
        )
        system_layout_group = QVBoxLayout(system_group)
        
        # 添加关闭系统资源管理器选项
        self.disable_system_explorer_checkbox = QCheckBox("启动时关闭系统资源管理器")
        self.disable_system_explorer_checkbox.setChecked(self.settings.get("disable_system_explorer", False))
        self.disable_system_explorer_checkbox.setStyleSheet(
            "QCheckBox {padding: 5px;}"
            "QCheckBox::indicator {width: 15px; height: 15px;}"
            "QCheckBox::indicator:unchecked {background-color: #3E3E42; border: 1px solid #555555;}"
            "QCheckBox::indicator:checked {background-color: #0078D7; border: 1px solid #0078D7;}"
        )
        system_layout_group.addWidget(self.disable_system_explorer_checkbox)
        
        # 添加桌面路径设置
        desktop_path_group = QGroupBox("桌面路径设置")
        desktop_path_group.setStyleSheet(
            "QGroupBox {border: 1px solid #3F3F46; border-radius: 5px; margin-top: 10px; padding-top: 10px;}"
            "QGroupBox::title {subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px;}"
        )
        desktop_path_layout = QVBoxLayout(desktop_path_group)
        
        self.desktop_path_edit = QLineEdit()
        self.desktop_path_edit.setPlaceholderText("请输入桌面路径")
        self.desktop_path_edit.setText(self.settings.get("desktop_path", ""))
        self.desktop_path_edit.setStyleSheet(
            "QLineEdit {background-color: #3E3E42; color: white; border: 1px solid #555555; padding: 5px;}"
        )
        desktop_path_layout.addWidget(self.desktop_path_edit)
        
        system_layout_group.addWidget(desktop_path_group)

                # 添加系统设置组到布局
        system_layout.addWidget(system_group)
        
        # 添加弹性空间
        system_layout.addStretch(1)
        
        # 添加系统设置选项卡
        tab_widget.addTab(system_tab, "系统设置")
        
        # 添加按钮区域到主布局
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignRight)
        
        # 添加保存按钮
        save_button = QPushButton("保存")
        save_button.setFixedSize(80, 30)
        save_button.setStyleSheet(
            "QPushButton {background-color: #0078D7; color: white; border: none; border-radius: 3px;}"
            "QPushButton:hover {background-color: #1C97EA;}"
            "QPushButton:pressed {background-color: #00559B;}"
        )
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        # 添加取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setFixedSize(80, 30)
        cancel_button.setStyleSheet(
            "QPushButton {background-color: #3E3E42; color: white; border: none; border-radius: 3px;}"
            "QPushButton:hover {background-color: #505054;}"
            "QPushButton:pressed {background-color: #0078D7;}"
        )
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # 添加退出按钮
        exit_button = QPushButton("退出程序")
        exit_button.setFixedSize(120, 30)
        exit_button.setStyleSheet(
            "QPushButton {background-color: #E81123; color: white; border: none; border-radius: 3px;}"
            "QPushButton:hover {background-color: #F1707A;}"
            "QPushButton:pressed {background-color: #C50F1F;}"
        )
        exit_button.clicked.connect(self.exit_application)
        
        # 添加系统设置组到布局
        system_layout.addWidget(system_group)
        
        # 添加弹性空间
        system_layout.addStretch(1)
        
        # 添加退出按钮到布局
        button_layout_system = QHBoxLayout()
        button_layout_system.setAlignment(Qt.AlignRight)
        button_layout_system.addWidget(exit_button)
        system_layout.addLayout(button_layout_system)
        
        # 添加系统设置选项卡
        tab_widget.addTab(system_tab, "系统设置")
        
        main_layout.addWidget(tab_widget)
    
    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                self.logger.info("成功加载设置文件")
            else:
                # 默认设置
                self.settings = {
                    "left_buttons_center": False,
                    "disable_system_explorer": False
                }
                self.logger.info("使用默认设置")
        except Exception as e:
            self.logger.error(f"加载设置时出错: {str(e)}")
            # 出错时使用默认设置
            self.settings = {
                "left_buttons_center": False,
                "disable_system_explorer": False,
                "desktop_path": ""
            }
    
    def exit_application(self):
        """退出应用程序"""
        from file_manager import FileManager
        # 创建文件管理器实例以检查系统资源管理器状态
        file_manager = FileManager()
        
        # 如果系统资源管理器被关闭，则重新启动它
        if self.settings.get("disable_system_explorer", False):
            file_manager.start_system_explorer()
        
        # 退出应用程序
        QApplication.quit()
    
    def save_settings(self):
        """保存设置"""
        try:
            # 更新设置
            self.settings["center_start_button"] = self.center_start_button_checkbox.isChecked()
            self.settings["auto_hide_taskbar"] = self.auto_hide_taskbar_checkbox.isChecked()
            self.settings["disable_system_explorer"] = self.disable_system_explorer_checkbox.isChecked()
            self.settings["desktop_path"] = self.desktop_path_edit.text()
            
            # 保存到文件
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            
            self.logger.info("设置已成功保存")
            # 显示成功消息
            QMessageBox.information(self, "保存成功", "设置已成功保存。\n部分设置可能需要重启应用程序才能生效。")
            
            # 关闭设置窗口
            self.close()
        except Exception as e:
            self.logger.error(f"保存设置时出错: {str(e)}")
            QMessageBox.warning(self, "保存失败", f"保存设置时出错: {str(e)}")
    
    @staticmethod
    def get_setting(key, default=None):
        """获取设置值"""
        settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return settings.get(key, default)
            return default
        except Exception:
            return default