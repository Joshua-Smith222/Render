from flask import Blueprint, jsonify
from ...extensions import db
from ...models import ServiceTicket, Vehicle
from app.utils.token import token_required
from app.blueprints.service_tickets.schemas import ServiceTicketSchema

customer_ticket_bp = Blueprint('customer_tickets', __name__)
tickets_schema = ServiceTicketSchema(many=True)

@customer_ticket_bp.route('/my-tickets', methods=['GET'])
@token_required
def get_my_tickets(customer_id):
    vehicles = Vehicle.query.filter_by(customer_id=customer_id).all()
    vins = [v.vin for v in vehicles]

    tickets = ServiceTicket.query.filter(ServiceTicket.vin.in_(vins)).all()
    return tickets_schema.jsonify(tickets), 200
