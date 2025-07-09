#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 网络状态模块
负责在任务栏显示网络连接状态
"""

from PyQt5.QtWidgets import QHBoxLayout, QPushButton
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QToolButton
import os

from log import get_logger

logger = get_logger()

class NetworkStatus(QToolButton):
    """网络状态控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setStyleSheet(
            "QToolButton {background-color: transparent; border: none;}"
            "QToolButton:hover {background-color: #505054; border-radius: 3px;}"
        )
        # 设置网络状态图标
        self.set_icon("icons/network.svg")
        
    def set_icon(self, icon_path):
        """设置网络状态图标"""
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            # 如果图标不存在，使用默认图标
            self.setIcon(QIcon.fromTheme("network-wired"))
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_network_status)
        self.update_timer.start(5000) # 每5秒更新一次

    def init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 网络图标按钮 (后续可根据连接状态改变图标)
        self.network_button = QPushButton()
        # 根据实际情况选择合适的图标，例如 Wi-Fi 或以太网
        self.network_button.setIcon(QIcon.fromTheme("network-wireless", QIcon("icons/wifi.svg"))) # 尝试使用系统主题图标，提供备用
        self.network_button.setFixedSize(24, 24)
        self.network_button.setFlat(True)
        self.network_button.setToolTip("网络状态")
        self.network_button.clicked.connect(self.show_network_details) # 点击显示网络详情
        layout.addWidget(self.network_button)

        self.update_network_status()

    def update_network_status(self):
        """更新网络状态(图标、提示等)"""
        # is_connected = self.check_connection()
        # connection_type = self.get_connection_type()
        # 更新图标和 ToolTip
        # ... 实现检查网络连接状态的逻辑 ...
        # print("更新网络状态...")
        pass

    def check_connection(self):
        """检查网络连接状态"""
        # TODO: 实现跨平台的网络连接检查逻辑
        # 例如，尝试 ping 一个可靠的服务器或使用特定库
        return True # 示例值

    def get_connection_type(self):
        """获取网络连接类型(如 Wi-Fi, Ethernet)"""
        # TODO: 实现获取网络连接类型的逻辑
        return "Wi-Fi" # 示例值

    def show_network_details(self):
        """显示网络详情(可选)"""
        # 可以弹出一个窗口或菜单显示更详细的网络信息
        logger.info("显示网络详情")
        pass