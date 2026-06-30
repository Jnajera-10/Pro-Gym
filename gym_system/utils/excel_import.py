import openpyxl
from database.models.client import Client
from database.db import db

def import_clients_from_excel(filepath):
    wb = openpyxl.load_workbook(filepath)
    ws = wb.active
    imported, errors = 0, []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        try:
            client = Client(
                full_name=row[0],
                document_type=row[1] or 'CC',
                document_number=str(row[2]),
                email=row[3],
                phone=str(row[4]) if row[4] else None,
                is_migrated=True
            )
            db.session.add(client)
            imported += 1
        except Exception as e:
            errors.append(str(e))
    db.session.commit()
    return imported, errors
