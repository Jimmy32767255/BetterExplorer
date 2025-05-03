import subprocess
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QPushButton, QMessageBox
from PyQt5.QtCore import Qt

class VolumeControlWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("音量控制")
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        # 音量标签
        self.volume_label = QLabel("音量：50%")
        layout.addWidget(self.volume_label)
        
        # 音量滑块
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(self.get_current_volume())
        self.volume_slider.valueChanged.connect(self.update_volume)
        layout.addWidget(self.volume_slider)
        
        # 静音按钮
        mute_button = QPushButton("静音")
        mute_button.clicked.connect(self.toggle_mute)
        layout.addWidget(mute_button)
        
        self.setLayout(layout)
    
    def get_current_volume(self):
        """获取当前音量"""
        try:
            result = subprocess.run(["powershell", "-Command", "(Get-AudioDevice -Playback).Volume"], capture_output=True, text=True)
            return int(result.stdout.strip())
        except Exception as e:
            QMessageBox.warning(self, "错误", f"获取当前音量失败: {str(e)}")
            return 50
    
    def update_volume(self, value):
        """更新音量"""
        try:
            subprocess.run(["powershell", "-Command", f"(Get-AudioDevice -Playback).Volume = {value}"])
            self.volume_label.setText(f"音量：{value}%")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"更新音量失败: {str(e)}")
    
    def toggle_mute(self):
        """切换静音状态"""
        try:
            subprocess.run(["powershell", "-Command", "(Get-AudioDevice -Playback).Mute = $true"])
            self.volume_slider.setValue(0)
            self.volume_label.setText("音量：0% (静音)")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"切换静音状态失败: {str(e)}")