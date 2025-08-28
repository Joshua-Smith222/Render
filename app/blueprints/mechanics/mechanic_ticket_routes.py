from flask import Blueprint, jsonify
from ...extensions import db
from ...models import ServiceTicket, ServiceAssignment
from app.utils.token import token_required
from app.blueprints.service_tickets.schemas import ServiceTicketSchema

mechanic_ticket_bp = Blueprint('mechanic_tickets', __name__)
ticket_schema = ServiceTicketSchema()
tickets_schema = ServiceTicketSchema(many=True)

@mechanic_ticket_bp.route('/my-assigned-tickets', methods=['GET'])
@token_required
def get_my_assigned_tickets(mechanic_id):
    assignments = ServiceAssignment.query.filter_by(mechanic_id=mechanic_id).all()
    tickets = [assignment.ticket for assignment in assignments]
    return tickets_schema.jsonify(tickets), 200
