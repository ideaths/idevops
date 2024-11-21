# Sử dụng image python làm base image
FROM python:3.8-slim

# Cài đặt các thư viện cần thiết
RUN pip install --no-cache-dir flask requests jinja2

# Tạo thư mục ứng dụng trong container
WORKDIR /app

# Copy các file mã nguồn vào container
COPY . /app/

# Mở cổng 5000 để ứng dụng Flask có thể nghe
EXPOSE 5000

# Chạy ứng dụng Flask
CMD ["python", "app.py"]
