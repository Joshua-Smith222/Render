# app/blueprints/service_tickets/routes.py
from flask import Blueprint, request, jsonify
from ...extensions import db
from ...models import ServiceTicket, Mechanic, ServiceAssignment, Inventory, Vehicle
from .schemas import ServiceTicketSchema
from app.utils.token import token_required  # encode_token not needed here

tickets_bp     = Blueprint("service_tickets", __name__)
ticket_schema  = ServiceTicketSchema()
tickets_schema = ServiceTicketSchema(many=True)

# POST /service_tickets/  (auth required) -> 201
@tickets_bp.post("/")
@token_required
def create_ticket(current_customer_id):
    data = request.get_json() or {}
    data.setdefault("customer_id", current_customer_id)

    if not data.get("vin"):
        vin = None
        if data.get("vehicle_id"):
            v= Vehicle.query.get(data["vehicle_id"])
            vin = getattr(v, "vin", None) if v else None
        data["vin"] = vin or ("0" * 17)  # Default VIN if none provided
    t = ticket_schema.load(data, session=db.session)
    db.session.add(t)
    db.session.commit()
    return jsonify(ticket_schema.dump(t)), 201

# GET /service_tickets/ (auth required) -> 200
@tickets_bp.get("/")
@token_required
def list_tickets(_current_customer_id):
    allt = ServiceTicket.query.all()
    return jsonify(tickets_schema.dump(allt)), 200

# GET /service_tickets/<id> (auth required) -> 200
@tickets_bp.get("/<int:ticket_id>")
@token_required
def get_ticket(current_user, ticket_id):
    t = ServiceTicket.query.get_or_404(ticket_id)
    return jsonify(ticket_schema.dump(t)), 200

# PUT /service_tickets/<id> (auth required) -> 200
# Supports add/remove mechanic IDs in the same payload if your tests send them.
@tickets_bp.put("/<int:ticket_id>")
@token_required
def update_ticket(current_user, ticket_id):
    t = ServiceTicket.query.get_or_404(ticket_id)
    data = (request.get_json() or {}).copy()

    add_ids = data.pop("add_ids", [])
    remove_ids = data.pop("remove_ids", [])

    # Update core fields
    t = ticket_schema.load(data, instance=t, partial=True, session=db.session)

    # Maintain mechanic assignments
    for mid in add_ids:
        if not ServiceAssignment.query.get((ticket_id, mid)):
            db.session.add(
                ServiceAssignment(service_ticket_id=ticket_id, mechanic_id=mid, hours_worked=0.0)
            )
    for mid in remove_ids:
        existing = ServiceAssignment.query.get((ticket_id, mid))
        if existing:
            db.session.delete(existing)

    db.session.commit()
    return jsonify(ticket_schema.dump(t)), 200

# POST /service_tickets/<id>/assign (auth required) -> 200
# Tests send {"mechanic_ids": [], "inventory_ids": []}
@tickets_bp.post("/<int:ticket_id>/assign")
@token_required
def assign(current_user, ticket_id):
    t = ServiceTicket.query.get_or_404(ticket_id)
    data = request.get_json() or {}
    mech_ids = data.get("mechanic_ids", [])
    inv_ids  = data.get("inventory_ids", [])

    # Attach mechanics (via join table)
    for mid in mech_ids:
        if not ServiceAssignment.query.get((ticket_id, mid)):
            db.session.add(
                ServiceAssignment(service_ticket_id=ticket_id, mechanic_id=mid, hours_worked=0.0)
            )

    # Attach inventory parts (many-to-many)
    if hasattr(t, "parts"):
        for pid in inv_ids:
            part = Inventory.query.get(pid)
            if part and part not in t.parts:
                t.parts.append(part)

    db.session.commit()
    return jsonify(ticket_schema.dump(t)), 200

# DELETE /service_tickets/<id> (auth required) -> 204
@tickets_bp.delete("/<int:ticket_id>")
@token_required
def delete_ticket(current_user, ticket_id):
    t = ServiceTicket.query.get_or_404(ticket_id)
    db.session.delete(t)
    db.session.commit()
    return "", 204
