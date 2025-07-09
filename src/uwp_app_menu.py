import subprocess
import asyncio
from PyQt5.QtCore import QThread, pyqtSignal
import json
from log import get_logger

logger = get_logger()

async def get_uwp_apps_async():
    """
    异步获取所有UWP应用列表
    Returns: list of dict {name: 应用名称, appid: 应用ID}
    """
    try:
        cmd = 'Get-StartApps | ConvertTo-Json'
        # 使用 asyncio.create_subprocess_shell 替代 subprocess.run 实现异步执行
        proc = await asyncio.create_subprocess_shell(
            f'powershell -Command "{cmd}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            logger.error(f"获取UWP应用失败: {stderr.decode().strip()}")
            return []

        output = stdout.decode('gbk', errors='ignore').strip()
        # 过滤空行和重复项
        filtered_output = [line for line in output.split('\n') if line.strip() and not line.startswith('---')]
        
        if not filtered_output:
            logger.warning("未获取到UWP应用列表或输出为空。")
            return []

        try:
            apps = json.loads('\n'.join(filtered_output))
        except json.JSONDecodeError as e:
            logger.error(f"解析UWP应用JSON失败: {e}\n原始输出:\n{output}")
            return []

        return [{'name': app['Name'], 'appid': app['AppID']} for app in apps]
    except Exception as e:
        logger.error(f"获取UWP应用失败: {str(e)}")
        return []

class UWPAppFetcher(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            apps = loop.run_until_complete(get_uwp_apps_async())
            self.finished.emit(apps)
        except Exception as e:
            self.error.emit(str(e))

def launch_uwp_app(app_id):
    """启动UWP应用"""
    try:
        subprocess.run(f'explorer shell:appsFolder\{app_id}', shell=True)
        return True
    except Exception as e:
        logger.error(f"启动应用失败: {str(e)}")
        return False