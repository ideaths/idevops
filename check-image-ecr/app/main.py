import os

from dotenv import load_dotenv
import structlog

from src.logging_setup import setup_logging
from src.scheduler import setup_scheduler, run_once
from src.health import create_app


def main():
    load_dotenv()
    logger = setup_logging()

    # Decide run mode
    mode = os.getenv("RUN_MODE", "scheduled")
    logger.info("app_start", mode=mode)

    if mode == "once":
        run_once(os.getenv("CONFIG_PATH", "/app/config.txt"))
    else:
        setup_scheduler()
        app = create_app()
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))


if __name__ == "__main__":
    main()