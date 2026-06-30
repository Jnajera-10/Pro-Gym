from database.models.attendance import Attendance
from database.db import db
import pytz
from datetime import datetime

BOGOTA = pytz.timezone('America/Bogota')

class AttendanceService:
    @staticmethod
    def register(client_id, notes=None):
        record = Attendance(client_id=client_id, notes=notes)
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def today():
        today = datetime.now(BOGOTA).date()
        return Attendance.query.filter(
            db.func.date(Attendance.check_in) == today
        ).all()
