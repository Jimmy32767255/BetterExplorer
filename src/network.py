#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 网络状态模块
负责在任务栏显示网络连接状态
"""

import subprocess
import socket
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QMenu, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt
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
        
        # 初始化网络状态
        self.is_connected = False
        self.connection_type = "未知"
        self.network_name = ""
        self.ip_address = ""
        
        # 设置网络状态图标
        self.set_icon("icons/network.svg")
        
        # 创建右键菜单
        self.create_context_menu()
        
        # 设置点击事件
        self.clicked.connect(self.show_network_details)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        
        # 启动定时器更新网络状态
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_network_status)
        self.update_timer.start(5000)  # 每5秒更新一次
        
        # 初始更新
        self.update_network_status()
        
    def set_icon(self, icon_path):
        """设置网络状态图标"""
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            # 如果图标不存在，使用默认图标
            self.setIcon(QIcon.fromTheme("network-wired"))
    
    def create_context_menu(self):
        """创建右键菜单"""
        self.menu = QMenu(self)
        
        # 网络状态信息
        self.status_action = self.menu.addAction("网络状态: 检测中...")
        self.status_action.setEnabled(False)
        
        self.connection_type_action = self.menu.addAction("连接类型: 未知")
        self.connection_type_action.setEnabled(False)
        
        self.network_name_action = self.menu.addAction("网络名称: 未知")
        self.network_name_action.setEnabled(False)
        
        self.ip_action = self.menu.addAction("IP地址: 未知")
        self.ip_action.setEnabled(False)
        
        self.menu.addSeparator()
        
        # 刷新网络
        refresh_action = self.menu.addAction("刷新网络状态")
        refresh_action.triggered.connect(self.refresh_network)
        
        # 网络设置
        settings_action = self.menu.addAction("网络设置")
        settings_action.triggered.connect(self.open_network_settings)
        
        self.menu.addSeparator()
        
        # 网络故障排除
        troubleshoot_action = self.menu.addAction("网络故障排除")
        troubleshoot_action.triggered.connect(self.open_network_troubleshoot)
    
    def show_menu(self, position):
        """显示右键菜单"""
        self.update_menu_info()
        self.menu.exec_(self.mapToGlobal(position))
    
    def update_menu_info(self):
        """更新菜单中的网络信息"""
        status_text = "已连接" if self.is_connected else "未连接"
        self.status_action.setText(f"网络状态: {status_text}")
        self.connection_type_action.setText(f"连接类型: {self.connection_type}")
        self.network_name_action.setText(f"网络名称: {self.network_name}")
        self.ip_action.setText(f"IP地址: {self.ip_address}")
    
    def check_connection(self):
        """检查网络连接状态"""
        try:
            # 尝试连接到一个可靠的服务器
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except (socket.error, socket.timeout):
            return False
    
    def get_network_adapters(self):
        """获取网络适配器信息"""
        try:
            result = subprocess.run(
                ["netsh", "interface", "show", "interface"], 
                capture_output=True, text=True, timeout=10, encoding='utf-8', errors='replace'
            )
            adapters = []
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.splitlines()[3:]  # 跳过标题行
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            admin_state = parts[0]
                            state = parts[1]
                            name = " ".join(parts[2:])
                            if "已连接" in state or "Connected" in state:
                                adapters.append({
                                    'name': name,
                                    'admin_state': admin_state,
                                    'state': state
                                })
            return adapters
        except Exception as e:
            logger.error(f"获取网络适配器失败: {e}")
            return []
    
    def get_connection_type(self, adapter_name):
        """获取连接类型"""
        try:
            # 检查是否为 Wi-Fi
            result = subprocess.run(
                ["netsh", "wlan", "show", "profiles"], 
                capture_output=True, text=True, timeout=5, encoding='utf-8', errors='replace'
            )
            if result.returncode == 0:
                return "Wi-Fi"
            
            # 检查是否为以太网
            if "ethernet" in adapter_name.lower() or "以太网" in adapter_name:
                return "以太网"
            
            return "未知"
        except Exception:
            return "未知"
    
    def get_current_network_name(self):
        """获取当前网络名称"""
        try:
            # 尝试获取 Wi-Fi 名称
            result = subprocess.run(
                ["netsh", "wlan", "show", "profiles"], 
                capture_output=True, text=True, timeout=5, encoding='utf-8', errors='replace'
            )
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.splitlines()
                for line in lines:
                    if "所有用户配置文件" in line or "All User Profile" in line:
                        network_name = line.split(":")[-1].strip()
                        return network_name
            return ""
        except Exception:
            return ""
    
    def get_ip_address(self):
        """获取本机IP地址"""
        try:
            # 获取本机主机名
            hostname = socket.gethostname()
            # 获取本机IP
            ip_address = socket.gethostbyname(hostname)
            return ip_address
        except Exception:
            return "127.0.0.1"
    
    def update_network_status(self):
        """更新网络状态"""
        try:
            self.is_connected = self.check_connection()
            
            adapters = self.get_network_adapters()
            if adapters:
                primary_adapter = adapters[0]  # 使用第一个连接的适配器
                self.connection_type = self.get_connection_type(primary_adapter['name'])
                self.network_name = self.get_current_network_name() or primary_adapter['name']
            else:
                self.connection_type = "未连接"
                self.network_name = ""
            
            self.ip_address = self.get_ip_address()
            
            self.update_network_icon()
            self.update_menu_info()
            
        except Exception as e:
            logger.error(f"更新网络状态失败: {e}")
            self.is_connected = False
            self.connection_type = "未知"
            self.network_name = ""
            self.ip_address = ""
    
    def update_network_icon(self):
        """根据网络状态更新图标"""
        if not self.is_connected:
            icon_name = "network-offline"
            tooltip = "网络: 未连接"
        elif self.connection_type == "Wi-Fi":
            icon_name = "network-wireless"
            tooltip = f"网络: {self.network_name} (Wi-Fi)"
        elif self.connection_type == "以太网":
            icon_name = "network-wired"
            tooltip = f"网络: {self.network_name} (以太网)"
        else:
            icon_name = "network-idle"
            tooltip = f"网络: {self.network_name}"
        
        # 尝试使用系统主题图标，如果不存在则使用默认图标
        self.setIcon(QIcon.fromTheme(icon_name, QIcon("icons/wifi.svg")))
        self.setToolTip(tooltip)
    
    def refresh_network(self):
        """刷新网络状态"""
        self.update_network_status()
        logger.info("手动刷新网络状态")
    
    def show_network_details(self):
        """显示网络详情"""
        # 创建详细信息窗口
        details_window = QWidget()
        details_window.setWindowTitle("网络详细信息")
        details_window.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # 状态信息
        status_text = "已连接" if self.is_connected else "未连接"
        status_label = QLabel(f"网络状态: {status_text}")
        layout.addWidget(status_label)
        
        connection_label = QLabel(f"连接类型: {self.connection_type}")
        layout.addWidget(connection_label)
        
        name_label = QLabel(f"网络名称: {self.network_name}")
        layout.addWidget(name_label)
        
        ip_label = QLabel(f"IP地址: {self.ip_address}")
        layout.addWidget(ip_label)
        
        layout.addStretch()
        
        details_window.setLayout(layout)
        details_window.show()
        
        # 保持窗口引用，防止被垃圾回收
        self.details_window = details_window
        
        logger.info("显示网络详细信息")
    
    def open_network_settings(self):
        """打开网络设置"""
        try:
            # 打开 Windows 网络设置
            subprocess.run(["start", "ms-settings:network"], shell=True)
            logger.info("打开网络设置")
        except Exception as e:
            logger.error(f"打开网络设置失败: {e}")
    
    def open_network_troubleshoot(self):
        """打开网络故障排除"""
        try:
            # 打开 Windows 网络故障排除
            subprocess.run(["msdt.exe", "-id", "NetworkDiagnosticsNetworkAdapter"], capture_output=True)
            logger.info("打开网络故障排除")
        except Exception as e:
            logger.error(f"打开网络故障排除失败: {e}")