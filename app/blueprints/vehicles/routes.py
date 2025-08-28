from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Vehicle, Customer
from .schemas import VehicleSchema

vehicles_bp = Blueprint("vehicles", __name__)

vehicle_schema = VehicleSchema()
vehicle_list_schema = VehicleSchema(many=True)

# Create a new vehicle
@vehicles_bp.route("/vehicles", methods=["POST"])
def create_vehicle():
    data = request.get_json()

    # Validate customer exists
    customer = Customer.query.get(data.get("customer_id"))
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    try:
        vehicle = vehicle_schema.load(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    db.session.add(vehicle)
    db.session.commit()
    return vehicle_schema.jsonify(vehicle), 201

# Get all vehicles
@vehicles_bp.route("/vehicles", methods=["GET"])
def get_vehicles():
    vehicles = Vehicle.query.all()
    return vehicle_list_schema.jsonify(vehicles), 200

# Get a vehicle by VIN
@vehicles_bp.route("/vehicles/<string:vin>", methods=["GET"])
def get_vehicle(vin):
    vehicle = Vehicle.query.get_or_404(vin)
    return vehicle_schema.jsonify(vehicle), 200

# Update a vehicle
@vehicles_bp.route("/vehicles/<string:vin>", methods=["PUT"])
def update_vehicle(vin):
    vehicle = Vehicle.query.get_or_404(vin)
    data = request.get_json()

    try:
        updated = vehicle_schema.load(data, instance=vehicle, partial=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    db.session.commit()
    return vehicle_schema.jsonify(updated), 200

# Delete a vehicle
@vehicles_bp.route("/vehicles/<string:vin>", methods=["DELETE"])
def delete_vehicle(vin):
    vehicle = Vehicle.query.get_or_404(vin)
    db.session.delete(vehicle)
    db.session.commit()
    return jsonify({"message": "Vehicle deleted"}), 204

# Get all vehicles for a specific customer
@vehicles_bp.route("/customers/<int:customer_id>/vehicles", methods=["GET"])
def get_customer_vehicles(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return vehicle_list_schema.jsonify(customer.vehicles), 200
