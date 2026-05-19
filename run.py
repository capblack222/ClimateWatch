from app import create_app
from app.database.db import init_db
from app.database.seed import load_owid_csv

app = create_app()

if __name__ == "__main__":
    init_db()
    load_owid_csv()
    app.run(debug=True)

