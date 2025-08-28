# app/blueprints/customers/routes.py
from flask import Blueprint, request, jsonify
from app.extensions import db, limiter
from app.models import Customer
from .schemas import CustomerSchema

customers_bp = Blueprint("customers", __name__)

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

# GET /customers/  -> tests expect a plain list
@customers_bp.get("/")
@limiter.limit("100 per hour")
def list_customers():
    customers = Customer.query.all()
    return jsonify(customers_schema.dump(customers)), 200

# POST /customers/ -> create and return the created customer as JSON
@customers_bp.post("/")
@limiter.limit("10 per minute")
def create_customer():
    data = request.get_json() or {}
    # load via marshmallow (will validate)
    customer = customer_schema.load(data, session=db.session)
    # set password if provided
    if "password" in data and data["password"]:
        customer.set_password(data["password"])
    db.session.add(customer)
    db.session.commit()
    return jsonify(customer_schema.dump(customer)), 201

# GET /customers/<id>
@customers_bp.get("/<int:customer_id>")
def get_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return jsonify(customer_schema.dump(customer)), 200

# PUT /customers/<id>  -> tests send invalid email to trigger 400/422
@customers_bp.put("/<int:customer_id>")
def update_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    data = request.get_json() or {}
    try:
        updated = customer_schema.load(data, instance=customer, partial=True, session=db.session)
    except Exception as e:
        # bad email, etc.
        return jsonify({"error": str(e)}), 400
    db.session.commit()
    return jsonify(customer_schema.dump(updated)), 200

# DELETE /customers/<id>
@customers_bp.delete("/<int:customer_id>")
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    return "", 204
