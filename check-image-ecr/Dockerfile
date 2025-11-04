# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder
WORKDIR /opt/app
COPY requirements.txt ./
RUN pip install --upgrade pip && pip wheel --wheel-dir /opt/wheels -r requirements.txt

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOG_DIR=/app/logs \
    AWS_REGION=ap-southeast-1 \
    TARGET_NAMESPACE=digigold
WORKDIR /app

# Non-root user
RUN addgroup --system app && adduser --system --ingroup app app
COPY --from=builder /opt/wheels /opt/wheels
RUN pip install --no-cache-dir /opt/wheels/*

COPY app /app

VOLUME ["/app"]

USER app

EXPOSE 8080
CMD ["python", "/app/main.py"]