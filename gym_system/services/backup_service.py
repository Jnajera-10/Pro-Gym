"""
BackupService — exporta los datos como JSON usando SQLAlchemy,
sin depender de pg_dump (que no está disponible en Render free).

IMPORTANTE: el disco de Render (plan free) NO es persistente — se
reinicia en cada deploy, reinicio o "sleep" del servicio. Por eso este
servicio ya NO guarda el respaldo en disco; genera el JSON en memoria
y lo entrega directamente para descarga (BytesIO), para que el admin
se lo guarde en su computador.
"""
import json
import io
import logging
from datetime import datetime, date
import pytz

BOGOTA = pytz.timezone('America/Bogota')
logger = logging.getLogger(__name__)


def _serialize(value):
    """Convierte tipos no-JSON a string."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _model_to_dict(instance):
    """Convierte una fila de SQLAlchemy a dict serializable."""
    return {
        col.name: _serialize(getattr(instance, col.name))
        for col in instance.__table__.columns
    }


class BackupService:

    @staticmethod
    def generate_backup_json():
        """
        Genera un backup JSON con todas las tablas principales,
        completamente en memoria (no escribe nada en disco).
        Devuelve (BytesIO, nombre_de_archivo).
        """
        from database.models.client import Client
        from database.models.payment import Payment
        from database.models.membership import Membership
        from database.models.sales import Sale, SaleItem
        from database.models.inventory import Product, StockMovement
        from database.models.attendance import Attendance
        from database.models.user import User
        from database.models.notifications import Notification
        from database.models.audit import AuditLog
        from database.models.settings import GymSettings

        tables = {
            'clients':        Client.query.all(),
            'payments':       Payment.query.all(),
            'memberships':    Membership.query.all(),
            'sales':          Sale.query.all(),
            'sale_items':     SaleItem.query.all(),
            'products':       Product.query.all(),
            'stock_movements': StockMovement.query.all(),
            'attendances':    Attendance.query.all(),
            'users':          User.query.all(),
            'notifications':  Notification.query.all(),
            'audit_logs':     AuditLog.query.all(),
            'gym_settings':   GymSettings.query.all(),
        }

        data = {
            'generated_at': datetime.now(BOGOTA).isoformat(),
            'tables': {
                name: [_model_to_dict(row) for row in rows]
                for name, rows in tables.items()
            }
        }

        timestamp = datetime.now(BOGOTA).strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.json'

        buf = io.BytesIO()
        buf.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
        buf.seek(0)

        logger.info(f'[backup] Backup generado para descarga: {filename}')
        return buf, filename

    @staticmethod
    def restore_backup(filename):
        """
        La restauración automática desde JSON requiere lógica de
        inserción tabla por tabla y está fuera del alcance de este
        módulo. Para restaurar, usa el archivo JSON descargado y
        contacta al administrador del sistema.
        """
        raise NotImplementedError(
            'La restauración automática no está disponible. '
            'Usa el archivo JSON descargado para restaurar manualmente.'
        )
