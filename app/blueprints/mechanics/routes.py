from flask import Blueprint, request, jsonify
from ...extensions import db
from ...models import Mechanic, ServiceAssignment
from .schemas import MechanicSchema

mechanics_bp = Blueprint('mechanics', __name__)
mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)

@mechanics_bp.route('/', methods=['POST'])
def create_mechanic():
    data = request.get_json(force=True)
    m = mechanic_schema.load(data, session=db.session)
    # hash password if provided
    pw = data.get("password")
    if pw:
        m.set_password(pw)
    db.session.add(m)
    db.session.commit()
    return mechanic_schema.jsonify(m), 201

@mechanics_bp.route('/', methods=['GET'])
def list_mechanics():
    allm = Mechanic.query.all()
    return mechanics_schema.jsonify(allm), 200

@mechanics_bp.route('/<int:id>', methods=['PUT'])
def update_mechanic(id):
    data = request.get_json(force=True)
    m = Mechanic.query.get_or_404(id)
    # handle password first
    pw = data.get("password")
    if pw:
        m.set_password(pw)
    # partial update to avoid required-field issues
    m = mechanic_schema.load(data, instance=m, session=db.session, partial=True)
    db.session.commit()
    return mechanic_schema.jsonify(m), 200

@mechanics_bp.route('/<int:id>', methods=['DELETE'])
def delete_mechanic(id):
    m = Mechanic.query.get_or_404(id)
    db.session.delete(m)
    db.session.commit()
    return '', 204

@mechanics_bp.route('/<int:id>', methods=['GET'])
def get_mechanic(id):
    m = Mechanic.query.get_or_404(id)
    return mechanic_schema.jsonify(m), 200

@mechanics_bp.route('/ranked', methods=['GET'])
def get_ranked_mechanics():
    ranked = (
        db.session.query(Mechanic, db.func.count(ServiceAssignment.mechanic_id).label('assignment_count'))
        .outerjoin(ServiceAssignment, Mechanic.mechanic_id == ServiceAssignment.mechanic_id)
        .group_by(Mechanic.mechanic_id)
        .order_by(db.desc('assignment_count'))
        .all()
    )
    result = [{
        "mechanic": mechanic_schema.dump(mech),
        "assignment_count": int(count or 0)
    } for mech, count in ranked]
    return jsonify(result), 200
