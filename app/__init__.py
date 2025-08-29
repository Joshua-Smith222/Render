# app/__init__.py
import os
from flask import Flask, jsonify, request, redirect
from flask_swagger_ui import get_swaggerui_blueprint
from sqlalchemy import text

from .extensions import db, migrate, ma
from flask_cors import CORS

# Only import here to avoid circulars at module import time
from flask_migrate import upgrade as alembic_upgrade


def _auto_migrate(app: Flask) -> None:
    """
    Run Alembic upgrade at startup. If the database points at a missing
    revision (e.g., stale alembic_version), drop that table and retry.
    Uses a Postgres advisory lock so only one worker performs the work.
    Skips entirely for SQLite/dev/test.
    """
    with app.app_context():
        uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        # Only do this on Postgres; SQLite and tests don't need it and may break.
        if not uri.startswith("postgresql"):
            app.logger.info("Auto-migrate skipped (non-Postgres URI).")
            return

        engine = db.engine

        def do_upgrade():
            alembic_upgrade()  # to head

        # Single-run guard so only one Gunicorn worker migrates
        with engine.begin() as conn:
            conn.execute(text("SELECT pg_advisory_lock(91199001)"))
            try:
                try:
                    app.logger.info("Running Alembic upgrade...")
                    do_upgrade()
                    app.logger.info("Alembic upgrade complete.")
                except Exception as err:
                    app.logger.warning(
                        "Alembic upgrade failed (%s). Dropping alembic_version and retrying...",
                        err,
                    )
                    conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
                    do_upgrade()
                    app.logger.info("Alembic upgrade succeeded after resetting alembic_version.")
            finally:
                conn.execute(text("SELECT pg_advisory_unlock(91199001)"))


def create_app(config_object=None):
    """
    config_object can be:
      - a dict (tests pass overrides like TESTING + SQLite URI)
      - a string import path, e.g. "app.config.DevelopmentConfig"
      - a config class
    If nothing provided, we try APP_CONFIG env var, else default to DevelopmentConfig.
    """
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        expose_headers=["Location"],
        supports_credentials=False,
    )

    cfg = config_object or os.getenv("APP_CONFIG") or "app.config.DevelopmentConfig"

    if isinstance(cfg, dict):
        # Minimal safe defaults, then apply test overrides
        app.config.update(
            {
                "SECRET_KEY": os.getenv("SECRET_KEY", "fallback_dev_secret"),
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            }
        )
        app.config.update(cfg)
    elif isinstance(cfg, str):
        app.config.from_object(cfg)
    else:
        app.config.from_object(cfg)

    # Final fallbacks & JWT settings
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "fallback_dev_secret"))
    app.config.setdefault("JWT_SECRET", app.config["SECRET_KEY"])
    app.config.setdefault("JWT_ALGO", "HS256")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # --- init extensions ---
    db.init_app(app)
    from app import models  # noqa: F401 (register models with SQLAlchemy)
    migrate.init_app(app, db)
    ma.init_app(app)

    # --- Swagger UI ---
    SWAGGER_URL = "/docs"
    API_URL = "/swagger.json"
    swaggerui_bp = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={"app_name": "Mechanic Shop API"},
    )
    app.register_blueprint(swaggerui_bp, url_prefix=SWAGGER_URL)

    # swagger.json endpoint (dynamic host/scheme so it works locally and behind proxies)
    from app.swagger import swagger_spec

    @app.route("/swagger.json")
    def swagger_json():
        spec = dict(swagger_spec)  # copy
        spec["host"] = request.headers.get("X-Forwarded-Host", request.host)
        spec["schemes"] = [request.headers.get("X-Forwarded-Proto", "http")]
        return jsonify(spec)

    # Simple healthcheck + root redirect to docs
    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/")
    def index():
        return redirect("/docs", code=302)

    # --- Blueprints ---
    from .blueprints.customers.routes import customers_bp
    from .blueprints.Inventory.routes import inventory_bp
    from .blueprints.mechanics.routes import mechanics_bp
    from .blueprints.service_tickets.routes import tickets_bp
    from .blueprints.vehicles.routes import vehicles_bp
    from .blueprints.customers.ticket_routes import customer_ticket_bp
    from .blueprints.mechanics.mechanic_ticket_routes import mechanic_ticket_bp
    from .blueprints.auth.routes import auth_bp

    app.register_blueprint(customers_bp,       url_prefix="/customers")
    app.register_blueprint(inventory_bp,       url_prefix="/inventory")
    app.register_blueprint(mechanics_bp,       url_prefix="/mechanics")
    app.register_blueprint(tickets_bp,         url_prefix="/service_tickets")
    app.register_blueprint(vehicles_bp,        url_prefix="/vehicles")
    app.register_blueprint(customer_ticket_bp, url_prefix="/customer")
    app.register_blueprint(mechanic_ticket_bp, url_prefix="/mechanic")
    app.register_blueprint(auth_bp)

    # --- Auto-migrate on startup (Postgres only) ---
    # Keep your Render Start Command SIMPLE:
    #   gunicorn "app:create_app()" --bind 0.0.0.0:$PORT
    # This function will handle the migration safely.
    try:
        _auto_migrate(app)
    except Exception as e:
        # If something goes wrong, log but don't prevent the app from starting.
        app.logger.error("Auto-migrate failed at startup: %s", e)

    return app
