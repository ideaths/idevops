"""
Thin wrapper to run the refactored app locally.
The original monolithic implementation has been split into OOP modules under `webhook_alert_gapo`.
"""

import os
from webhook_alert_gapo import create_app, initialize_app

app = create_app()

if __name__ == '__main__':
    initialize_app(app)
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'false').lower() == 'true',
        threaded=True,
    )