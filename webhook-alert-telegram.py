# -*- coding: utf-8 -*-
import logging
from flask import Flask, request, jsonify
import requests

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Fix cứng Telegram Bot Token và Chat ID
TELEGRAM_BOT_TOKEN = "6494203431:AAFWpCkE_sTYAKRkcn0PDv-hPBdArT_tPRE"  # Thay bằng token thực tế
TELEGRAM_CHAT_ID = "-900003347"  # Thay bằng Chat ID thực tế (bắt đầu bằng `-100` nếu là nhóm)

# URL của API Telegram
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Hàm gửi tin nhắn Telegram
def send_to_telegram(message):
    logger.info("Preparing to send message to Telegram.")
    logger.debug(f"Telegram API URL: {TELEGRAM_API_URL}")
    logger.debug(f"Telegram Chat ID: {TELEGRAM_CHAT_ID}")
    logger.debug(f"Message content to send: {message}")

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    # Log gói tin gửi đi
    logger.info(f"Payload gửi tới Telegram: {payload}")

    try:
        response = requests.post(TELEGRAM_API_URL, json=payload)
        logger.info(f"Request sent to Telegram API. Status code: {response.status_code}")
        logger.debug(f"Response content: {response.text}")

        if response.status_code == 200:
            logger.info("Message sent to Telegram successfully.")
        else:
            logger.error(f"Failed to send message to Telegram. "
                         f"Status Code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        logger.exception("Exception occurred while sending message to Telegram.")

# Hàm định dạng thông điệp theo mẫu
def format_alerts(alerts):
    logger.info("Formatting alerts for Telegram message.")
    alert_list = []
    for alert in alerts:
        alert_name = alert.get('labels', {}).get('alertname', 'n/a')
        summary = alert.get('annotations', {}).get('summary', '')
        description = alert.get('annotations', {}).get('description', '')
        labels = alert.get('labels', {})

        logger.debug(f"Processing alert: {alert_name}, Labels: {labels}")

        # Tạo danh sách nhãn
        labels_str = "\n".join(
            f"  <i>{key}</i>: <code>{value}</code>" for key, value in labels.items()
        )

        # Tạo đoạn văn bản chi tiết cho từng alert
        alert_item = (
            f"🪪 <b>{alert_name}</b>\n"
            f"{'📝 ' + summary if summary else ''}\n"
            f"{'📖 ' + description if description else ''}\n"
            f"🏷 Labels:\n{labels_str}\n"
        )
        alert_list.append(alert_item)
    return "\n".join(alert_list)

# Endpoint nhận webhook từ Alertmanager
@app.route('/alertmanager', methods=['POST'])
def alertmanager_webhook():
    try:
        logger.info("Received request on /alertmanager endpoint.")
        
        # Ghi log gói tin nhận được
        raw_data = request.get_data(as_text=True)
        logger.info(f"Gói tin nhận được từ client: {raw_data}")
        
        data = request.json  # Nhận payload JSON từ Alertmanager
        logger.debug(f"Parsed JSON payload: {data}")

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

        # Gửi tin nhắn đến Telegram
        send_to_telegram(message)

        logger.info("Alerts processed successfully.")
        return jsonify({"message": "Alerts processed"}), 200
    except Exception as e:
        logger.exception("Error processing alert.")
        return jsonify({"error": "Error processing alert"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
