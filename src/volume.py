#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - 音量控制模块
负责在任务栏显示和控制系统音量
"""

import subprocess
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QMenu, QSlider, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QToolButton
from PyQt5.QtCore import Qt, QTimer
import os
from log import get_logger

logger = get_logger()

class VolumeControl(QToolButton):
    """音量控制控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setStyleSheet(
            "QToolButton {background-color: transparent; border: none;}"
            "QToolButton:hover {background-color: #505054; border-radius: 3px;}"
        )
        
        # 初始化音量状态
        self.current_volume = 50
        self.is_muted_status = False
        
        # 设置音量图标
        self.set_icon("icons/volume.svg")
        
        # 创建右键菜单
        self.create_context_menu()
        
        # 设置点击事件
        self.clicked.connect(self.toggle_mute)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        
        # 启动定时器更新音量状态
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_volume_status)
        self.update_timer.start(2000)  # 每2秒更新一次
        
        # 初始更新
        self.update_volume_status()
        
    def set_icon(self, icon_path):
        """设置音量图标"""
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            # 如果图标不存在，使用默认图标
            self.setIcon(QIcon.fromTheme("audio-volume-medium"))
    
    def create_context_menu(self):
        """创建右键菜单"""
        self.menu = QMenu(self)
        
        # 添加音量滑块 - 使用 QWidgetAction 代替 QAction
        from PyQt5.QtWidgets import QWidgetAction
        
        # 创建音量滑块容器
        volume_widget = QWidget()
        volume_layout = QHBoxLayout(volume_widget)
        volume_layout.setContentsMargins(10, 5, 10, 5)
        
        volume_label = QLabel("音量:")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(self.current_volume)
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.valueChanged.connect(self.on_slider_changed)
        
        self.volume_value_label = QLabel(f"{self.current_volume}%")
        self.volume_value_label.setFixedWidth(40)
        
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_value_label)
        
        # 使用 QWidgetAction 添加自定义控件
        volume_action = QWidgetAction(self.menu)
        volume_action.setDefaultWidget(volume_widget)
        self.menu.addAction(volume_action)
        
        self.menu.addSeparator()
        
        # 静音选项
        self.mute_action = self.menu.addAction("静音")
        self.mute_action.setCheckable(True)
        self.mute_action.triggered.connect(self.toggle_mute)
        
        self.menu.addSeparator()
        
        # 音量设置
        settings_action = self.menu.addAction("音量设置")
        settings_action.triggered.connect(self.open_volume_settings)
    
    def show_menu(self, position):
        """显示右键菜单"""
        self.volume_slider.setValue(self.current_volume)
        self.volume_value_label.setText(f"{self.current_volume}%")
        self.mute_action.setChecked(self.is_muted_status)
        self.menu.exec_(self.mapToGlobal(position))
    
    def on_slider_changed(self, value):
        """滑块值改变时的处理"""
        self.volume_value_label.setText(f"{value}%")
        self.set_volume(value)
    
    def get_current_volume(self):
        """获取当前系统音量"""
        try:
            # 使用 Windows 核心音频 API 通过 PowerShell
            ps_command = """
            $device = Get-WmiObject -Class Win32_SoundDevice | Where-Object {$_.Status -eq 'OK'} | Select-Object -First 1
            if ($device) { 
                Add-Type -TypeDefinition @'
                using System;
                using System.Runtime.InteropServices;
                public class Audio {
                    [DllImport("winmm.dll")]
                    public static extern int waveOutGetVolume(IntPtr hwo, out uint dwVolume);
                    [DllImport("winmm.dll")]
                    public static extern int waveOutSetVolume(IntPtr hwo, uint dwVolume);
                }
'@ -ErrorAction SilentlyContinue
                $volume = 0
                [Audio]::waveOutGetVolume([IntPtr]::Zero, [ref]$volume) | Out-Null
                $leftChannel = ($volume -band 0xFFFF)
                $volumePercent = [math]::Round($leftChannel / 65535 * 100)
                $volumePercent
            } else { 50 }
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command.strip()], 
                capture_output=True, text=True, timeout=3, encoding='utf-8', errors='replace'
            )
            if result.returncode == 0 and result.stdout.strip():
                volume = int(float(result.stdout.strip()))
                return max(0, min(100, volume))
        except Exception as e:
            logger.error(f"获取音量失败: {e}")
        return self.current_volume
    
    def set_volume(self, value):
        """设置系统音量"""
        try:
            # 使用 Windows 核心音频 API 设置音量
            ps_command = f"""
            Add-Type -TypeDefinition @'
            using System;
            using System.Runtime.InteropServices;
            public class Audio {{
                [DllImport("winmm.dll")]
                public static extern int waveOutGetVolume(IntPtr hwo, out uint dwVolume);
                [DllImport("winmm.dll")]
                public static extern int waveOutSetVolume(IntPtr hwo, uint dwVolume);
            }}
'@ -ErrorAction SilentlyContinue
            $volumePercent = {value}
            $volumeValue = [uint32]($volumePercent * 65535 / 100)
            $combinedVolume = ($volumeValue -shl 16) -bor $volumeValue
            [Audio]::waveOutSetVolume([IntPtr]::Zero, $combinedVolume)
            """
            
            subprocess.run(
                ["powershell", "-Command", ps_command.strip()], 
                capture_output=True, timeout=3, encoding='utf-8', errors='replace'
            )
            self.current_volume = value
            self.update_volume_icon()
            logger.info(f"设置音量为: {value}%")
        except Exception as e:
            logger.error(f"设置音量失败: {e}")
    
    def toggle_mute(self):
        """切换静音状态"""
        try:
            if self.is_muted_status:
                # 取消静音 - 恢复之前的音量
                self.set_volume(self.current_volume)
                self.is_muted_status = False
                logger.info("取消静音")
            else:
                # 静音 - 保存当前音量然后设置为0
                self.current_volume = self.get_current_volume()
                self.set_volume(0)
                self.is_muted_status = True
                logger.info("设置为静音")
            
            self.update_volume_icon()
            
        except Exception as e:
            logger.error(f"切换静音失败: {e}")
    
    def is_muted(self):
        """检查是否静音"""
        try:
            # 通过检查当前音量是否为0来判断是否静音
            current_vol = self.get_current_volume()
            return current_vol == 0
        except Exception as e:
            logger.error(f"检查静音状态失败: {e}")
        return self.is_muted_status
    
    def update_volume_status(self):
        """更新音量状态"""
        try:
            self.current_volume = self.get_current_volume()
            self.is_muted_status = self.is_muted()
            self.update_volume_icon()
        except Exception as e:
            logger.error(f"更新音量状态失败: {e}")
    
    def update_volume_icon(self):
        """根据音量状态更新图标"""
        if self.is_muted_status:
            icon_name = "audio-volume-muted"
        elif self.current_volume == 0:
            icon_name = "audio-volume-zero"
        elif self.current_volume < 33:
            icon_name = "audio-volume-low"
        elif self.current_volume < 66:
            icon_name = "audio-volume-medium"
        else:
            icon_name = "audio-volume-high"
        
        # 尝试使用系统主题图标，如果不存在则使用默认图标
        self.setIcon(QIcon.fromTheme(icon_name, QIcon("icons/volume.svg")))
        
        # 更新提示信息
        if self.is_muted_status:
            self.setToolTip("音量: 静音")
        else:
            self.setToolTip(f"音量: {self.current_volume}%")
    
    def open_volume_settings(self):
        """打开系统音量设置"""
        try:
            # 打开 Windows 音量混音器
            subprocess.run(["sndvol.exe"], capture_output=True)
            logger.info("打开音量设置")
        except Exception as e:
            logger.error(f"打开音量设置失败: {e}")