#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 显示器管理模块
负责实现多显示器支持功能
"""

import sys
from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtCore import QRect
from log import Logger


class DisplayManager:
    """显示器管理类，提供多显示器支持"""
    
    def __init__(self):
        # 获取应用程序实例
        if QApplication.instance() is None:
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        
        # 初始化日志记录器
        self.logger = Logger()
        self.logger.info("显示器管理器初始化")
        
        # 获取桌面窗口部件
        self.desktop = QDesktopWidget()
        
        # 连接屏幕变化信号
        self.desktop.screenCountChanged.connect(self.on_screen_count_changed)
        self.desktop.resized.connect(self.on_screen_resized)
        
        # 初始化屏幕信息
        self.update_screen_info()
    
    def update_screen_info(self):
        """更新屏幕信息"""
        self.screen_count = self.desktop.screenCount()
        self.screens = []
        
        for i in range(self.screen_count):
            screen_geometry = self.desktop.screenGeometry(i)
            screen_info = {
                'index': i,
                'geometry': screen_geometry,
                'width': screen_geometry.width(),
                'height': screen_geometry.height(),
                'x': screen_geometry.x(),
                'y': screen_geometry.y(),
                'is_primary': (i == self.desktop.primaryScreen())
            }
            self.screens.append(screen_info)
        self.logger.info(f"更新屏幕信息: 检测到{self.screen_count}个显示器")

    def on_screen_count_changed(self, count):
        """处理屏幕数量变化事件"""
        self.logger.info(f"屏幕数量变化: {count}个显示器")
        self.update_screen_info()

    def on_screen_resized(self, screen_index):
        """处理屏幕尺寸变化事件"""
        self.logger.info(f"屏幕{screen_index}尺寸变化")
        self.update_screen_info()
        # 这里可以添加屏幕尺寸变化的处理逻辑
    
    def get_screens(self):
        """获取所有屏幕信息"""
        return self.screens
    
    def get_screen_count(self):
        """获取屏幕数量"""
        return self.screen_count
    
    def get_primary_screen(self):
        """获取主屏幕信息"""
        primary_index = self.desktop.primaryScreen()
        return self.screens[primary_index]
    
    def get_screen_at(self, pos):
        """获取指定位置所在的屏幕"""
        screen_number = self.desktop.screenNumber(pos)
        return self.screens[screen_number]
    
    def get_screen_by_index(self, index):
        """根据索引获取屏幕"""
        if 0 <= index < self.screen_count:
            return self.screens[index]
        return None
    
    def get_total_geometry(self):
        """获取所有屏幕组成的总几何区域"""
        return self.desktop.geometry()
    
    def on_screen_count_changed(self, count):
        """处理屏幕数量变化事件"""
        self.update_screen_info()
        # 这里可以添加屏幕数量变化的处理逻辑
    
    def on_screen_resized(self, screen_index):
        """处理屏幕尺寸变化事件"""
        self.update_screen_info()
        # 这里可以添加屏幕尺寸变化的处理逻辑
    
    def is_point_on_screen(self, pos):
        """判断点是否在任一屏幕上"""
        for screen in self.screens:
            if screen['geometry'].contains(pos):
                return True
        return False
    
    def move_to_screen(self, widget, screen_index):
        """将窗口部件移动到指定屏幕"""
        if 0 <= screen_index < self.screen_count:
            target_screen = self.screens[screen_index]
            widget_geometry = widget.geometry()
            
            # 计算新位置，使窗口居中显示在目标屏幕上
            new_x = target_screen['x'] + (target_screen['width'] - widget_geometry.width()) // 2
            new_y = target_screen['y'] + (target_screen['height'] - widget_geometry.height()) // 2
            
            widget.move(new_x, new_y)
            return True
        return False