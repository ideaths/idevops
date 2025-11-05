import os

from webhook_alert_gapo import create_app, initialize_app

# Create the Flask app for Gunicorn
application = create_app()

# Optionally initialize workers
try:
    initialize_app()
except Exception:
    pass