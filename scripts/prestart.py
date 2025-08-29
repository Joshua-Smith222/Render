# scripts/prestart.py
import sys
from sqlalchemy import text
from app import create_app
from app.extensions import db

def main():
    app = create_app()
    with app.app_context():
        try:
            # This removes the stale Alembic pointer (e.g., 5e3804aff328)
            db.session.execute(text("DROP TABLE IF EXISTS alembic_version"))
            db.session.commit()
            print("Prestart: dropped alembic_version")
        except Exception as e:
            print(f"Prestart: could not drop alembic_version: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
