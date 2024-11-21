# Sử dụng image Golang chính thức làm base image
FROM golang:1.20 AS builder

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Tạo go.mod và go.sum
RUN echo "module telegram-alert" > go.mod \
    && go mod tidy

# Copy mã nguồn vào container
COPY . .

# Build ứng dụng Go
RUN go build -o main .

# Sử dụng Debian để chạy ứng dụng trong một image nhỏ hơn
FROM debian:bullseye-slim

# Cài đặt ca-certificates
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy ứng dụng đã biên dịch từ builder container
COPY --from=builder /app/main .

# Copy các thư mục cần thiết (templates, logs, v.v.) từ container builder
COPY --from=builder /app/templates ./templates
COPY --from=builder /app/logs ./logs

# Mở cổng 5000
EXPOSE 5000

# Chạy ứng dụng Go
CMD ["./main"]
