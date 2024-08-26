import requests

def notify_message(message):
    url = 'http://localhost:18080/telegram/message'
    body = {
        "chat_name": "noticenter",
        "message": message,
        "async": True
    }
    requests.post(url=url, json=body)
