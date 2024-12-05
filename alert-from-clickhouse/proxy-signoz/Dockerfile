# Sử dụng Python 3.9 làm base image
FROM python:3.9-slim

WORKDIR /app
# Cài đặt các thư viện cần thiết
RUN pip install requests

# Copy file proxy.py vào container
COPY app.py .

# Expose cổng (mặc định sẽ là biến môi trường)
EXPOSE 8080

# Chạy script proxy
CMD ["python", "app.py"]
