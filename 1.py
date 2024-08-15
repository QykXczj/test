import json
import os
import shutil
import zipfile
import requests
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning
VX_BOT_KEY = '84b5c352-7018-4ca3-9198-7a2e2fb9b0af'
def send_VX_Bot_message(message):
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
def parse_html(response):
    """解析 HTML 并提取版本号和文件 ID。"""
    soup = BeautifulSoup(response.text, 'html.parser')
    version_meta = soup.find('meta', {'property': 'twitter:data1'})
    version_number = version_meta['content'] if version_meta else None
    file_element = soup.find('dt', class_='file-expander-header clearfix accopen')
    file_id = file_element.get('data-id') if file_element else None
    return version_number, file_id
def generate_download_url(file_id):
    """生成下载 URL。"""
    url = "https://www.nexusmods.com/Core/Libs/Common/Managers/Downloads?GenerateDownloadUrl"
    # 请求头
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": "_ga=GA1.1.629248622.1719590561; _pk_id.1.3564=950705183bd94c2d.1719590561.; fwroute=1722573480.797.1140.57643|b295758090068ae543818c1ba2aeea3e; nexusmods_session=b486138d0382001e53c4c6c709c817c6; nexusmods_session_refresh=1722576817; ab=0|1722586079; _pk_ref.1.3564=%5B%22%22%2C%22%22%2C1722585780%2C%22https%3A%2F%2Fusers.nexusmods.com%2F%22%5D; _pk_ses.1.3564=1; _ga_N0TELNQ37M=GS1.1.1722585776.36.1.1722585780.0.0.0; cf_clearance=AXZNvT44cV_GxbgM2HDTCZg5NfQM9Zng94Gkmvk.XC0-1722585781-1.0.1.1-70dxNju4rj3seiFMOZnS_Yo7OK0SFvEL3MYPqyAWbXJQjSTi2UDC5jWzlnezFVn3flThqAa2GlD3HahEWg8DZA"，
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
        response = session.post(url, headers=headers, data=data)
        response.raise_for_status()
        response_data = response.json()

        # 检查返回的数据是否为字典
        if isinstance(response_data, dict):
            download_url = response_data.get('url')
            if download_url is None:
                print("下载 URL 未找到，请检查返回数据。")
            return download_url
        else:
            print(f"返回的数据不是字典，而是 {type(response_data)}。")
            return None

    except requests.RequestException as e:
        print(f"POST 请求过程中发生错误: {e}")
        exit(1)
    except ValueError as e:
        # 如果无法解析 JSON 数据
        print(f"无法解析 JSON 数据: {e}")
        exit(1)
# 网页 URL
url_main = "https://www.nexusmods.com/eldenring/mods/510?tab=files"
response = requests.get(url_main)
# 解析 HTML
version_number, file_id = parse_html(response)
download_url = generate_download_url(file_id)
print(download_url)




