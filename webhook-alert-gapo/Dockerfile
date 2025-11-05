# syntax=docker/dockerfile:1

# Stage 1: Obfuscate Python sources with PyArmor
FROM python:3.11-alpine AS obfuscator
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apk add --no-cache ca-certificates curl
WORKDIR /src
COPY . /src/
RUN pip install --no-cache-dir -U pip setuptools wheel pyarmor \
    && pyarmor gen -O /src-obf -r /src/webhook_alert_gapo /src/wsgi.py

# Common runtime base
FROM python:3.11-alpine AS runtime-base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apk add --no-cache ca-certificates curl tzdata
RUN adduser -D appuser
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -U pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt
COPY gunicorn.conf.py /app/gunicorn.conf.py
COPY templates /app/templates
COPY webhook_alert_gapo /app/webhook_alert_gapo
USER appuser
EXPOSE 5051
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:application"]

# Stage 2a: Runtime with obfuscated sources
FROM runtime-base AS runtime-obf
COPY --from=obfuscator /src-obf/ /app/

# Stage 2b: Runtime without obfuscation (plain sources)
FROM runtime-base AS runtime-plain
COPY webhook_alert_gapo /app/webhook_alert_gapo
COPY wsgi.py /app/wsgi.py