# app/__init__.py
from __future__ import annotations

import importlib
import os

from flask import Flask, jsonify, Response
from flask_cors import CORS
from .extensions import db, migrate, ma


def _load_config(app: Flask) -> None:
    """
    Load a config class via APP_CONFIG env var.
    Defaults to ProductionConfig so Render keeps using Postgres there.
    Examples:
      APP_CONFIG=app.config.ProductionConfig
      APP_CONFIG=app.config.TestingConfig
      APP_CONFIG=app.config.DevelopmentConfig
    """
    cfg_path = os.getenv("APP_CONFIG", "app.config.ProductionConfig")
    module, _, cls = cfg_path.rpartition(".")
    if not module or not cls:
        raise RuntimeError(f"Invalid APP_CONFIG value: {cfg_path}")
    mod = importlib.import_module(module)
    app.config.from_object(getattr(mod, cls))


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    # --- Config ---
    _load_config(app)
    if overrides:
        app.config.update(overrides)

    # Ensure a SECRET_KEY exists (Testing/Dev/Prod should set it; keep fallback)
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret"))

    # --- Extensions ---
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    # import models so SQLAlchemy sees them
    from app import models  # noqa: F401

    # --- Auto-migrate in non-testing (safe/optional) ---
    if not app.config.get("TESTING") and app.config.get("AUTO_MIGRATE", True):
        try:
            from flask_migrate import upgrade
            with app.app_context():
                upgrade()
        except Exception as e:
            app.logger.error("Auto-migrate outer error (ignored): %s", e)

    # --- Swagger UI (/docs) ---
    try:
        from flask_swagger_ui import get_swaggerui_blueprint

        SWAGGER_URL = "/docs"
        API_URL = "/swagger.json"
        swaggerui_bp = get_swaggerui_blueprint(
            SWAGGER_URL,
            API_URL,
            config={"app_name": "Mechanic Shop API"},
        )
        app.register_blueprint(swaggerui_bp, url_prefix=SWAGGER_URL)

        from app.swagger import swagger_spec  # your static swagger dict

        @app.route("/swagger.json")
        def swagger_json():
            return jsonify(swagger_spec)

    except Exception as e:
        app.logger.warning("Swagger UI not configured: %s", e)

    # --- Blueprints ---
    # Auth: register WITHOUT prefix so /login exists for tests
    try:
        from .blueprints.auth.routes import auth_bp
        app.register_blueprint(auth_bp)  # exposes POST /login

        # Also provide /auth/login as an alias without double-registering the blueprint
        @app.route("/auth/login", methods=["POST"])
        def _login_alias():
            return app.view_functions["auth.login"]()
    except Exception as e:
        app.logger.info("auth_bp not registered: %s", e)

    try:
        from .blueprints.customers.routes import customers_bp
        app.register_blueprint(customers_bp, url_prefix="/customers")
    except Exception as e:
        app.logger.warning("customers_bp not registered: %s", e)

    try:
        from .blueprints.inventory.routes import inventory_bp
        app.register_blueprint(inventory_bp, url_prefix="/inventory")
    except Exception as e:
        app.logger.warning("inventory_bp not registered: %s", e)

    try:
        from .blueprints.mechanics.routes import mechanics_bp
        app.register_blueprint(mechanics_bp, url_prefix="/mechanics")
    except Exception as e:
        app.logger.warning("mechanics_bp not registered: %s", e)

    try:
        from .blueprints.service_tickets.routes import tickets_bp
        app.register_blueprint(tickets_bp, url_prefix="/service_tickets")
    except Exception as e:
        app.logger.warning("tickets_bp not registered: %s", e)

    try:
        from .blueprints.vehicles.routes import vehicles_bp
        app.register_blueprint(vehicles_bp, url_prefix="/vehicles")
    except Exception as e:
        app.logger.warning("vehicles_bp not registered: %s", e)

    # Optional extras
    try:
        from .blueprints.customers.ticket_routes import customer_ticket_bp
        app.register_blueprint(customer_ticket_bp, url_prefix="/customer")
    except Exception as e:
        app.logger.info("customer_ticket_bp not registered: %s", e)

    try:
        from .blueprints.mechanics.mechanic_ticket_routes import mechanic_ticket_bp
        app.register_blueprint(mechanic_ticket_bp, url_prefix="/mechanic")
    except Exception as e:
        app.logger.info("mechanic_ticket_bp not registered: %s", e)

    # --- Errors (match tests’ expectations) ---
    @app.errorhandler(404)
    def handle_404(e):
        html = (
            "<!doctype html>"
            "<html lang='en'>"
            "<head><meta charset='utf-8'><title>Not Found</title></head>"
            "<body><h1>Not Found</h1><p>The requested URL was not found on the server.</p></body>"
            "</html>"
        )
        return Response(html, status=404, headers={"Content-Type": "text/html"})

    @app.errorhandler(405)
    def handle_405(e):
        return Response("Method Not Allowed", status=405, headers={"Content-Type": "text/html"})

       # --- Testing DB bootstrap (SQLite) ---
    if app.config.get("TESTING"):
        with app.app_context():
            db.create_all()

            # Seed a known test customer used by unit tests
            try:
                from app.models import Customer  # adjust import if your model path differs
            except Exception as e:
                app.logger.warning("Could not import Customer for test seed: %s", e)
                Customer = None

            if Customer is not None:
                try:
                    # Only create if missing (tests may create/destroy their own data too)
                    test_email = "sam@example.com"
                    existing = Customer.query.filter_by(email=test_email).first()
                    if not existing:
                        c = Customer(
                            first_name="Sam",
                            last_name="Example",
                            phone="555-1111",
                            email=test_email,
                            address="",
                        )

                        # Set password in whichever way your model supports
                        if hasattr(c, "set_password"):
                            c.set_password("password")  # <- tests will log in with this
                        else:
                            from werkzeug.security import generate_password_hash
                            # fall back to direct field if your model uses `password_hash`
                            if hasattr(c, "password_hash"):
                                c.password_hash = generate_password_hash("password")
                            else:
                                # As a last resort, store on a generic `password` field if it exists
                                if hasattr(c, "password"):
                                    c.password = generate_password_hash("password")

                        db.session.add(c)
                        db.session.commit()
                        app.logger.info("Seeded test customer %s", test_email)
                    else:
                        app.logger.info("Test customer %s already present; seed skipped", test_email)

                except Exception as e:
                    # Do not hard-fail tests on seed; log with full context to help debugging
                    app.logger.warning("Test seed skipped due to error: %s", e)

    from flask import redirect

    @app.route("/healthz")
    def healthz():
        try:
            db.session.execute(db.text("SELECT 1"))
            return jsonify({"status": "ok", "db": "up"}), 200
        except Exception:
            return jsonify({"status": "degraded", "db": "down"}), 500

    @app.route("/", methods=["GET", "HEAD"])
    def root():
        return redirect("/docs", code =302)

    return app
