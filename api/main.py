import logging
import sys
import traceback

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')

try:
    from app import app
    application = app  # make uwsgi happy
    logging.info("App initialized successfully")
except Exception:
    logging.critical("STARTUP FAILED:\n%s", traceback.format_exc())
    sys.exit(3)

if __name__ == "__main__":
    app.run()