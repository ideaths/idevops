import os
from http.server import SimpleHTTPRequestHandler
import socketserver
import requests
import json

# Đọc cấu hình từ biến môi trường
SIGNOZ_URL = os.getenv("SIGNOZ_URL", "http://10.6.160.137:3301")
EMAIL = os.getenv("EMAIL", "view@icbv.com")
PASSWORD = os.getenv("PASSWORD", "Ab123456")
PORT = int(os.getenv("PORT", 8080))  # Cổng mặc định là 8080

# Hàm lấy accessJwt
def get_access_jwt():
    response = requests.post(
        f"{SIGNOZ_URL}/api/v1/login",
        headers={"Content-Type": "application/json"},
        json={"email": EMAIL, "password": PASSWORD},
        verify=False
    )
    if response.status_code == 200:
        return response.json().get("accessJwt")
    else:
        raise Exception("Failed to get accessJwt: " + response.text)

# Lấy JWT ban đầu
access_jwt = get_access_jwt()

# Proxy server class
class ProxyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global access_jwt
        try:
            target_url = f"{SIGNOZ_URL}{self.path}"
            headers = {key: value for key, value in self.headers.items()}
            headers["Authorization"] = f"Bearer {access_jwt}"
            response = requests.get(target_url, headers=headers, verify=False)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)
        except Exception as e:
            self.send_error(500, f"Error: {e}")

    def do_POST(self):
        global access_jwt
        try:
            target_url = f"{SIGNOZ_URL}{self.path}"
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            headers = {key: value for key, value in self.headers.items()}
            headers["Authorization"] = f"Bearer {access_jwt}"
            response = requests.post(
                target_url,
                headers=headers,
                data=post_data,
                verify=False
            )
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)
        except Exception as e:
            self.send_error(500, f"Error: {e}")

# Chạy proxy
def run_proxy():
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        print(f"Proxy server running on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_proxy()
