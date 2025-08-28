from marshmallow import EXCLUDE, fields
from ...extensions import ma
from ...models import ServiceTicket

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    id = fields.Method("dump_id", dump_only=True)  # Expose `id` even if model uses `ticket_id`")
    vin = fields.Str(required=False, allow_none=True, load_default=None)  # make optional if your model allows it

    def dump_id(self, obj):
        return getattr(obj, "ticket_id", None) or getattr(obj, "id", None)
    class Meta:
        model = ServiceTicket
        include_relationships = False  # 👈 Turn this OFF to stop auto-loading `vehicle`
        include_fk = True              # 👈 Required to allow `vin` input
        load_instance = True
        unknown = EXCLUDE           # 👈 Ignore unexpected keys instead of hard-failing

    # Optional: define vin explicitly if needed
    # vin = ma.Str(required=True)
