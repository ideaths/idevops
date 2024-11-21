import logging
import os
from flask import Flask, request, jsonify
import requests
from jinja2 import Environment, FileSystemLoader

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Lấy các biến từ environment variables
WORKCHAT_API_URL = os.getenv("WORKCHAT_API_URL", "http://10.0.72.130:8081/v1/messageSupport")  # Mặc định nếu không có
THREAD_ID = os.getenv("THREAD_ID", "61555923755026")
USER_LIST = os.getenv("USER_LIST", "ducdt1")
PRIORITY = os.getenv("PRIORITY", "1")

# Thiết lập Jinja2 Environment để load template
template_loader = FileSystemLoader(searchpath="./")
template_env = Environment(loader=template_loader)

# Hàm gửi tin nhắn đến WorkChat
def send_to_workchat(message):
    logger.info(f"Preparing to send message to WorkChat. API URL: {WORKCHAT_API_URL}")
    logger.debug(f"Message content: {message}")
    
    headers = {
        'Content-Type': 'application/json',
        'charset': 'UTF-8',
        'Accept': 'application/json'
    }

    payload = {
        "threadId": THREAD_ID,
        "userList": USER_LIST,
        "content": message,
        "priority": PRIORITY
    }

    logger.debug(f"Sending payload to WorkChat: {payload}")  # Log gói tin gửi đi

    try:
        response = requests.post(WORKCHAT_API_URL, json=payload, headers=headers)
        logger.info(f"Request sent to WorkChat API. Status code: {response.status_code}")
        logger.debug(f"Response text: {response.text}")

        if response.status_code == 200:
            logger.info("Message sent to WorkChat successfully.")
        else:
            logger.error(f"Failed to send message to WorkChat. "
                         f"Status Code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        logger.exception("Exception occurred while sending message to WorkChat.")

# Hàm định dạng thông điệp theo mẫu từ template
def format_alerts(alerts):
    logger.info("Formatting alerts for WorkChat message.")
    alert_list = []
    
    # Load the template
    template = template_env.get_template("alert_template.html")

    for alert in alerts:
        alert_name = alert.get('labels', {}).get('alertname', 'n/a')
        summary = alert.get('annotations', {}).get('summary', '')
        description = alert.get('annotations', {}).get('description', '')
        labels = alert.get('labels', {})

        logger.debug(f"Processing alert: {alert_name}, Labels: {labels}")

        # Render the template with the alert data
        alert_item = template.render(
            alert_name=alert_name,
            summary=summary,
            description=description,
            labels=labels
        )
        alert_list.append(alert_item)
    
    return "\n".join(alert_list)

# Endpoint nhận webhook từ Alertmanager
@app.route('/alertmanager', methods=['POST'])
def alertmanager_webhook():
    try:
        logger.info("Received request on /alertmanager endpoint.")
        data = request.json  # Nhận payload JSON từ Alertmanager

        # Log gói tin nhận từ Alertmanager (client)
        logger.debug(f"Received webhook payload: {data}")

        if not data:
            logger.warning("Received empty or invalid JSON payload.")
            return jsonify({"error": "Invalid JSON payload"}), 400

        # Phân loại cảnh báo
        firing_alerts = format_alerts([ 
            alert for alert in data.get('alerts', [])
            if alert.get('status') == 'firing'
        ])
        resolved_alerts = format_alerts([ 
            alert for alert in data.get('alerts', [])
            if alert.get('status') == 'resolved'
        ])

        # Xây dựng tin nhắn tổng hợp
        message = ""
        if firing_alerts:
            logger.info("Detected firing alerts.")
            message += f"🔥 <b>Alerts Firing</b> 🔥\n{firing_alerts}\n"
        if resolved_alerts:
            logger.info("Detected resolved alerts.")
            message += f"✅ <b>Alerts Resolved</b> ✅\n{resolved_alerts}\n"

        if not message:
            logger.info("No alerts to process.")
            message = "No alerts to process."

        # Gửi tin nhắn đến WorkChat
        send_to_workchat(message)

        logger.info("Alerts processed successfully.")
        return jsonify({"message": "Alerts processed"}), 200
    except Exception as e:
        logger.exception("Error processing alert.")
        return jsonify({"error": "Error processing alert"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
