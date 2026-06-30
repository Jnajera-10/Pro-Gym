from database.db import db
from datetime import datetime
import pytz

BOGOTA = pytz.timezone('America/Bogota')

SHIFT_MORNING   = 'mañana'
SHIFT_AFTERNOON = 'tarde'

def _get_shift():
    hour = datetime.now(BOGOTA).hour
    return SHIFT_MORNING if hour < 13 else SHIFT_AFTERNOON


class Payment(db.Model):
    __tablename__ = 'payments'
    id               = db.Column(db.Integer, primary_key=True)
    client_id        = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    membership_id    = db.Column(db.Integer, db.ForeignKey('memberships.id'), nullable=False)
    amount           = db.Column(db.Float, nullable=False)
    payment_date     = db.Column(db.Date, default=lambda: datetime.now(BOGOTA).date())
    start_date       = db.Column(db.Date, nullable=False)
    end_date         = db.Column(db.Date, nullable=False)
    payment_method   = db.Column(db.String(120), default='efectivo')
    notes            = db.Column(db.Text)
    is_deleted       = db.Column(db.Boolean, default=False)
    created_at       = db.Column(db.DateTime, default=lambda: datetime.now(BOGOTA))
    shift            = db.Column(db.String(10), default=_get_shift)
    cash_received    = db.Column(db.Float, nullable=True)
    cash_change      = db.Column(db.Float, nullable=True)
    partner_client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    payment_status   = db.Column(db.String(20), default='pagado', nullable=False)

    # ── Cantidad de personas para plan diario ─────────────────────
    daily_quantity   = db.Column(db.Integer, default=1, nullable=False)

    membership = db.relationship('Membership', backref='payments')
    partner    = db.relationship('Client', foreign_keys=[partner_client_id], backref='partner_payments')
    items      = db.relationship('PaymentItem', backref='payment', lazy=True)


class PaymentItem(db.Model):
    """Productos del inventario comprados junto con una membresía."""
    __tablename__ = 'payment_items'
    id         = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal   = db.Column(db.Float, nullable=False)
    product    = db.relationship('Product', backref='payment_items', lazy=True)
