import os
import json
from dataclasses import dataclass
from typing import Dict


@dataclass
class ChatConfig:
    collab_id: int
    bot_id: int
    receiver_id: str
    max_retries: int = 3
    timeout: int = 10


class Config:
    def __init__(self):
        self.GAPO_API_URL = os.getenv("GAPO_API_URL", "http://10.6.131.11:8082/webhooktest4pt/chatbot/alert-bot")
        self.GAPO_SIGNATURE = os.getenv("GAPO_SIGNATURE", "1")
        self.ALERTMANAGER_ENDPOINT = os.getenv("ALERTMANAGER_ENDPOINT", "/alertmanager")
        self.SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())
        self.WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN", "")
        self.IS_PRODUCTION = os.getenv("IS_PRODUCTION", "false").lower() == "true"

        self.WEBHOOK_IP_WHITELIST = [ip.strip() for ip in os.getenv("WEBHOOK_IP_WHITELIST", "").split(',') if ip.strip()]
        self.LIMITER_STORAGE = os.getenv("LIMITER_STORAGE", "memory://")
        self.MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "1000"))
        self.WORKER_THREADS = int(os.getenv("WORKER_THREADS", "4"))
        self.QUEUE_PUT_TIMEOUT = int(os.getenv("QUEUE_PUT_TIMEOUT", "2"))
        self.WORKER_IDLE_LOG_INTERVAL = int(os.getenv("WORKER_IDLE_LOG_INTERVAL", "30"))
        self.RATE_LIMIT = os.getenv("RATE_LIMIT", "100 per minute")
        self.MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "1048576"))
        self.LOG_ALERT_DETAILS = os.getenv("LOG_ALERT_DETAILS", "false").lower() == "true"
        self.ROUTING_LABEL = os.getenv("ROUTING_LABEL", "system")
        self.ALLOWED_VALUES = os.getenv("ALLOWED_VALUES", "efast,ipay").split(',')

        self.DEFAULT_CHAT_CONFIG = ChatConfig(
            collab_id=int(os.getenv("DEFAULT_COLLAB_ID", "1")),
            bot_id=int(os.getenv("DEFAULT_BOT_ID", "1")),
            receiver_id=os.getenv("DEFAULT_RECEIVER_ID", "1")
        )

        self.EXCLUDED_NAMESPACES = set(os.getenv(
            "EXCLUDED_NAMESPACES",
            "cattle-prometheus,cattle-system,cert-manager,default,kube-logging"
        ).split(','))
        self.EXCLUDED_ALERTNAMES = set(os.getenv(
            "EXCLUDED_ALERTNAMES",
            "InfoInhibitor,Watchdog,etcdHighNumberOfFailedGRPCRequests"
        ).split(','))
        self.EXCLUDED_JOBS = set(os.getenv("EXCLUDED_JOBS", "kafka,abcd").split(','))

        self.ROUTING_CONFIG = self._load_routing_config()

        # Healthcheck configuration
        # Comma-separated list of URLs to check
        self.HEALTHCHECK_URLS = [u.strip() for u in os.getenv("HEALTHCHECK_URLS", "").split(',') if u.strip()]
        # Interval seconds between checks
        self.HEALTHCHECK_INTERVAL = int(os.getenv("HEALTHCHECK_INTERVAL", "60"))
        # Timeout per request
        self.HEALTHCHECK_TIMEOUT = int(os.getenv("HEALTHCHECK_TIMEOUT", "10"))
        # Routing value used when sending healthcheck alerts (must exist in ROUTING_CONFIG or DEFAULT)
        self.HEALTHCHECK_ROUTING = os.getenv("HEALTHCHECK_ROUTING", "efast")
        # Minimum status code considered healthy (< this will alert)
        self.HEALTHCHECK_MIN_OK = int(os.getenv("HEALTHCHECK_MIN_OK", "200"))
        # Maximum status code considered healthy (>= this will alert)
        self.HEALTHCHECK_MAX_OK = int(os.getenv("HEALTHCHECK_MAX_OK", "399"))

    def _load_routing_config(self) -> Dict[str, ChatConfig]:
        config_str = os.getenv("ROUTING_CONFIG", '{}')
        try:
            raw_config = json.loads(config_str)
        except json.JSONDecodeError:
            raw_config = {}

        routing_config: Dict[str, ChatConfig] = {}
        for value in self.ALLOWED_VALUES:
            if value in raw_config:
                cfg = raw_config[value]
                collab_id = int(cfg.get('collab_id', self.DEFAULT_CHAT_CONFIG.collab_id))
                bot_id = int(cfg.get('bot_id', self.DEFAULT_CHAT_CONFIG.bot_id))
                receiver_id = str(cfg.get('receiver_id', self.DEFAULT_CHAT_CONFIG.receiver_id))
                routing_config[value] = ChatConfig(collab_id=collab_id, bot_id=bot_id, receiver_id=receiver_id)
            else:
                collab_env = os.getenv(f"{value.upper()}_COLLAB_ID", str(self.DEFAULT_CHAT_CONFIG.collab_id))
                bot_env = os.getenv(f"{value.upper()}_BOT_ID", str(self.DEFAULT_CHAT_CONFIG.bot_id))
                receiver_env = os.getenv(f"{value.upper()}_RECEIVER_ID", self.DEFAULT_CHAT_CONFIG.receiver_id)
                try:
                    collab_id = int(collab_env)
                except Exception:
                    collab_id = self.DEFAULT_CHAT_CONFIG.collab_id
                try:
                    bot_id = int(bot_env)
                except Exception:
                    bot_id = self.DEFAULT_CHAT_CONFIG.bot_id
                routing_config[value] = ChatConfig(collab_id=collab_id, bot_id=bot_id, receiver_id=str(receiver_env))
        return routing_config