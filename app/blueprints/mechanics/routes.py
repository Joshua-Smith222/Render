from flask import Blueprint, request, jsonify
from ...extensions import db
from ...models import Mechanic, ServiceAssignment
from .schemas import MechanicSchema
from marshmallow import Schema, fields
from werkzeug.security import check_password_hash
from app.utils.token import encode_token

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

# simple login schema
class MechanicLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

login_schema = MechanicLoginSchema()

@mechanics_bp.post("/login")
def mechanic_login():
    data = request.get_json() or {}
    errors = login_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 400

    mech = Mechanic.query.filter_by(email=data["email"]).first()
    if not mech:
        return jsonify({"error": "Invalid credentials"}), 401

    ok = mech.check_password(data["password"]) if hasattr(mech, "check_password") \
         else check_password_hash(mech.password_hash, data["password"])
    if not ok:
        return jsonify({"error": "Invalid credentials"}), 401

    identity = getattr(mech, "mechanic_id", None) or getattr(mech, "id")
    return jsonify({"token": encode_token(identity)}), 200
