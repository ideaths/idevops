import os
import hmac
import hashlib
import ipaddress
import pyotp
from functools import wraps
from flask import request, jsonify, g


def _ip_in_whitelist(remote_ip: str, whitelist: list[str]) -> bool:
    if not whitelist:
        return True
    try:
        ip_obj = ipaddress.ip_address(remote_ip)
    except ValueError:
        return False
    for entry in whitelist:
        try:
            if '/' in entry:
                if ip_obj in ipaddress.ip_network(entry, strict=False):
                    return True
            else:
                if ip_obj == ipaddress.ip_address(entry):
                    return True
        except ValueError:
            continue
    return False


def require_token(config, logger, metrics):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not config.WEBHOOK_TOKEN:
                return f(*args, **kwargs)
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1]
            elif request.headers.get('X-Auth-Token'):
                token = request.headers.get('X-Auth-Token')
            else:
                token = request.args.get('token')
            if not token:
                logger.warning(f"Unauthorized access attempt from {request.remote_addr} - no token")
                metrics['alerts_filtered'].labels(reason='unauthorized').inc()
                return jsonify({'error': 'Authentication required'}), 401
            if not hmac.compare_digest(token, config.WEBHOOK_TOKEN):
                logger.warning(f"Invalid token from {request.remote_addr}")
                metrics['alerts_filtered'].labels(reason='invalid_token').inc()
                return jsonify({'error': 'Invalid token'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_webhook_signature():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            signature_header = os.getenv('WEBHOOK_SIGNATURE_HEADER')
            signature_secret = os.getenv('WEBHOOK_SIGNATURE_SECRET')
            if not signature_header or not signature_secret:
                return f(*args, **kwargs)
            provided_signature = request.headers.get(signature_header)
            if not provided_signature:
                return jsonify({'error': 'Missing signature'}), 401
            payload = request.get_data()
            expected_signature = hmac.new(signature_secret.encode(), payload, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(provided_signature, expected_signature):
                return jsonify({'error': 'Invalid signature'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin_mfa():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            totp_secret = os.getenv("ADMIN_MFA_TOTP_SECRET", "").strip()
            ip_whitelist_env = os.getenv("ADMIN_IP_WHITELIST", "")
            whitelist = [x.strip() for x in ip_whitelist_env.split(",") if x.strip()]
            try:
                remote_ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '').split(',')[0].strip()
                if whitelist and _ip_in_whitelist(remote_ip, whitelist):
                    return f(*args, **kwargs)
            except Exception:
                pass
            if not totp_secret:
                return f(*args, **kwargs)
            provided_code = request.headers.get("X-Admin-MFA") or request.args.get("mfa")
            if not provided_code:
                return jsonify({"error": "MFA required"}), 401
            try:
                totp = pyotp.TOTP(totp_secret)
                if not totp.verify(provided_code, valid_window=1):
                    return jsonify({"error": "Invalid MFA code"}), 401
            except Exception:
                return jsonify({"error": "MFA verification failed"}), 500
            return f(*args, **kwargs)
        return decorated_function
    return decorator