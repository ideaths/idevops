from typing import Dict, Tuple


class AlertFilter:
    def __init__(self, config):
        self.config = config

    def is_ignored(self, alert: Dict) -> Tuple[bool, str]:
        labels = alert.get("labels", {})
        namespace = labels.get("namespace", "")
        alertname = labels.get("alertname", "")
        job = labels.get("job", "")
        routing_value = labels.get(self.config.ROUTING_LABEL, "")
        if routing_value not in self.config.ALLOWED_VALUES:
            return True, "invalid_routing_value"
        if namespace in self.config.EXCLUDED_NAMESPACES:
            return True, "excluded_namespace"
        if alertname in self.config.EXCLUDED_ALERTNAMES:
            return True, "excluded_alertname"
        if job in self.config.EXCLUDED_JOBS:
            return True, "excluded_job"
        return False, ""