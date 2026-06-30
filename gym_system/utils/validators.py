import re
from database.models.client import Client

def validate_client(form):
    errors = []
    if not form.get('full_name'):
        errors.append('El nombre completo es obligatorio.')
    if not form.get('document_number'):
        errors.append('El número de documento es obligatorio.')
    else:
        existing = Client.query.filter_by(document_number=form['document_number']).first()
        if existing:
            errors.append('Ya existe un cliente con ese número de documento.')
    email = form.get('email')
    if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        errors.append('El correo electrónico no es válido.')
    return errors

def validate_positive_amount(value):
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False
