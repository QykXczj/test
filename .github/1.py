import requests
curl='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=84b5c352-7018-4ca3-9198-7a2e2fb9b0af'
Headers = 'Content-Type: application/json'

# response = requests.post(curl, json={
#     "msgtype": "text",
#     "text": {
#         "content": "hello world"
#     }
# })
response = requests.post(curl, json={
    "msgtype": "text",
    "text": {
        "content": "hello world"
    }
})
