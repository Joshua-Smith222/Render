from flask import Blueprint

inventory_bp = Blueprint("inventory", __name__)

from . import routes  # ensure routes are loaded
from . import schemas  # ensure schemas are loaded
