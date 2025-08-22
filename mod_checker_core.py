#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nexus Mods版本检查器 - 核心版本
专门用于GitHub Actions自动化，精简版本
"""

import requests
import json
import time
import os
import random
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import functools

# 强制print函数立即刷新缓冲区，解决无实时输出问题
print = functools.partial(print, flush=True)

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class ModVersionChecker:
    def __init__(self):
        self.api_key = os.getenv('NEXUS_API_KEY')
        self.webhook_url = os.getenv('WEBHOOK_URL')
        self.api_base_url = "https://api.nexusmods.com/v1"
        self.version_file = "Version.json"
        
        # 从配置文件加载mod列表
        self.load_mods_config()
        
        # 创建会话
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def load_mods_config(self):
        """从配置文件加载mod列表"""
        print("📁 正在加载mod配置文件...")
        try:
            with open('mods_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.game_domain = config.get('game_domain', 'eldenringnightreign')
                self.mods = {}

                for mod in config.get('mods', []):
                    self.mods[mod['name']] = {
                        'mod_id': mod['id'],
                        'game_domain': self.game_domain,
                        'url': f"https://www.nexusmods.com/{self.game_domain}/mods/{mod['id']}"
                    }

                print(f"✅ 已加载 {len(self.mods)} 个mod配置")
                for mod_name in self.mods.keys():
                    print(f"   - {mod_name}")

        except FileNotFoundError:
            error_msg = "❌ 未找到 mods_config.json 配置文件"
            print(error_msg)
            self.send_error_notification("配置文件错误", error_msg)
            raise
        except Exception as e:
            error_msg = f"❌ 加载mod配置失败: {str(e)}"
            print(error_msg)
            self.send_error_notification("配置文件错误", error_msg)
            raise
    
    def get_api_headers(self):
        """获取API请求头"""
        if not self.api_key:
            return None
        return {
            'apikey': self.api_key,
            'User-Agent': 'ModVersionChecker/2.0',
            'Content-Type': 'application/json'
        }

    def test_api_availability(self):
        """测试API可用性"""
        print("🔍 正在测试Nexus Mods API连接...")

        if not self.api_key:
            error_msg = "❌ 未配置API密钥，无法使用API功能"
            print(error_msg)
            self.send_error_notification("API配置错误", error_msg)
            return False

        try:
            headers = self.get_api_headers()
            # 测试用户验证接口
            response = self.session.get(
                "https://api.nexusmods.com/v1/users/validate.json",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                user_info = response.json()
                print(f"✅ API连接成功，用户: {user_info.get('name', 'Unknown')}")
                return True
            else:
                error_msg = f"❌ API连接失败，状态码: {response.status_code}"
                print(error_msg)
                self.send_error_notification("API连接失败", f"{error_msg}\n响应: {response.text[:200]}")
                return False

        except Exception as e:
            error_msg = f"❌ API连接异常: {str(e)}"
            print(error_msg)
            self.send_error_notification("API连接异常", error_msg)
            return False
    
    def get_mod_info_via_api(self, game_domain, mod_id):
        """通过API获取mod信息"""
        if not self.api_key:
            return None
            
        try:
            headers = self.get_api_headers()
            url = f"{self.api_base_url}/games/{game_domain}/mods/{mod_id}.json"
            
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 获取最新文件信息
            files_url = f"{self.api_base_url}/games/{game_domain}/mods/{mod_id}/files.json"
            files_response = self.session.get(files_url, headers=headers, timeout=30)
            files_response.raise_for_status()
            
            files_data = files_response.json()
            
            # 找到最新的主文件
            latest_file = None
            latest_date = None
            
            for file_info in files_data.get('files', []):
                if file_info.get('category_id') == 1:  # 主文件
                    file_date = file_info.get('uploaded_timestamp')
                    if latest_date is None or file_date > latest_date:
                        latest_date = file_date
                        latest_file = file_info
            
            # 构建返回信息
            version = latest_file.get('version', 'Unknown') if latest_file else data.get('version', 'Unknown')
            update_time = latest_file.get('uploaded_time', 'Unknown') if latest_file else data.get('updated_time', 'Unknown')
            upload_timestamp = latest_file.get('uploaded_timestamp', 0) if latest_file else data.get('updated_timestamp', 0)

            return {
                'version': version,
                'mod_name': data.get('name', 'Unknown'),
                'update_time': update_time,
                'upload_timestamp': upload_timestamp, # 添加用于精确比对的时间戳
                'last_checked': datetime.now().isoformat(),
                'url': f"https://www.nexusmods.com/{game_domain}/mods/{mod_id}",
                'method': 'API'
            }
            
        except Exception as e:
            print(f"⚠️ API获取失败 {game_domain}/mods/{mod_id}: {str(e)}")
            return None
    
    def get_mod_version(self, mod_name, mod_info):
        """获取mod的版本信息"""
        print(f"  🔄 正在获取 {mod_name} 的版本信息...")

        api_result = self.get_mod_info_via_api(mod_info['game_domain'], mod_info['mod_id'])
        if api_result:
            print(f"  ✅ {mod_name}: {api_result.get('version', 'Unknown')}")
            return api_result

        # API失败，发送错误通知
        error_msg = f"获取 {mod_name} 版本信息失败"
        print(f"  ❌ {error_msg}")
        self.send_error_notification("Mod获取失败", f"{error_msg}\nMod ID: {mod_info['mod_id']}\nURL: {mod_info['url']}")

        return {
            'version': 'Error',
            'mod_name': 'Error',
            'update_time': 'Error',
            'last_checked': datetime.now().isoformat(),
            'url': mod_info['url'],
            'error': 'API获取失败',
            'method': 'Failed'
        }
    
    def load_previous_versions(self):
        """加载之前保存的版本信息"""
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ 读取版本文件失败: {str(e)}")
        return {}
    
    def save_versions(self, versions):
        """保存版本信息到文件"""
        try:
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(versions, f, ensure_ascii=False, indent=2)
            print(f"✅ 版本信息已保存到 {self.version_file}")
        except Exception as e:
            print(f"❌ 保存版本文件失败: {str(e)}")
    
    def send_wechat_notification(self, message):
        """发送企业微信通知"""
        if not self.webhook_url:
            print("⚠️ 未配置企业微信Webhook URL，跳过通知")
            return

        try:
            data = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }

            response = requests.post(
                self.webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    print("✅ 企业微信通知发送成功")
                else:
                    print(f"❌ 企业微信通知发送失败: {result}")
            else:
                print(f"❌ 企业微信通知发送失败，状态码: {response.status_code}")

        except Exception as e:
            print(f"❌ 发送企业微信通知异常: {str(e)}")

    def send_error_notification(self, error_type, error_message):
        """发送错误通知"""
        message = f"🚨 Mod版本检查器错误通知\n\n"
        message += f"错误类型: {error_type}\n"
        message += f"错误详情: {error_message}\n"
        message += f"发生时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        message += "请检查配置或网络连接"

        self.send_wechat_notification(message)
    
    def check_updates(self):
        """检查所有mod的更新"""
        print("🔍 开始检查mod版本更新...")
        print("=" * 50)

        # 首先测试API可用性
        if not self.test_api_availability():
            print("❌ API不可用，终止检查")
            return {}, []

        print("\n📋 开始检查各个mod...")
        previous_versions = self.load_previous_versions()
        current_versions = {}
        updates_found = []
        errors_found = []
        
        total_mods = len(self.mods)
        for index, (mod_name, mod_info) in enumerate(self.mods.items(), 1):
            print(f"\n📦 [{index}/{total_mods}] 检查 {mod_name}...")

            current_info = self.get_mod_version(mod_name, mod_info)
            current_versions[mod_name] = current_info

            # 检查是否获取失败
            if current_info.get('version') == 'Error':
                errors_found.append({
                    'name': mod_name,
                    'url': mod_info['url'],
                    'error': current_info.get('error', 'Unknown error')
                })
                print(f"  ❌ {mod_name} 获取版本失败")
                time.sleep(random.uniform(2, 4))
                continue

            # 检查是否有更新
            if mod_name in previous_versions:
                prev_info = previous_versions[mod_name]
                prev_version = prev_info.get('version', 'Unknown')
                prev_timestamp = prev_info.get('upload_timestamp', 0)
                
                curr_version = current_info.get('version', 'Unknown')
                curr_timestamp = current_info.get('upload_timestamp', 0)

                if prev_version != curr_version or prev_timestamp != curr_timestamp:
                    update_info = {
                        'name': mod_name,
                        'mod_display_name': current_info.get('mod_name', mod_name),
                        'old_version': prev_version,
                        'new_version': curr_version,
                        'url': mod_info['url']
                    }
                    if prev_version != curr_version:
                        print(f"  🆕 发现版本更新: {prev_version} -> {curr_version}")
                        update_info['update_type'] = 'version'
                    else:
                        print(f"  🆕 发现文件更新 (版本号未变): {prev_version}")
                        update_info['update_type'] = 'file'
                    updates_found.append(update_info)
                else:
                    print(f"  ✅ 版本无变化: {curr_version}")
            else:
                print(f"  📝 首次记录版本: {current_info.get('version', 'Unknown')}")

            # 添加延迟，避免请求过快
            if index < total_mods:  # 最后一个不需要延迟
                delay = random.uniform(2, 4)
                print(f"  ⏳ 等待 {delay:.1f}s...")
                time.sleep(delay)
        
        print("\n" + "=" * 50)
        print("📊 检查结果汇总:")

        # 保存当前版本信息
        self.save_versions(current_versions)

        # 发送更新通知
        if updates_found:
            self.send_update_notification(updates_found)
            print(f"🎉 发现 {len(updates_found)} 个mod更新:")
            for update in updates_found:
                print(f"   - {update['name']}: {update['old_version']} -> {update['new_version']}")
        else:
            print("✅ 所有mod都是最新版本")

        if errors_found:
            print(f"⚠️ 有 {len(errors_found)} 个mod获取失败:")
            for error in errors_found:
                print(f"   - {error['name']}: {error['error']}")

            # 发送错误汇总通知
            error_summary = f"共有 {len(errors_found)} 个mod获取失败:\n"
            for error in errors_found:
                error_summary += f"- {error['name']}\n"
            self.send_error_notification("批量获取失败", error_summary)

        success_count = len(current_versions) - len(errors_found)
        print(f"\n📈 统计信息:")
        print(f"   总mod数: {len(current_versions)}")
        print(f"   成功获取: {success_count}")
        print(f"   获取失败: {len(errors_found)}")
        print(f"   发现更新: {len(updates_found)}")

        return current_versions, updates_found
    
    def send_update_notification(self, updates):
        """发送更新通知"""
        message = "🎮 Elden Ring Night Reign Mod 更新通知:\n\n"
        
        for update in updates:
            display_name = update.get('mod_display_name', update['name'])
            update_type = update.get('update_type')

            message += f"📦 {display_name}\n"
            if update_type == 'version':
                message += f"   🔥 版本更新: {update['old_version']} → {update['new_version']}\n"
            elif update_type == 'file':
                message += f"   ✨ 文件更新 (版本号未变: {update['new_version']})\n"
            else:
                # 兼容旧数据或未知情况
                message += f"   版本: {update['old_version']} → {update['new_version']}\n"
            message += f"   链接: {update['url']}\n\n"
        
        message += f"检查时间: {datetime.当前()。strftime('%Y-%m-%d %H:%M:%S')}"
        self.send_wechat_notification(message)

def main():
    """主函数"""
    print("🎮 Elden Ring Night Reign Mod版本检查器")
    print("=" * 50)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        checker = ModVersionChecker()
        current_versions, updates = checker.check_updates()

        print(f"\n⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)

        return len(updates) > 0  # 返回是否有更新

    except Exception as e:
        error_msg = f"❌ 程序执行异常: {str(e)}"
        print(error_msg)

        # 尝试发送错误通知
        try:
            checker = ModVersionChecker()
            checker.send_error_notification("程序执行异常", str(e))
        except:
            pass  # 如果连初始化都失败，就不发送通知了

        return False

if __name__ == "__main__":
    # 设置控制台编码以支持Unicode字符
    import sys
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout。detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    
    has_updates = main()
    if has_updates:
        print("发现更新，为GitHub Actions设置输出变量...")
        # 如果在GitHub Actions环境中，则设置输出变量
        if 'GITHUB_OUTPUT' 在 os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write('updates_found=true\n')
    
    # 始终以代码0成功退出，通过输出变量传递“有更新”的状态
    sys.exit(0)
