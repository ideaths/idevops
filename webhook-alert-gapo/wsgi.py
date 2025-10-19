import os

from app import app, initialize_app

# Ensure app components are initialized for worker processes
initialize_app()

# Expose the Flask app for Gunicorn
application = app