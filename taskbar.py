#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 任务栏模块
负责实现任务栏功能，包括显示当前运行的应用程序、系统托盘和时间显示
"""

import os
import time
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                             QMenu, QAction, QSystemTrayIcon, QToolButton,
                             QVBoxLayout, QFrame, QSizePolicy)
from PyQt5.QtCore import (Qt, QTimer, QSize, QRect, QPropertyAnimation,
                          QPoint, QEvent, QEasingCurve)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QCursor


class TaskBar(QWidget):
    """任务栏类，提供任务栏功能"""
    
    def __init__(self, display_manager, parent=None):
        super().__init__(parent)
        self.display_manager = display_manager
        self.running_apps = []
        self.taskbar_widgets = []
        self.hide_animations = []
        self.show_animations = []
        self.hide_timers = []
        self.is_hidden = False
        self.taskbar_height = 40
        
        # 初始化日志记录器
        from log import Logger
        self.logger = Logger()
        self.logger.info("任务栏初始化")
        
        # 创建鼠标位置检测定时器
        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.timeout.connect(self.check_mouse_position)
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 获取所有屏幕信息
        self.screens = self.display_manager.get_screens()
        
        # 导入设置模块
        from settings import Settings
        
        # 获取设置
        self.center_start_button = Settings.get_setting("center_start_button", False)
        self.auto_hide_taskbar = Settings.get_setting("auto_hide_taskbar", False)
        
        # 为每个屏幕创建任务栏
        for screen_index, screen in enumerate(self.screens):
            # 创建任务栏窗口
            taskbar = QWidget()
            taskbar.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            
            # 设置任务栏位置和大小
            taskbar.setGeometry(QRect(
                screen['x'],
                screen['y'] + screen['height'] - self.taskbar_height,
                screen['width'],
                self.taskbar_height
            ))
            
            # 设置任务栏样式
            taskbar.setStyleSheet(
                "background-color: #2D2D30; color: white; border-top: 1px solid #3F3F46;"
            )
            
            # 创建水平布局
            layout = QHBoxLayout(taskbar)
            layout.setContentsMargins(5, 0, 5, 0)
            layout.setSpacing(5)
            
            # 添加开始按钮
            start_button = QPushButton("开始")
            start_button.setFixedSize(60, 30)
            start_button.setStyleSheet(
                "QPushButton {background-color: #0078D7; color: white; border: none; border-radius: 3px;}"
                "QPushButton:hover {background-color: #1C97EA;}"
                "QPushButton:pressed {background-color: #00559B;}"
            )
            start_button.clicked.connect(self.show_start_menu)
            
            # 根据设置决定开始按钮是否居中
            if self.center_start_button:
                # 使用QSpacerItem实现居中布局
                layout.addStretch(1)
                layout.addWidget(start_button)
                layout.addStretch(1)
            else:
                layout.addWidget(start_button)
            
            # 添加任务栏应用按钮区域
            app_area = QWidget()
            app_layout = QHBoxLayout(app_area)
            app_layout.setContentsMargins(10, 0, 10, 0)
            app_layout.setSpacing(5)
            app_layout.setAlignment(Qt.AlignLeft)
            layout.addWidget(app_area, 1)  # 占据大部分空间
            
            # 添加系统托盘区域
            tray_area = QWidget()
            tray_layout = QHBoxLayout(tray_area)
            tray_layout.setContentsMargins(0, 0, 0, 0)
            tray_layout.setSpacing(5)
            tray_layout.setAlignment(Qt.AlignRight)
            layout.addWidget(tray_area)
            
            # 添加时间显示
            time_label = QLabel()
            time_label.setAlignment(Qt.AlignCenter)
            time_label.setStyleSheet("font-size: 12px; padding: 0 5px;")
            tray_layout.addWidget(time_label)
            
            # 更新时间
            self.update_time(time_label)
            
            # 创建定时器，每秒更新一次时间
            timer = QTimer(self)
            timer.timeout.connect(lambda label=time_label: self.update_time(label))
            timer.start(1000)
            
            # 创建动画对象
            hide_animation = QPropertyAnimation(taskbar, b"pos")
            hide_animation.setDuration(300)  # 300毫秒的动画时长
            hide_animation.setEasingCurve(QEasingCurve.InOutCubic)  # 设置动画曲线
            
            show_animation = QPropertyAnimation(taskbar, b"pos")
            show_animation.setDuration(300)  # 300毫秒的动画时长
            show_animation.setEasingCurve(QEasingCurve.InOutCubic)  # 设置动画曲线
            
            # 创建隐藏定时器
            hide_timer = QTimer(self)
            hide_timer.setSingleShot(True)  # 单次触发
            hide_timer.timeout.connect(lambda tb=taskbar, anim=hide_animation: self.hide_taskbar(tb, anim))
            
            # 设置鼠标事件过滤器
            taskbar.installEventFilter(self)
            
            # 保存任务栏部件和相关信息
            self.taskbar_widgets.append({
                'widget': taskbar,
                'screen_index': screen_index,
                'start_button': start_button,
                'app_area': app_area,
                'app_layout': app_layout,
                'tray_area': tray_area,
                'time_label': time_label,
                'screen': screen
            })
            
            # 保存动画和定时器
            self.hide_animations.append(hide_animation)
            self.show_animations.append(show_animation)
            self.hide_timers.append(hide_timer)
    
    def show(self):
        """显示所有任务栏"""
        for taskbar_info in self.taskbar_widgets:
            taskbar_info['widget'].show()
        
        # 如果启用了自动隐藏，初始化任务栏位置
        if self.auto_hide_taskbar:
            self.init_taskbar_positions()
            # 启动鼠标位置检测定时器
            self.mouse_check_timer.start(200)  # 每200毫秒检测一次
            # 通知桌面调整大小
            self.notify_desktop_resize()
        else:
            # 如果不启用自动隐藏，停止定时器
            self.mouse_check_timer.stop()
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理鼠标进入和离开事件"""
        if self.auto_hide_taskbar:
            for i, taskbar_info in enumerate(self.taskbar_widgets):
                if obj == taskbar_info['widget']:
                    if event.type() == QEvent.Enter:
                        # 鼠标进入任务栏，显示任务栏
                        self.show_taskbar(obj, self.show_animations[i])
                        # 取消隐藏定时器
                        self.hide_timers[i].stop()
                        return True
                    elif event.type() == QEvent.Leave:
                        # 鼠标离开任务栏，启动隐藏定时器
                        self.hide_timers[i].start(500)  # 500毫秒后隐藏
                        return True
        return super().eventFilter(obj, event)
        
    def check_mouse_position(self):
        """检查鼠标位置，当鼠标移动到屏幕底部时显示任务栏"""
        if not self.auto_hide_taskbar or not self.is_hidden:
            return
            
        cursor_pos = QCursor.pos()
        for i, taskbar_info in enumerate(self.taskbar_widgets):
            screen = taskbar_info['screen']
            # 检查鼠标是否在屏幕底部区域（最后5个像素）
            if (screen['x'] <= cursor_pos.x() <= screen['x'] + screen['width'] and
                screen['y'] + screen['height'] - 5 <= cursor_pos.y() <= screen['y'] + screen['height']):
                self.show_taskbar(taskbar_info['widget'], self.show_animations[i])
                break
    
    def init_taskbar_positions(self):
        """初始化任务栏位置（用于自动隐藏功能）"""
        if not self.auto_hide_taskbar:
            return
            
        for i, taskbar_info in enumerate(self.taskbar_widgets):
            taskbar = taskbar_info['widget']
            screen = taskbar_info['screen']
            
            # 设置隐藏位置（只露出1像素）
            hidden_y = screen['y'] + screen['height'] - 1
            # 设置显示位置
            shown_y = screen['y'] + screen['height'] - self.taskbar_height
            
            # 设置动画的起始和结束位置
            self.hide_animations[i].setStartValue(QPoint(screen['x'], shown_y))
            self.hide_animations[i].setEndValue(QPoint(screen['x'], hidden_y))
            
            self.show_animations[i].setStartValue(QPoint(screen['x'], hidden_y))
            self.show_animations[i].setEndValue(QPoint(screen['x'], shown_y))
            
            # 初始状态为隐藏
            taskbar.move(screen['x'], hidden_y)
            self.is_hidden = True
    
    def hide_taskbar(self, taskbar, animation):
        """隐藏任务栏"""
        if not self.is_hidden:
            animation.start()
            self.is_hidden = True
            self.logger.debug("任务栏隐藏")
            # 通知桌面调整大小
            self.notify_desktop_resize()
    
    def show_taskbar(self, taskbar, animation):
        """显示任务栏"""
        if self.is_hidden:
            animation.start()
            self.is_hidden = False
            self.logger.debug("任务栏显示")
            # 通知桌面调整大小
            self.notify_desktop_resize()
    
    def notify_desktop_resize(self):
        """通知桌面调整大小"""
        if hasattr(self.display_manager, 'desktop') and hasattr(self.display_manager.desktop, 'adjust_desktop_size'):
            self.display_manager.desktop.adjust_desktop_size()
    
    def is_taskbar_hidden(self):
        """返回任务栏是否处于隐藏状态"""
        return self.is_hidden and self.auto_hide_taskbar
    
    def update_time(self, label):
        """更新时间显示"""
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")
        label.setText(f"{current_time}\n{current_date}")
    
    def add_app_button(self, app_name, icon_path=None):
        """添加应用程序按钮到任务栏"""
        # 创建应用按钮
        app_button = QToolButton()
        app_button.setText(app_name)
        app_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        app_button.setFixedHeight(30)
        app_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        
        # 设置图标（如果有）
        if icon_path and os.path.exists(icon_path):
            app_button.setIcon(QIcon(icon_path))
            self.logger.debug(f"设置应用程序图标: {icon_path}")
        else:
            # 如果图标不存在，设置一个默认图标或者只显示文本
            app_button.setToolButtonStyle(Qt.ToolButtonTextOnly)
            self.logger.debug(f"使用默认图标样式")
        
        # 设置样式
        app_button.setStyleSheet(
            "QToolButton {background-color: #3E3E42; color: white; border: none; border-radius: 3px; padding: 5px;}"
            "QToolButton:hover {background-color: #505054;}"
            "QToolButton:pressed {background-color: #0078D7;}"
        )
        
        # 添加到主屏幕的任务栏
        primary_screen_index = self.display_manager.desktop.primaryScreen() if hasattr(self.display_manager, 'desktop') else 0
        added = False
        for taskbar_info in self.taskbar_widgets:
            if taskbar_info['screen_index'] == primary_screen_index:
                taskbar_info['app_layout'].addWidget(app_button)
                app_button.show()  # 确保按钮可见
                added = True
                break
        
        # 如果没有找到主屏幕的任务栏，添加到第一个可用的任务栏
        if not added and self.taskbar_widgets:
            self.taskbar_widgets[0]['app_layout'].addWidget(app_button)
            app_button.show()  # 确保按钮可见
        
        # 保存应用信息
        app_info = {
            'name': app_name,
            'button': app_button,
            'icon_path': icon_path
        }
        self.running_apps.append(app_info)
        
        return app_button
    
    def remove_app_button(self, app_name):
        """从任务栏移除应用程序按钮"""
        for app_info in self.running_apps:
            if app_info['name'] == app_name:
                app_info['button'].deleteLater()
                self.running_apps.remove(app_info)
                self.logger.info(f"移除应用程序: {app_name}")
                break
    
    def add_system_tray_icon(self, icon_path, tooltip, parent=None):
        """添加系统托盘图标"""
        # 检查图标文件是否存在
        if not os.path.exists(icon_path):
            print(f"警告：系统托盘图标文件不存在: {icon_path}")
            return None
            
        # 创建系统托盘图标
        tray_icon = QSystemTrayIcon(parent if parent else self)
        tray_icon.setIcon(QIcon(icon_path))
        tray_icon.setToolTip(tooltip)
        tray_icon.show()  # 确保图标显示
        
        # 添加到主屏幕的任务栏
        primary_screen_index = self.display_manager.desktop.primaryScreen() if hasattr(self.display_manager, 'desktop') else 0
        for taskbar_info in self.taskbar_widgets:
            if taskbar_info['screen_index'] == primary_screen_index:
                # 创建一个按钮来表示托盘图标
                tray_button = QToolButton()
                tray_button.setIcon(QIcon(icon_path))
                tray_button.setToolTip(tooltip)
                tray_button.setFixedSize(24, 24)
                tray_button.setStyleSheet(
                    "QToolButton {background-color: transparent; border: none;}"
                    "QToolButton:hover {background-color: #505054; border-radius: 3px;}"
                )
                
                taskbar_info['tray_area'].layout().insertWidget(
                    0, tray_button
                )
                # 确保按钮可见
                tray_button.show()
                break
        
        # 确保系统托盘图标显示
        tray_icon.show()
        return tray_icon
    
    def show_start_menu(self):
        """显示开始菜单"""
        # 获取发送信号的按钮
        button = self.sender()
        if button:
            # 如果任务栏处于隐藏状态，先显示任务栏
            if self.auto_hide_taskbar and self.is_hidden:
                for i, taskbar_info in enumerate(self.taskbar_widgets):
                    if button == taskbar_info['start_button']:
                        self.show_taskbar(taskbar_info['widget'], self.show_animations[i])
                        break
            
            # 发出信号，将在main.py中连接到start_menu.toggle_visibility
            button_pos = button.mapToGlobal(button.rect().topLeft())
            # 这个方法会在main.py中被连接到StartMenu的toggle_visibility方法
            # 实际的菜单显示逻辑在StartMenu类中实现