# app/blueprints/service_tickets/__init__.py
from flask import Blueprint

tickets_bp = Blueprint('service_tickets', __name__)

from .routes import *
from .schemas import *
