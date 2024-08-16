import json
import os
import shutil
import zipfile
import requests
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
TELEGRAM_BOT_TOKEN = '7438184086:AAGBvptwMKmOttFDWYAXZpnE8KHGJKf8xzo'
TELEGRAM_CHAT_ID = '5240805827'
VX_BOT_KEY = '84b5c352-7018-4ca3-9198-7a2e2fb9b0af'
LOCAL_VERSION = '1.8.3'
LOCAL_PATH = ''
COOKIE = '_ga=GA1.1.629248622.1719590561; _pk_id.1.3564=950705183bd94c2d.1719590561.; fwroute=1722573480.797.1140.57643|b295758090068ae543818c1ba2aeea3e; nexusmods_session=b486138d0382001e53c4c6c709c817c6; nexusmods_session_refresh=1722576817; ab=0|1722586079; _pk_ref.1.3564=%5B%22%22%2C%22%22%2C1722585780%2C%22https%3A%2F%2Fusers.nexusmods.com%2F%22%5D; _pk_ses.1.3564=1; _ga_N0TELNQ37M=GS1.1.1722585776.36.1.1722585780.0.0.0; cf_clearance=AXZNvT44cV_GxbgM2HDTCZg5NfQM9Zng94Gkmvk.XC0-1722585781-1.0.1.1-70dxNju4rj3seiFMOZnS_Yo7OK0SFvEL3MYPqyAWbXJQjSTi2UDC5jWzlnezFVn3flThqAa2GlD3HahEWg8DZA'

class ModDownloader:
    def __init__(self):
        self.local_version = LOCAL_VERSION
        self.local_path = LOCAL_PATH
        self.cookies = COOKIE
        self.session = None

    def create_requests_session(self):
        """创建一个配置好的请求会话。"""
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.verify = False  # 忽略 SSL 验证
        return session

    def fetch_webpage(self, url):
        """获取网页内容。"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"请求过程中发生错误: {e}")
            exit(1)

    def parse_html(self, response):
        """解析 HTML 并提取版本号和文件 ID。"""
        soup = BeautifulSoup(response.text, 'html.parser')
        version_meta = soup.find('meta', {'property': 'twitter:data1'})
        version_number = version_meta['content'] if version_meta else None
        file_element = soup.find('dt', class_='file-expander-header clearfix accopen')
        file_id = file_element.get('data-id') if file_element else None
        return version_number, file_id

    def generate_download_url(self, file_id):
        """生成下载 URL。"""
        url = "https://www.nexusmods.com/Core/Libs/Common/Managers/Downloads?GenerateDownloadUrl"
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": self.cookies,
            "Origin": "https://www.nexusmods.com",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
            "X-Requested-With": "XMLHttpRequest",
        }
        data = {
            'fid': file_id,
            'game_id': '4333',
        }
        try:
            response = self.session.post(url, data=data, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            if isinstance(response_data, dict):
                return response_data.get('url')
            else:
                print(f"返回的数据不是字典，而是 {type(response_data)}.")
                return None
        except (requests.RequestException, ValueError) as e:
            print(f"请求过程中发生错误: {e}")
            exit(1)

    def download_and_extract_file(self, download_url, version_number):
        """下载文件并解压。"""
        if download_url:
            try:
                file_response = self.session.get(download_url, stream=True)
                file_response.raise_for_status()
                file_name = f"Seamless_Co-op_v{version_number}.zip"
                save_path = os.path.join(self.local_path, file_name)
                with open(save_path, 'wb') as file:
                    for chunk in file_response.iter_content(chunk_size=65536):
                        if chunk:
                            file.write(chunk)
                print(f"文件已成功下载至 {save_path}。")

                # 解压文件
                extract_path = os.path.join(self.local_path, f"Seamless_Co-op_v{version_number}")
                with zipfile.ZipFile(save_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)

                # 检查解压后的文件
                files_in_zip = zip_ref.namelist()
                all_files_extracted = all(os.path.exists(os.path.join(extract_path, file_name)) and os.path.getsize(os.path.join(extract_path, file_name)) > 0 for file_name in files_in_zip)

                if all_files_extracted:
                    print(f"所有文件已成功解压至 {extract_path}。")
                    # 删除解压后的文件
                    shutil.rmtree(extract_path)
                    print(f"解压后的文件已被删除。")
                    return True
                else:
                    print(f"部分文件未正确从 {save_path} 中解压。")

            except Exception as e:
                print(f"文件处理过程中发生错误: {e}")
                exit(1)
            return False

    # def update_local_version(self, local_version, version_number):
    #     """更新本地版本。"""
    #     old_target_path = os.path.join(self.local_path, f"Seamless_Co-op_v{local_version}.zip")
    #     old_extract_path = os.path.join(self.local_path, f"Seamless_Co-op_v{local_version}")
    #
    #     # 清除旧版本的文件
    #     if os.path.exists(old_target_path):
    #         os.remove(old_target_path)
    #         print(f"已删除旧版本的压缩包 {old_target_path}。")
    #     if os.path.exists(old_extract_path):
    #         shutil.rmtree(old_extract_path)
    #         print(f"已删除旧版本的解压文件夹 {old_extract_path}。")
    #
    #     # 更新版本信息
    #     with open(self.config_file_path, 'r') as version_file:
    #         config_data = json.load(version_file)
    #     config_data["version"] = version_number
    #     with open(self.config_file_path, 'w') as version_file:
    #         json.dump(config_data, version_file, indent=4)

    def check_version_before_download(self, version_number):
        """检查本地版本与目标版本，避免重复下载。"""
        target_path = os.path.join(self.local_path, f"Seamless_Co-op_v{version_number}.zip")
        extract_path = os.path.join(self.local_path, f"Seamless_Co-op_v{version_number}")

        # 比较本地版本与目标版本
        if self.local_version != version_number:
            print("发现新版本，开始下载。")
            self.send_VX_Bot_message("发现新版本，开始下载。")
            return True

        # 检查目标路径或解压路径是否存在文件
        if not (os.path.exists(target_path) and os.path.getsize(target_path) > 0) and \
           not (os.path.exists(extract_path) and os.listdir(extract_path)):
            # 目标路径或解压路径不存在或为空，允许下载
            print("目标路径或解压路径不存在或为空，允许下载。")
            return True

        print("当前版本已是最新，无需重新下载。")
        return False

    def send_telegram_message(message):
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'reply_markup': {
                'inline_keyboard': [
                    [
                        {
                            'text': '问题反馈❓',
                            'url': 'https://t.me/yxjsjl'
                        }
                    ]
                ]
            }
        }
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                print(f"发送消息到Telegram失败: {response.text}")
        except Exception as e:
            print(f"发送消息到Telegram时出错: {e}")

    def send_VX_Bot_message(self, message):
        url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={VX_BOT_KEY}"
        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                print(f"发送消息到VX_BOT失败: {response.text}")
        except Exception as e:
            print(f"发送消息到VX_Bot时出错: {e}")
    def run(self, url_main):
        """运行下载流程。"""
        self.session = self.create_requests_session()

        # 获取网页内容
        response = self.fetch_webpage(url_main)

        # 解析 HTML
        version_number, file_id = self.parse_html(response)
        print(f"模组版本号: {version_number}")
        print(f"文件 ID: {file_id}")

        # 检查版本
        if self.check_version_before_download(version_number):
            # 生成下载 URL
            download_url = self.generate_download_url(file_id)
            print(f"下载链接: {download_url}")

            # 下载并解压文件
            if self.download_and_extract_file(download_url, version_number):
                print("下载并解压文件成功。")
                # self.update_local_version(self.local_version, version_number)

        # 关闭会话
        self.session.close()

if __name__ == "__main__":
    downloader = ModDownloader()
    url_main = "https://www.nexusmods.com/eldenring/mods/510?tab=files"
    downloader.run(url_main)





