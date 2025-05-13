import subprocess
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QCheckBox, QMessageBox
from PyQt5.QtCore import Qt

class NetworkSettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("网络设置")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # 网络连接状态
        self.status_label = QLabel("网络状态：未知")
        layout.addWidget(self.status_label)
        
        # 网络适配器选择
        self.adapter_combo = QComboBox()
        self.adapter_combo.addItems(self.get_network_adapters())
        layout.addWidget(self.adapter_combo)
        
        # 自动连接选项
        self.auto_connect = QCheckBox("自动连接")
        layout.addWidget(self.auto_connect)
        
        # 刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_network)
        layout.addWidget(refresh_button)
        
        # 保存按钮
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
        
        self.setLayout(layout)
        self.refresh_network()
    
    def get_network_adapters(self):
        """获取网络适配器列表"""
        try:
            result = subprocess.run(["netsh", "interface", "show", "interface"], capture_output=True, text=True)
            lines = result.stdout.splitlines()
            adapters = [line.split()[-1] for line in lines[3:] if line.strip()]
            return adapters
        except Exception as e:
            QMessageBox.warning(self, "错误", f"获取网络适配器失败: {str(e)}")
            return ["Wi-Fi", "以太网"]
    
    def refresh_network(self):
        """刷新网络状态"""
        try:
            result = subprocess.run(["netsh", "interface", "show", "interface"], capture_output=True, text=True)
            if "已连接" in result.stdout:
                self.status_label.setText("网络状态：已连接")
            else:
                self.status_label.setText("网络状态：未连接")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"刷新网络状态失败: {str(e)}")
    
    def save_settings(self):
        """保存网络设置"""
        selected_adapter = self.adapter_combo.currentText()
        auto_connect = self.auto_connect.isChecked()
        try:
            subprocess.run(["netsh", "interface", "set", "interface", selected_adapter, "admin=enabled"])
            QMessageBox.information(self, "成功", "网络设置已保存")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存网络设置失败: {str(e)}")