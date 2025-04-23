#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BetterExplorer - Alt+Tab切换模块
负责实现Alt+Tab窗口切换功能
"""


import sys
import win32con
import win32gui
import ctypes
import win32api
import win32process
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap


class AltTabSwitcher(QWidget):
    """Alt+Tab窗口切换器类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化日志记录器
        from log import Logger
        self.logger = Logger()
        self.logger.info("Alt+Tab切换器初始化")
        
        # 初始化UI
        self.init_ui()
        
        # 窗口列表
        self.window_list = []
        self.current_index = 0
        
        # 键盘钩子状态
        self.alt_pressed = False
        self.tab_pressed = False
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口大小
        self.resize(400, 300)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建标题标签
        title_label = QLabel("窗口切换器")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建窗口列表
        self.window_list_widget = QListWidget()
        self.window_list_widget.setViewMode(QListWidget.IconMode)
        self.window_list_widget.setIconSize(QPixmap(64, 64).size())
        self.window_list_widget.setSpacing(10)
        main_layout.addWidget(self.window_list_widget)
        
    def start_monitoring(self):
        """开始监听Alt+Tab组合键"""
        # 使用pywin32库的SetWindowsHookEx函数设置低级键盘钩子
        self.logger.info("开始监听键盘事件")
        
        # 定义键盘钩子回调函数
        def low_level_keyboard_handler(nCode, wParam, lParam):
            # 如果nCode小于0，必须调用CallNextHookEx
            if nCode < 0:
                return ctypes.windll.user32.CallNextHookEx(self.keyboard_hook, nCode, wParam, lParam)
            
            # 获取按键信息
            key_info = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_ulong * 5)).contents
            vk_code = key_info[0]  # 虚拟键码
            scan_code = key_info[1]  # 扫描码
            flags = key_info[2]  # 标志位
            time = key_info[3]  # 时间戳
            
            self.logger.debug(f"键盘事件: vk_code={vk_code}, scan_code={scan_code}, flags={flags}, time={time}")
            
            # 检测Alt键状态
            if vk_code == win32con.VK_MENU:  # Alt键的虚拟键码
                if wParam == win32con.WM_KEYDOWN or wParam == win32con.WM_SYSKEYDOWN:
                    self.alt_pressed = True
                elif wParam == win32con.WM_KEYUP or wParam == win32con.WM_SYSKEYUP:
                    self.alt_pressed = False
                    # Alt键释放时处理
                    self.on_alt_released()
            
            # 检测Tab键状态
            if vk_code == win32con.VK_TAB:  # Tab键的虚拟键码
                if wParam == win32con.WM_KEYDOWN or wParam == win32con.WM_SYSKEYDOWN:
                    self.tab_pressed = True
                    # 检测Shift键状态
                    shift_pressed = win32api.GetKeyState(win32con.VK_SHIFT) & 0x8000 != 0
                    
                    # 处理Alt+Tab组合键
                    if self.alt_pressed and self.tab_pressed:
                        self.logger.debug(f"检测到Alt+Tab组合键, shift状态: {shift_pressed}")
                        if shift_pressed:
                            self.on_alt_shift_tab_pressed()
                        else:
                            self.on_alt_tab_pressed()
                elif wParam == win32con.WM_KEYUP or wParam == win32con.WM_SYSKEYUP:
                    self.tab_pressed = False
            
            # 继续传递给下一个钩子
            return ctypes.windll.user32.CallNextHookEx(self.keyboard_hook, nCode, wParam, lParam)
        
        # 创建钩子回调函数的C类型
        self.keyboard_proc = ctypes.WINFUNCTYPE(
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_ulong)
        )(low_level_keyboard_handler)
        
        # 安装键盘钩子
        self.keyboard_hook = ctypes.windll.user32.SetWindowsHookExW(
            win32con.WH_KEYBOARD_LL,  # 低级键盘钩子
            self.keyboard_proc,
            0,  # 全局钩子不需要模块句柄
            0  # 全局钩子
        )
        
        # 检查钩子是否安装成功
        if not self.keyboard_hook:
            raise Exception("键盘钩子安装失败")
        
    def __del__(self):
        """析构函数，确保钩子被正确释放"""
        # 释放键盘钩子
        if hasattr(self, 'keyboard_hook') and self.keyboard_hook:
            ctypes.windll.user32.UnhookWindowsHookEx(self.keyboard_hook)
            self.keyboard_hook = None
        
    def show_switcher(self):
        """显示窗口切换器"""
        self.logger.debug("开始显示窗口切换器")
        
        # 获取所有窗口
        self.update_window_list()
        self.logger.debug(f"窗口列表更新完成，共找到 {len(self.window_list)} 个窗口\n详细列表：{[w['title'] for w in self.window_list]}")
        
        # 更新窗口列表显示
        self.window_list_widget.clear()
        if not self.window_list:
            self.logger.warning("没有找到可切换的窗口，窗口切换器将不会显示")
            return
            
        for window in self.window_list:
            item = QListWidgetItem(window['title'])
            # 这里应该获取窗口图标，为简化示例，使用默认图标
            self.window_list_widget.addItem(item)
            self.logger.debug(f"添加窗口到列表: {window['title']}")
        
        # 居中显示
        self.center_on_screen()
        self.logger.debug("窗口切换器已居中")
        
        # 显示窗口
        self.show()
        self.logger.debug("窗口切换器显示完成")
        
        # 选中第一个窗口
        if self.window_list:
            self.current_index = 0
            self.window_list_widget.setCurrentRow(0)
            self.logger.debug(f"已选中第一个窗口: {self.window_list[0]['title']}")
        
    def update_window_list(self):
        """更新窗口列表"""
        self.window_list = []
        
        def enum_windows_callback(hwnd, _):
            # 过滤掉不可见窗口
            if not win32gui.IsWindowVisible(hwnd):
                return True
            
            # 过滤掉没有标题的窗口
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return True
            
            # 获取窗口进程ID和类名
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            # 过滤掉特定的系统窗口
            if class_name in ["Shell_TrayWnd", "Shell_SecondaryTrayWnd", "DV2ControlHost"]:
                self.logger.debug(f"过滤掉系统窗口: {title} (类名: {class_name})")
                return True
                
            # 过滤掉Alt+Tab切换器自身
            if title == "窗口切换器" or "AltTabSwitcher" in class_name:
                self.logger.debug(f"过滤掉切换器窗口: {title}")
                return True
                
            # 过滤掉空标题或不可见的窗口
            if not title or not win32gui.IsWindowVisible(hwnd):
                return True
            
            # 添加到窗口列表
            self.window_list.append({
                'hwnd': hwnd,
                'title': title,
                'process_id': process_id,
                'class_name': class_name
            })
            
            return True
        
        # 枚举所有顶级窗口
        win32gui.EnumWindows(enum_windows_callback, None)
        
    def center_on_screen(self):
        """将窗口居中显示"""
        from PyQt5.QtWidgets import QApplication
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
    def switch_to_window(self, index):
        """切换到指定窗口"""
        if 0 <= index < len(self.window_list):
            hwnd = self.window_list[index]['hwnd']
            # 将窗口设为前台窗口
            win32gui.SetForegroundWindow(hwnd)
            # 如果窗口最小化，则恢复
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            self.logger.info(f"切换到窗口: {self.window_list[index]['title']}")

    def next_window(self):
        """切换到下一个窗口"""
        if not self.window_list:
            self.logger.warning("窗口列表为空，无法切换窗口")
            return
            
        # 更新当前索引
        self.current_index = (self.current_index + 1) % len(self.window_list)
        self.window_list_widget.setCurrentRow(self.current_index)
        
        # 激活选中的窗口
        window = self.window_list[self.current_index]
        hwnd = window['hwnd']
        self.logger.debug(f"切换到窗口: {window['title']} (hwnd={hwnd})")
        win32gui.SetForegroundWindow(hwnd)

    def previous_window(self):
        """切换到上一个窗口"""
        if self.window_list:
            self.current_index = (self.current_index - 1) % len(self.window_list)
            self.window_list_widget.setCurrentRow(self.current_index)
            
            # 激活选中的窗口
            window = self.window_list[self.current_index]
            hwnd = window['hwnd']
            self.logger.debug(f"切换到窗口: {window['title']} (hwnd={hwnd})")
            win32gui.SetForegroundWindow(hwnd)
            # 如果窗口最小化，则恢复
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    def on_alt_tab_pressed(self):
        """处理Alt+Tab按下事件"""
        self.logger.debug("处理Alt+Tab按下事件")
        if not self.isVisible():
            self.logger.debug("窗口切换器未显示，准备显示切换器")
            self.show_switcher()
        else:
            self.logger.debug("窗口切换器已显示，准备切换到下一个窗口")
        self.next_window()

    def on_alt_shift_tab_pressed(self):
        """处理Alt+Shift+Tab按下事件"""
        if not self.isVisible():
            self.show_switcher()
            self.logger.debug("显示窗口切换器(Shift)")
        self.previous_window()

    def on_alt_released(self):
        """处理Alt键释放事件"""
        self.logger.debug("Alt键释放")
        if self.isVisible():
            self.logger.debug("窗口切换器可见，准备隐藏")
            self.hide()
            # 激活当前选中的窗口
            if self.window_list and 0 <= self.current_index < len(self.window_list):
                window = self.window_list[self.current_index]
                hwnd = window['hwnd']
                self.logger.debug(f"激活最终选中的窗口: {window['title']} (hwnd={hwnd})")
                win32gui.SetForegroundWindow(hwnd)
                # 如果窗口最小化，则恢复
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)