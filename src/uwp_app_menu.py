import subprocess
import subprocess
import json
from log import get_logger

logger = get_logger()

def get_uwp_apps():
    """
    获取所有UWP应用列表
    Returns: list of dict {name: 应用名称, appid: 应用ID}
    """
    try:
        cmd = 'Get-StartApps | ConvertTo-Json'
        result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True, shell=True)
        # 过滤空行和重复项
        filtered_output = [line for line in result.stdout.split('\n') if line.strip() and not line.startswith('---')]
        apps = json.loads('\n'.join(filtered_output))
        return [{'name': app['Name'], 'appid': app['AppID']} for app in apps]
    except Exception as e:
        logger.error(f"获取UWP应用失败: {str(e)}\n原始输出:\n{result.stdout}")
        return []

def launch_uwp_app(app_id):
    """启动UWP应用"""
    try:
        subprocess.run(f'explorer shell:appsFolder\{app_id}', shell=True)
        return True
    except Exception as e:
        logger.error(f"启动应用失败: {str(e)}")
        return False