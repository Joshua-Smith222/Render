from marshmallow import fields, EXCLUDE
from ...extensions import ma
from ...models import Mechanic

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    # Ensure API returns an `id` the tests can read
    id = fields.Int(attribute="mechanic_id", dump_only=True)

    # Accept this from the test payload (optional if your model doesn't require it)
    specialty = fields.Str(required=False)

    class Meta:
        model = Mechanic
        load_instance = True
        include_fk = True
        load_only = ("assignments",)
        unknown = EXCLUDE  # don't 400 on harmless extras like specialty if the model lacks it
