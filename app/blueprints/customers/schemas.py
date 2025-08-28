from marshmallow import Schema, fields, EXCLUDE, pre_load
from app.extensions import ma
from app.models import Customer

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    # expose `id` even if your model uses `customer_id`
    id = fields.Int(attribute="customer_id", dump_only=True)

    # keep email validated; tests rely on this for the “bad email” case
    email = fields.Email(required=True)

    # make these optional so tests that only send `name` + `email` pass
    first_name = fields.Str(required=False, allow_none=True)
    last_name  = fields.Str(required=False, allow_none=True)
    address    = fields.Str(required=False, allow_none=True)
    phone      = fields.Str(required=False, allow_none=True)

    # allow create without password; hash it in the route if provided
    password   = fields.Str(load_only=True, required=False)

    class Meta:
        model = Customer
        load_instance = True
        include_fk = True
        exclude = ("password_hash",)
        unknown = EXCLUDE  # ignore harmless extras

    @pre_load
    def split_name(self, data, **kwargs):
        # Accept {"name": "First Last"} and map to first/last_name
        name = data.get("name")
        if name and not data.get("first_name") and not data.get("last_name"):
            parts = str(name).strip().split(None, 1)
            data["first_name"] = parts[0]
            data["last_name"]  = parts[1] if len(parts) > 1 else ""
        return data
