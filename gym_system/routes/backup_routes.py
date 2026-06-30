from flask import Blueprint, render_template, redirect, url_for, flash, send_file
from services.backup_service import BackupService
from utils.security import login_required, role_required

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')

@backup_bp.route('/')
@login_required
@role_required('admin')
def index():
    return render_template('backups/backups.html')

@backup_bp.route('/download')
@login_required
@role_required('admin')
def download():
    """Genera el respaldo JSON en memoria y lo entrega para descarga directa.

    No se guarda nada en disco: en Render (plan free) el disco no es
    persistente, así que un archivo guardado ahí se perdería en el
    próximo reinicio/deploy sin que el admin pueda recuperarlo.
    """
    try:
        buf, filename = BackupService.generate_backup_json()
        return send_file(
            buf,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json',
        )
    except Exception as e:
        flash(f'Error al generar el respaldo: {e}', 'danger')
        return redirect(url_for('backup.index'))
