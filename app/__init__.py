# app/__init__.py
import os
from flask import Flask, jsonify, request, redirect
from flask_swagger_ui import get_swaggerui_blueprint

from .extensions import db, migrate, ma

def create_app(config_object=None):
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    # Allow: explicit class passed in, or APP_CONFIG="app.config.ProductionConfig",
    # or default to DevelopmentConfig.
    cfg = config_object or os.getenv("APP_CONFIG") or "app.config.DevelopmentConfig"
    if isinstance(cfg, str):
        app.config.from_object(cfg)
    else:
        app.config.from_object(cfg)

    # Final fallback to avoid KeyError locally
    app.config["SECRET_KEY"] = app.config.get("SECRET_KEY") or os.getenv("SECRET_KEY", "fallback_dev_secret")

    # --- init extensions ---
    db.init_app(app)
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

    # swagger.json endpoint
    from app.swagger import swagger_spec
    @app.route("/swagger.json")
    def swagger_json():
        spec = dict(swagger_spec)  # make a copy
        spec["host"] = request.headers.get("X-Forwarded-Host", request.host)
        spec["schemes"] = [request.headers.get("X-Forwarded-Proto", "https")]
        return jsonify(spec)

    # --- health check (handy for Render) ---
    @app.get("/health")
    def health():
        return jsonify(status= "ok")

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

    return app
