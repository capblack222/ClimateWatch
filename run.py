import logging

from dotenv import load_dotenv

# Load .env before importing the app, since Config reads environment variables at import time.
load_dotenv()

from app import create_app  # noqa: E402
from app.config import port_from_env  # noqa: E402
from app.database.db import init_db  # noqa: E402
from app.database.seed import load_owid_csv  # noqa: E402

app = create_app()

if __name__ == "__main__":
    port = port_from_env()  # fail on a bad PORT before the database setup and OWID download
    with app.app_context():
        init_db()
        load_owid_csv()
    logging.getLogger("app").info("Server starting", extra={"url": f"http://127.0.0.1:{port}"})
    app.run(port=port, debug=app.config["DEBUG"])
