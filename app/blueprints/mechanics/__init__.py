# app/blueprints/mechanics/__init__.py
from flask import Blueprint

# Initialize the mechanics blueprint
mechanics_bp = Blueprint('mechanics', __name__)

# Import routes to register endpoint handlers
from .routes import *
from .schemas import *

