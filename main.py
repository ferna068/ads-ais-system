from src.presentation.app import Application
import asyncio
import logging
import signal
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

application = Application()

def handler(num, frame):
    logger.info(f"Received signal {num}, stopping application")
    application.stop()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    try:
        asyncio.run(application.run())
    except KeyboardInterrupt:
        logger.info(f"Keyboard interrupt received, stopping application")
        application.stop()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in main: {e}")