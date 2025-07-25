#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nexus Mods版本检查器
用于监控指定mod的版本更新并发送企业微信通知
"""

import requests
import json
import time
import os
from datetime import datetime
from bs4 import BeautifulSoup
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mod_checker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ModVersionChecker:
    def __init__(self):
        # 优先从环境变量读取webhook URL，如果没有则使用默认值
        self.webhook_url = os.getenv(
            'WEBHOOK_URL',
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=f749b6e2-22c6-4196-b0b4-f862a9c43867"
        )
        self.version_file = "Version.json"
        self.mods = {
            "10级难度": "https://www.nexusmods.com/eldenringnightreign/mods/171",
            "4阶段人马": "https://www.nexusmods.com/eldenringnightreign/mods/243", 
            "3阶段解锁": "https://www.nexusmods.com/eldenringnightreign/mods/216",
            "黎明至黄昏": "https://www.nexusmods.com/eldenringnightreign/mods/199",
            "无缝联机": "https://www.nexusmods.com/eldenringnightreign/mods/3",
            "4阶段黑夜王": "https://www.nexusmods.com/eldenringnightreign/mods/273",
            "随机mod": "https://www.nexusmods.com/eldenringnightreign/mods/277",
            "动作大修mod": "https://www.nexusmods.com/eldenringnightreign/mods/287",
            "boss大修": "https://www.nexusmods.com/eldenringnightreign/mods/293"
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def get_mod_version(self, url):
        """获取mod的版本信息"""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # 主要方法：从Twitter meta标签获取版本信息
            version = None
            twitter_version_meta = soup.find('meta', {'property': 'twitter:data1'})
            if twitter_version_meta:
                version = twitter_version_meta.get('content', '').strip()

            # 备用方法1: 从页面标题提取版本号
            if not version or version == '':
                title = soup.find('title')
                if title:
                    title_text = title.get_text()
                    # 匹配标题中的版本号模式，如 "Mod Name 1.2.3 at Nexus"
                    import re
                    version_match = re.search(r'(\d+\.[\d\.]+)', title_text)
                    if version_match:
                        version = version_match.group(1)

            # 备用方法2: 查找页面中的版本标签
            if not version or version == '':
                version_element = soup.find('span', class_='version')
                if version_element:
                    version = version_element.get_text(strip=True)

            # 获取mod名称
            mod_name = None
            og_title_meta = soup.find('meta', {'property': 'og:title'})
            if og_title_meta:
                mod_name = og_title_meta.get('content', '').strip()

            # 获取更新时间 - 尝试多种方式
            update_time = None

            # 方法1: 查找time标签
            time_element = soup.find('time')
            if time_element:
                update_time = time_element.get('datetime') or time_element.get_text(strip=True)

            # 方法2: 查找更新日期相关的文本
            if not update_time:
                date_patterns = [
                    r'Updated:\s*([^<\n]+)',
                    r'Last updated:\s*([^<\n]+)',
                    r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'(\d{4}-\d{2}-\d{2})'
                ]
                page_text = soup.get_text()
                for pattern in date_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        update_time = match.group(1).strip()
                        break

            return {
                'version': version or 'Unknown',
                'mod_name': mod_name or 'Unknown',
                'update_time': update_time or 'Unknown',
                'last_checked': datetime.now().isoformat(),
                'url': url
            }

        except Exception as e:
            logging.error(f"获取版本信息失败 {url}: {str(e)}")
            return {
                'version': 'Error',
                'mod_name': 'Error',
                'update_time': 'Error',
                'last_checked': datetime.now().isoformat(),
                'url': url,
                'error': str(e)
            }
    
    def load_previous_versions(self):
        """加载之前保存的版本信息"""
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"读取版本文件失败: {str(e)}")
        return {}
    
    def save_versions(self, versions):
        """保存版本信息到文件"""
        try:
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(versions, f, ensure_ascii=False, indent=2)
            logging.info(f"版本信息已保存到 {self.version_file}")
        except Exception as e:
            logging.error(f"保存版本文件失败: {str(e)}")
    
    def send_wechat_notification(self, message):
        """发送企业微信通知"""
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
                    logging.info("企业微信通知发送成功")
                else:
                    logging.error(f"企业微信通知发送失败: {result}")
            else:
                logging.error(f"企业微信通知发送失败，状态码: {response.status_code}")
                
        except Exception as e:
            logging.error(f"发送企业微信通知异常: {str(e)}")
    
    def check_updates(self):
        """检查所有mod的更新"""
        logging.info("开始检查mod版本更新...")

        previous_versions = self.load_previous_versions()
        current_versions = {}
        updates_found = []
        errors_found = []

        for mod_name, mod_url in self.mods.items():
            logging.info(f"检查 {mod_name}...")

            current_info = self.get_mod_version(mod_url)
            current_versions[mod_name] = current_info

            # 检查是否获取失败
            if current_info.get('version') == 'Error':
                errors_found.append({
                    'name': mod_name,
                    'url': mod_url,
                    'error': current_info.get('error', 'Unknown error')
                })
                logging.error(f"{mod_name} 获取版本失败: {current_info.get('error', 'Unknown error')}")
                # 添加延迟后继续下一个
                time.sleep(2)
                continue

            # 检查是否有更新
            if mod_name in previous_versions:
                prev_info = previous_versions[mod_name]
                prev_version = prev_info.get('version', 'Unknown')
                curr_version = current_info.get('version', 'Unknown')

                # 版本比较逻辑改进 - 传递完整信息对象
                if self._is_version_updated(prev_info, current_info):
                    # 确定更新类型
                    version_changed = prev_version != curr_version
                    time_changed = (prev_info.get('update_time', 'Unknown') !=
                                  current_info.get('update_time', 'Unknown'))

                    update_type = []
                    if version_changed:
                        update_type.append("版本")
                    if time_changed:
                        update_type.append("上传时间")

                    updates_found.append({
                        'name': mod_name,
                        'mod_display_name': current_info.get('mod_name', mod_name),
                        'old_version': prev_version,
                        'new_version': curr_version,
                        'old_update_time': prev_info.get('update_time', 'Unknown'),
                        'new_update_time': current_info.get('update_time', 'Unknown'),
                        'url': mod_url,
                        'update_type': " + ".join(update_type)
                    })

                    update_desc = f"{mod_name}"
                    if version_changed:
                        update_desc += f" 版本: {prev_version} -> {curr_version}"
                    if time_changed:
                        update_desc += f" 时间: {prev_info.get('update_time', 'Unknown')} -> {current_info.get('update_time', 'Unknown')}"

                    logging.info(f"发现更新: {update_desc}")
            else:
                # 首次检查，记录当前版本但不发送通知
                logging.info(f"首次记录 {mod_name} 版本: {current_info.get('version', 'Unknown')}")

            # 添加延迟避免请求过快
            time.sleep(2)

        # 保存当前版本信息
        self.save_versions(current_versions)

        # 发送更新通知
        if updates_found:
            self._send_update_notification(updates_found)
            logging.info(f"发现 {len(updates_found)} 个mod更新")
        else:
            logging.info("未发现mod更新")

        # 如果有错误，记录但不发送通知（避免频繁报错）
        if errors_found:
            logging.warning(f"有 {len(errors_found)} 个mod获取版本失败")

        return current_versions, updates_found

    def _is_version_updated(self, old_info, new_info):
        """判断版本是否更新"""
        old_version = old_info.get('version', 'Unknown') if isinstance(old_info, dict) else old_info
        new_version = new_info.get('version', 'Unknown') if isinstance(new_info, dict) else new_info

        # 基本检查
        if old_version == 'Unknown' or new_version == 'Unknown':
            return False
        if old_version == 'Error' or new_version == 'Error':
            return False

        # 版本号比较
        version_changed = old_version != new_version

        # 上传时间比较（如果都是字典格式）
        time_changed = False
        if isinstance(old_info, dict) and isinstance(new_info, dict):
            old_time = old_info.get('update_time', 'Unknown')
            new_time = new_info.get('update_time', 'Unknown')

            if old_time != 'Unknown' and new_time != 'Unknown' and old_time != new_time:
                time_changed = True
                logging.info(f"检测到上传时间变化: {old_time} -> {new_time}")

        # 版本号变化或上传时间变化都视为更新
        return version_changed or time_changed

    def _send_update_notification(self, updates):
        """发送更新通知"""
        message = "🎮 Elden Ring Night Reign Mod 更新通知:\n\n"

        for update in updates:
            display_name = update.get('mod_display_name', update['name'])
            update_type = update.get('update_type', '版本')

            message += f"📦 {display_name}\n"
            message += f"   更新类型: {update_type}\n"

            # 版本信息
            if update['old_version'] != update['new_version']:
                message += f"   版本: {update['old_version']} → {update['new_version']}\n"
            else:
                message += f"   版本: {update['new_version']}\n"

            # 上传时间信息
            old_time = update.get('old_update_time', 'Unknown')
            new_time = update.get('new_update_time', 'Unknown')
            if old_time != new_time and old_time != 'Unknown' and new_time != 'Unknown':
                message += f"   上传时间: {old_time} → {new_time}\n"
            elif new_time != 'Unknown':
                message += f"   上传时间: {new_time}\n"

            message += f"   链接: {update['url']}\n\n"

        message += f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.send_wechat_notification(message)

def main():
    """主函数"""
    checker = ModVersionChecker()

    try:
        print("🎮 Elden Ring Night Reign Mod版本检查器")
        print("=" * 50)

        current_versions, updates = checker.check_updates()

        print("\n📋 当前版本信息:")
        print("-" * 50)
        for mod_name, info in current_versions.items():
            version = info.get('version', 'Unknown')
            mod_display_name = info.get('mod_name', mod_name)

            if info.get('error'):
                print(f"❌ {mod_name}: 获取失败")
                print(f"   错误: {info['error']}")
            else:
                print(f"✅ {mod_display_name}")
                print(f"   版本: {version}")
                if info.get('update_time') and info['update_time'] != 'Unknown':
                    print(f"   更新时间: {info['update_time']}")
            print()

        if updates:
            print(f"🔔 发现 {len(updates)} 个更新!")
            print("-" * 50)
            for update in updates:
                display_name = update.get('mod_display_name', update['name'])
                update_type = update.get('update_type', '版本')

                print(f"📦 {display_name}")
                print(f"   更新类型: {update_type}")

                # 显示版本变化
                if update['old_version'] != update['new_version']:
                    print(f"   版本: {update['old_version']} → {update['new_version']}")

                # 显示时间变化
                old_time = update.get('old_update_time', 'Unknown')
                new_time = update.get('new_update_time', 'Unknown')
                if old_time != new_time and old_time != 'Unknown' and new_time != 'Unknown':
                    print(f"   上传时间: {old_time} → {new_time}")

                print()
        else:
            print("✨ 所有mod都是最新版本")

        print(f"\n⏰ 检查完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except KeyboardInterrupt:
        print("\n\n⚠️ 程序被用户中断")
    except Exception as e:
        logging.error(f"程序执行异常: {str(e)}")
        print(f"\n❌ 程序执行异常: {str(e)}")

if __name__ == "__main__":
    main()
