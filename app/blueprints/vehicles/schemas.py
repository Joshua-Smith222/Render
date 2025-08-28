from app.extensions import ma
from app.models import Vehicle

class VehicleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Vehicle
        load_instance = True
        include_fk = True

    vin = ma.Str(required=True)
    customer_id = ma.Int(required=True)
    make = ma.Str()
    model = ma.Str()
    year = ma.Int()
    license_plate = ma.Str()
