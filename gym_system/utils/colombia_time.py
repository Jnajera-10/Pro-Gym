import pytz
from datetime import datetime

BOGOTA = pytz.timezone('America/Bogota')

def now_bogota():
    return datetime.now(BOGOTA)

def today_bogota():
    return datetime.now(BOGOTA).date()

def to_bogota(dt):
    if dt.tzinfo is None:
        return BOGOTA.localize(dt)
    return dt.astimezone(BOGOTA)

def format_date(dt):
    if dt is None:
        return ''
    return dt.strftime('%d/%m/%Y')

def format_datetime(dt):
    if dt is None:
        return ''
    return dt.strftime('%d/%m/%Y %H:%M')
