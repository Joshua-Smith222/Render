# app/__init__.py
import os
import logging
from flask import Flask, jsonify, request, redirect
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from sqlalchemy import text, inspect
from flask_migrate import upgrade as fm_upgrade, stamp as fm_stamp


from .extensions import db, migrate, ma

# Alembic (programmatic API, avoids sys.exit)
from alembic import command as alembic_cmd
from alembic.config import Config as AlembicConfig
from alembic.util.exc import CommandError


def _alembic_upgrade_head_safely() -> bool:
    """Run Alembic upgrade to head using the programmatic API."""
    # migrations dir is a sibling of app/
    try:
        fm_upgrade()
        return True
    except CommandError as ce:
        current_app.logger.warning("Alembic CommandError: %s", ce)
        return False
    except BaseException as be:
        current_app.logger.error("Alembic unexpected error: %s", be)
        return False

def _auto_migrate(app: Flask) -> None:
    """
    On Postgres only:
    - Take an advisory lock so only one worker migrates
    - Try upgrade -> if 'Can't locate revision' occurs, drop alembic_version and retry
    - Never crash the process; only log errors
    """
    if os.getenv("AUTO_MIGRATE", "1") != "1":
        app.logger.info("AUTO_MIGRATE=0; skipping auto-migrate.")
        return

    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not uri.startswith("postgresql"):
            app.logger.info("Auto-migrate skipped (non-Postgres URI).")
            return
    try:
            engine = db.engine
            insp = inspect(engine)
            with engine.begin() as conn:
                try:
            # single-run guard
                 conn.execute(text("SELECT pg_advisory_lock(91199001)"))
                except Exception:
                    app.logger.info("Advisory lock not available; skipping auto-migrate.")


                try:
                    app.logger.info("Running Alembic upgrade (programmatic)...")
                    if not _alembic_upgrade_head_safely():
                        app.logger.warning("Resseting alembic_version and retrying upgrade...")
                        try:
                            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))

                        except Exception as e:
                            app.logger.warning("Could not drop alembic_version: %s", e)
                        _alembic_upgrade_head_safely()
                    if not insp.has_table("customer"):
                        app.logger.info("No core tables found. Bootstrapping schema via create_all().")
                        try:
                            db.create_all()
                        except Exception as e:
                            app.logger.error("create_all() failed: %s", e)
                        try:
                            fm_stamp()
                            app.logger.info("Stamped alembic head after create_all().")
                        except BaseException as e:
                            app.logger.warning("Could not stamp alembic head after create_all(): %s", e)

    finally:
            try:
                conn.execute(text("SELECT pg_advisory_unlock(91199001)"))
            except Exception:
                pass
            except BaseException as e:
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

    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        expose_headers=["Location"],
        supports_credentials=False,
    )

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

    # --- init extensions ---
    db.init_app(app)
    from app import models  # noqa: F401
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

    # --- Auto-migrate on startup (Postgres only, non-fatal) ---
    try:
        _auto_migrate(app)
    except Exception as e:
        app.logger.error("Auto-migrate failed at startup (ignored): %s", e)

    return app
