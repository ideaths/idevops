#!/usr/bin/env python
import os
import requests
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def get_not_ready_nodes():
    config.load_kube_config()  # Load kubeconfig file (usually located at ~/.kube/config)

    v1 = client.CoreV1Api()
    nodes = v1.list_node()

    not_ready_nodes = []
    for node in nodes.items:
        for condition in node.status.conditions:
            if condition.type == 'Ready' and condition.status != 'True':
                not_ready_nodes.append(node.metadata.name)

    return not_ready_nodes

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
    not_ready_nodes = get_not_ready_nodes()

    if not_ready_nodes:
        alert_message = f"Warning: The following nodes are not ready in the Kubernetes cluster:\n{', '.join(not_ready_nodes)}"
        response = send_telegram_alert(alert_message)
        print("Telegram API Response:", response)
    else:
        print("All nodes are ready.")

if __name__ == "__main__":
    main()