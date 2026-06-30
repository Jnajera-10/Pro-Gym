from database.db import db
from datetime import datetime
import pytz

BOGOTA = pytz.timezone('America/Bogota')


class Expense(db.Model):
    """Egreso registrado manualmente por un administrador."""
    __tablename__ = 'expenses'

    id          = db.Column(db.Integer, primary_key=True)
    date        = db.Column(db.Date, nullable=False,
                            default=lambda: datetime.now(BOGOTA).date())
    amount      = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    category    = db.Column(db.String(80), nullable=True)   # ej. "servicios", "equipos", "otros"
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at  = db.Column(db.DateTime,
                            default=lambda: datetime.now(BOGOTA))

    user = db.relationship('User', backref='expenses')

    def __repr__(self):
        return f'<Expense {self.date} ${self.amount} — {self.description[:30]}>'
