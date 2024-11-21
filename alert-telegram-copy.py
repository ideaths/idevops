#!/usr/bin/env python
import requests
import os

def check_http_service(url):
    try:
        response = requests.head(url, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error checking HTTP service: {e}")
        return False

def send_telegram_alert(message):
    # Replace 'YOUR_BOT_TOKEN' and 'YOUR_CHAT_ID' with your actual Telegram bot token and chat ID
    bot_token = '6976486529:AAGXLhfelhQT_4qufTJ1AdhcfkD1ZAuDShE'
    chat_id = '-4096294187'
    telegram_api_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    
    data = {
        'chat_id': chat_id,
        'text': message,
    }

    response = requests.post(telegram_api_url, json=data)
    return response.json()

def main():
    services_to_check = [
        'https://sso.demozone.vn',
        'https://backupkg.idevops.io.vn',
        'https://gitlaskdfjl.com',
        # Add more services as needed
    ]
    for service_url in services_to_check:
        if not check_http_service(service_url):
            alert_message = f"Warning: The service at {service_url} is not responding,"
            response = send_telegram_alert(alert_message)
            print("Telegram API Response:", response)

if __name__ == "__main__":
    main()