"""Initial shema

Revision ID: 4daf2223518c
Revises:
Create Date: 2025-06-18 01:46:10.545270
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql  # <<< add this

# revision identifiers, used by Alembic.
revision = '4daf2223518c'
down_revision = None
branch_labels = None
depends_on = None

# define enum ONCE; do not let columns auto-create it
SERVICE_TICKET_STATUS_VALUES = ('open', 'in_progress', 'closed')
service_ticket_status_enum = psql.ENUM(
    *SERVICE_TICKET_STATUS_VALUES,
    name='service_ticket_status',
    create_type=False  # <<< critical
)

def upgrade():
    bind = op.get_bind()

    # create the type if it doesn't already exist (safe on reruns)
    op.execute(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'service_ticket_status') THEN "
        "CREATE TYPE service_ticket_status AS ENUM ('open','in_progress','closed'); "
        "END IF; "
        "END $$;"
    )

    op.create_table(
        'customer',
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=False),
        sa.Column('last_name', sa.String(length=50), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('address', sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint('customer_id')
    )

    op.create_table(
        'mechanic',
        sa.Column('mechanic_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('address', sa.String(length=200), nullable=True),
        sa.Column('salary', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.PrimaryKeyConstraint('mechanic_id')
    )

    op.create_table(
        'vehicle',
        sa.Column('vin', sa.String(length=17), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('make', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=50), nullable=True),
        sa.Column('year', sa.SmallInteger(), nullable=True),
        sa.Column('license_plate', sa.String(length=15), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customer.customer_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('vin')
    )

    op.create_table(
        'service_ticket',
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('vin', sa.String(length=17), nullable=False),
        sa.Column('date_in', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('date_out', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        # use the SAME enum object with create_type=False so no auto CREATE TYPE
        sa.Column('status', service_ticket_status_enum, nullable=False),
        sa.Column('total_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['vin'], ['vehicle.vin'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('ticket_id')
    )

    op.create_table(
        'service_assignment',
        sa.Column('service_ticket_id', sa.Integer(), nullable=False),
        sa.Column('mechanic_id', sa.Integer(), nullable=False),
        sa.Column('hours_worked', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['mechanic_id'], ['mechanic.mechanic_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_ticket_id'], ['service_ticket.ticket_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('service_ticket_id', 'mechanic_id')
    )

def downgrade():
    op.drop_table('service_assignment')
    op.drop_table('service_ticket')
    op.drop_table('vehicle')
    op.drop_table('mechanic')
    op.drop_table('customer')

    # drop type only if present
    op.execute("DROP TYPE IF EXISTS service_ticket_status")
