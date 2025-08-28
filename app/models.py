from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class Customer(db.Model):
    __tablename__ = 'customer'
    customer_id = db.Column(db.Integer, primary_key=True)
    first_name  = db.Column(db.String(100), nullable=False)
    last_name   = db.Column(db.String(100), nullable=False)
    phone       = db.Column(db.String(20))
    email       = db.Column(db.String(120), unique=True, nullable=False)
    address     = db.Column(db.String(200))
    password_hash = db.Column(db.String(512), nullable=False)

    # 1→M: customer → vehicles
    vehicles = db.relationship(
        'Vehicle', back_populates='owner', cascade='all, delete-orphan'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Vehicle(db.Model):
    __tablename__ = 'vehicle'
    vin           = db.Column(db.String(17), primary_key=True)
    customer_id   = db.Column(
        db.Integer,
        db.ForeignKey('customer.customer_id', ondelete='CASCADE'),
        nullable=False
    )
    make          = db.Column(db.String(50))
    model         = db.Column(db.String(50))
    year          = db.Column(db.SmallInteger)
    license_plate = db.Column(db.String(15))

    owner   = db.relationship('Customer', back_populates='vehicles')
    tickets = db.relationship(
        'ServiceTicket', back_populates='vehicle', cascade='all, delete-orphan'
    )

class Mechanic(db.Model):
    __tablename__ = 'mechanic'
    mechanic_id = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(100))
    phone       = db.Column(db.String(20))
    address     = db.Column(db.String(200))
    salary      = db.Column(db.Numeric(10,2))

    # M↔M via ServiceAssignment
    assignments = db.relationship(
        'ServiceAssignment', back_populates='mechanic', cascade='all, delete-orphan'
    )

class ServiceTicket(db.Model):
    __tablename__ = 'service_ticket'
    ticket_id   = db.Column(db.Integer, primary_key=True)
    vin         = db.Column(
        db.String(17),
        db.ForeignKey('vehicle.vin', ondelete='CASCADE'),
        nullable=False
    )
    date_in     = db.Column(db.DateTime, server_default=db.func.now())
    date_out    = db.Column(db.DateTime)
    description = db.Column(db.Text)
    status      = db.Column(
        db.Enum('open','in_progress','closed'),
        default='open',
        nullable=False
    )
    total_cost  = db.Column(db.Numeric(10,2), default=0.00)

    vehicle     = db.relationship('Vehicle', back_populates='tickets')
    assignments = db.relationship(
        'ServiceAssignment', back_populates='ticket', cascade='all, delete-orphan'
    )
    parts = db.relationship(
        "Inventory",
        secondary='ticket_inventory',
        back_populates='service_tickets'
    )
class ServiceAssignment(db.Model):
    __tablename__ = 'service_assignment'
    service_ticket_id = db.Column(
        db.Integer,
        db.ForeignKey('service_ticket.ticket_id', ondelete='CASCADE'),
        primary_key=True
    )
    mechanic_id       = db.Column(
        db.Integer,
        db.ForeignKey('mechanic.mechanic_id', ondelete='CASCADE'),
        primary_key=True
    )
    hours_worked      = db.Column(db.Numeric(5,2), default=0.00)

    ticket   = db.relationship('ServiceTicket', back_populates='assignments')
    mechanic = db.relationship('Mechanic',      back_populates='assignments')


# Junction table (simple version)
ticket_inventory = db.Table(
    'ticket_inventory',
    db.Column('ticket_id', db.Integer, db.ForeignKey('service_ticket.ticket_id'), primary_key=True),
    db.Column('inventory_id', db.Integer, db.ForeignKey('inventory.id'), primary_key=True)
)


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)

    # Relationship to ServiceTickets
    service_tickets = db.relationship(
        'ServiceTicket',
        secondary=ticket_inventory,
        back_populates='parts'
    )

# Add this to ServiceTicket model:
