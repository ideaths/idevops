import os
import sys
from functools import lru_cache
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape


class TemplateManager:
    def __init__(self, template_dir="./templates"):
        env_template_dir = os.getenv("TEMPLATE_DIR")
        if env_template_dir and os.path.isdir(env_template_dir):
            template_dir = env_template_dir
        else:
            meipass = getattr(sys, '_MEIPASS', None)
            if meipass:
                candidate = os.path.join(meipass, 'templates')
                if os.path.isdir(candidate):
                    template_dir = candidate

        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            cache_size=50,
        )
        self.fallback_template = """
🔥 **{{ alert_name }}**
{%- if summary %}\n📝 {{ summary }}{%- endif %}
{%- if description %}\n📄 {{ description }}{%- endif %}
\n🏷️ {{ routing_label|title }}: {{ routing_value }}
\n🗂️ Tất cả labels:
{%- for key, value in labels.items()|sort %}
- {{ key }}: {{ value }}
{%- endfor %}
{%- if annotations %}
\n📝 Tất cả annotations:
{%- for key, value in annotations.items()|sort %}
- {{ key }}: {{ value }}
{%- endfor %}
{%- endif %}
"""

    @lru_cache(maxsize=10)
    def get_template(self, name='alert_template.html'):
        try:
            return self.env.get_template(name)
        except TemplateNotFound:
            return self.env.from_string(self.fallback_template)

    def render_alert(self, alert, routing_label, routing_value):
        template = self.get_template()
        return template.render(
            alert_name=alert.get('labels', {}).get('alertname', 'Unknown'),
            summary=alert.get('annotations', {}).get('summary', ''),
            description=alert.get('annotations', {}).get('description', ''),
            labels=alert.get('labels', {}),
            annotations=alert.get('annotations', {}),
            routing_label=routing_label,
            routing_value=routing_value,
        )