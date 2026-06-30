from database.models.client import Client
from database.models.payment import Payment
from database.models.sales import Sale
from database.models.attendance import Attendance
from database.models.inventory import Product
import pytz
from datetime import datetime

BOGOTA = pytz.timezone('America/Bogota')

class ReportService:
    @staticmethod
    def clients_report(active_only=True):
        q = Client.query
        if active_only:
            q = q.filter_by(is_active=True)
        return q.all()

    @staticmethod
    def payments_report(start_date, end_date):
        return Payment.query.filter(
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date,
            Payment.is_deleted == False
        ).all()

    @staticmethod
    def sales_report(start_date, end_date):
        return Sale.query.filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date,
            Sale.is_deleted == False
        ).all()
