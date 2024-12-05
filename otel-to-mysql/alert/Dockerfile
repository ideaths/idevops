# Sử dụng Python base image
FROM python:3.9-slim

# Đặt thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements.txt và cài đặt các dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn ứng dụng vào container
COPY . .

# Expose cổng ứng dụng (nếu cần)
EXPOSE 5000

# Lệnh mặc định để chạy ứng dụng
CMD ["python", "app.py"]