#!/usr/bin/env python
import requests

TOKEN = "6976486529:AAGXLhfelhQT_4qufTJ1AdhcfkD1ZAuDShE"
chat_id = "-4096294187"
message = "failed to connect sso.demozone.vn"

try:
    r = requests.head("https://sso.demozone.vn")
    print(r.status_code)
    # prints the int of the status code. Find more at httpstatusrappers.com :)
except requests.ConnectionError:
    print("failed to connect")
    # API Send message to telegram
    url = "https://api.telegram.org/bot" + TOKEN + "/sendMessage?chat_id=" + chat_id + "&text=" + message
    print(requests.get(url).json())

