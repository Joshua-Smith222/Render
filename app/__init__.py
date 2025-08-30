# app/__init__.py
import os
import logging

from flask import Flask, jsonify, request, redirect
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from sqlalchemy import text, inspect
from flask_migrate import upgrade as fm_upgrade, stamp as fm_stamp
from alembic.util.exc import CommandError

from .extensions import db, migrate, ma


def _alembic_upgrade_head_safely(app: Flask) -> bool:
    """
    Run Alembic upgrade to head using Flask-Migrate's programmatic API.
    Never raises; logs and returns True/False.
    NOTE: Caller must ensure an app context is active.
    """
    try:
        fm_upgrade()
        return True
    except CommandError as ce:
        app.logger.warning("Alembic CommandError during upgrade: %s", ce)
        return False
    except BaseException as be:
        app.logger.error("Alembic unexpected error during upgrade: %s", be)
        return False


def _auto_migrate(app: Flask) -> None:
    """
    On Postgres only:
    - Take an advisory lock so only one worker migrates
    - Try upgrade -> on failure, drop alembic_version and retry
    - If core tables are missing, create_all() then stamp head
    - Never crash the process; only log errors
    """
    if os.getenv("AUTO_MIGRATE", "1") != "1":
        app.logger.info("AUTO_MIGRATE=0; skipping auto-migrate.")
        return

    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "") or ""
    if not uri.startswith("postgresql"):
        app.logger.info("Auto-migrate skipped (non-Postgres URI).")
        return

    # All Flask-Migrate and db.* calls require an app context
    with app.app_context():
        try:
            engine = db.engine
            insp = inspect(engine)

            with engine.begin() as conn:
                # Acquire advisory lock (released when connection closes)
                try:
                    conn.execute(text("SELECT pg_advisory_lock(91199001)"))
                except Exception:
                    app.logger.info("Advisory lock not available; skipping auto-migrate.")
                    return

                try:
                    app.logger.info("Running Alembic upgrade (programmatic)...")
                    ok = _alembic_upgrade_head_safely(app)

                    # If upgrade failed, reset alembic_version and retry once
                    if not ok:
                        app.logger.warning("Resetting alembic_version and retrying upgrade...")
                        try:
                            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
                        except Exception as e:
                            app.logger.warning("Could not drop alembic_version: %s", e)
                        ok = _alembic_upgrade_head_safely(app)

                    # If there still aren’t any core tables, bootstrap schema
                    core_has_tables = any(
                        insp.has_table(t)
                        for t in ("customers", "mechanics", "service_tickets", "vehicles", "inventory")
                    )
                    if not core_has_tables:
                        app.logger.info("No core tables found. Bootstrapping schema via create_all().")
                        try:
                            db.create_all()
                        except Exception as e:
                            app.logger.error("create_all() failed: %s", e)

                        try:
                            fm_stamp(revision="head")
                            app.logger.info("Stamped alembic head after create_all().")
                        except BaseException as e:
                            app.logger.warning("Could not stamp alembic head after create_all(): %s", e)

                finally:
                    # Always release lock
                    try:
                        conn.execute(text("SELECT pg_advisory_unlock(91199001)"))
                    except Exception:
                        pass

        except Exception as e:
            app.logger.error("Auto-migrate outer error (ignored): %s", e)


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

    # ---- CORS (single init) ----
    supports_credentials = os.getenv("CORS_CREDENTIALS", "0") == "1"
    cors_env = os.getenv("CORS_ORIGINS", "*").strip()

    if supports_credentials:
        # With credentials, you must list explicit origins
        cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
    else:
        # No credentials: allow any origin using the "*" string, or a list if provided
        cors_origins = "*" if cors_env == "*" else [o.strip() for o in cors_env.split(",") if o.strip()]

    CORS(
        app,
        resources={
            r"/*": {
                "origins": cors_origins,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "expose_headers": ["Location", "Content-Range"],
            }
        },
        supports_credentials=supports_credentials,
    )

    @app.before_request
    def _allow_preflight():
        if request.method == "OPTIONS":
            return ("", 204)

    app.logger.info("CORS configured: origins=%s creds=%s", cors_origins, supports_credentials)

    # ---- Config ----
    cfg = config_object or os.getenv("APP_CONFIG") or "app.config.DevelopmentConfig"
    if isinstance(cfg, dict):
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

    # ---- Extensions ----
    db.init_app(app)
    from app import models  # noqa: F401 - ensure models are imported so Alembic sees them
    migrate.init_app(app, db)
    ma.init_app(app)

    # ---- Swagger UI ----
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

    # ---- Blueprints (folder names must match case on Linux) ----
    from .blueprints.customers.routes import customers_bp
    from .blueprints.inventory.routes import inventory_bp      # ensure folder is 'inventory'
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

    # ---- Auto-migrate (Postgres only, non-fatal) ----
    try:
        _auto_migrate(app)
    except Exception as e:
        app.logger.error("Auto-migrate failed at startup (ignored): %s", e)

    return app
