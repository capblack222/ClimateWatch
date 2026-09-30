from dotenv import load_dotenv

# Load .env before importing the app, since modules read environment variables at import time.
load_dotenv()

from app import create_app  # noqa: E402
from app.database.db import init_db  # noqa: E402
from app.database.seed import load_owid_csv  # noqa: E402

app = create_app()

if __name__ == "__main__":
    init_db()
    load_owid_csv()
    app.run(debug=app.config["DEBUG"])
