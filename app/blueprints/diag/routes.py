# app/blueprints/diag/routes.py
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text, inspect
from app.extensions import db

diag_bp = Blueprint("diag", __name__)

def _safe_uri(uri: str) -> str:
    # hide password in DSN for display
    if not uri:
        return ""
    try:
        from urllib.parse import urlsplit, urlunsplit
        parts = urlsplit(uri)
        if parts.username or parts.password:
            netloc = parts.hostname or ""
            if parts.port:
                netloc += f":{parts.port}"
            user = parts.username or ""
            if user:
                netloc = f"{user}:***@" + netloc
            return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        pass
    return uri

@diag_bp.get("/__diag")
def diag():
    out = {"ok": True, "errors": []}
    cfg_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI") or ""
    out["config_uri"] = _safe_uri(cfg_uri)

    try:
        eng = db.engine
        out["dialect"] = eng.dialect.name
        out["driver"] = getattr(eng.dialect, "driver", "")
    except Exception as e:
        out["ok"] = False
        out["errors"].append(f"engine: {e!r}")

    try:
        with db.engine.connect() as conn:
            out["select_1"] = conn.execute(text("SELECT 1")).scalar()
            try:
                out["db_version"] = conn.execute(text("SELECT version()")).scalar()
            except Exception:
                pass
            try:
                out["alembic_version"] = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            except Exception as e:
                out["alembic_version"] = None
                out["errors"].append(f"alembic_version: {e!r}")
    except Exception as e:
        out["ok"] = False
        out["errors"].append(f"connect: {e!r}")

    try:
        insp = inspect(db.engine)
        out["tables"] = insp.get_table_names()
    except Exception as e:
        out["tables"] = []
        out["errors"].append(f"inspect: {e!r}")

    return jsonify(out), 200 if out["ok"] else 500
