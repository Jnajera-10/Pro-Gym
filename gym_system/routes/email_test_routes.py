"""
Módulo de prueba de emails — solo visible para admin.
Permite:
  1. Simular que hoy es otra fecha (para probar los avisos de vencimiento).
  2. Enviar un email de prueba manual a cualquier cliente.
  3. Ejecutar el job de vencimientos en ese momento.
"""
import os
import pytz
import logging
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.models.client import Client
from database.models.payment import Payment
from utils.security import login_required, role_required

email_test_bp = Blueprint('email_test', __name__, url_prefix='/email-test')
BOGOTA = pytz.timezone('America/Bogota')
logger = logging.getLogger(__name__)

# Clave de sesión para la fecha simulada
SESSION_KEY = '_simulated_date'


def get_simulated_date():
    """Devuelve la fecha simulada si está activa, o None."""
    sd = session.get(SESSION_KEY)
    if sd:
        try:
            return date.fromisoformat(sd)
        except Exception:
            session.pop(SESSION_KEY, None)
    return None


@email_test_bp.route('/', methods=['GET'])
@login_required
@role_required('admin')
def index():
    simulated = get_simulated_date()
    real_today = datetime.now(BOGOTA).date()

    # Cargar pagos que vencen en los próximos 5 días o vencieron ayer
    # usando la fecha simulada si está activa
    ref_date = simulated or real_today
    upcoming = Payment.query.filter(
        Payment.end_date >= ref_date - timedelta(days=1),
        Payment.end_date <= ref_date + timedelta(days=5),
        Payment.is_deleted == False,
    ).order_by(Payment.end_date).all()

    # Marcar cuántos días faltan respecto a la fecha de referencia
    for p in upcoming:
        p._days_left = (p.end_date - ref_date).days

    clients = Client.query.filter_by(is_active=True).order_by(Client.full_name).all()

    brevo_ok = bool(os.environ.get('BREVO_API_KEY'))
    mail_from_ok = bool(os.environ.get('MAIL_FROM'))

    return render_template(
        'email_test/email_test.html',
        simulated=simulated,
        real_today=real_today,
        upcoming=upcoming,
        clients=clients,
        brevo_ok=brevo_ok,
        mail_from_ok=mail_from_ok,
    )


@email_test_bp.route('/set-date', methods=['POST'])
@login_required
@role_required('admin')
def set_date():
    """Activa una fecha simulada."""
    fecha_str = request.form.get('fecha', '').strip()
    if not fecha_str:
        flash('Ingresa una fecha válida.', 'danger')
        return redirect(url_for('email_test.index'))
    try:
        date.fromisoformat(fecha_str)  # validar formato
        session[SESSION_KEY] = fecha_str
        flash(f'✅ Fecha simulada activada: {fecha_str}. '
              'El job de vencimientos usará esta fecha.', 'success')
    except ValueError:
        flash('Formato de fecha inválido. Usa AAAA-MM-DD.', 'danger')
    return redirect(url_for('email_test.index'))


@email_test_bp.route('/clear-date', methods=['POST'])
@login_required
@role_required('admin')
def clear_date():
    """Desactiva la fecha simulada, vuelve a la fecha real."""
    session.pop(SESSION_KEY, None)
    flash('Fecha simulada eliminada. Ahora se usa la fecha real.', 'info')
    return redirect(url_for('email_test.index'))


@email_test_bp.route('/run-job', methods=['POST'])
@login_required
@role_required('admin')
def run_job():
    """
    Ejecuta el job de vencimientos usando la fecha simulada.
    Ignora el control de 'ya corrió hoy' para poder probar varias veces.
    """
    from flask import current_app
    simulated = get_simulated_date()
    ref_date = simulated or datetime.now(BOGOTA).date()

    try:
        from services.notification_service import NotificationService

        sent = 0
        errors = 0

        # Avisos de vencimiento próximo (3 días y 1 día)
        for days in [3, 1]:
            target = ref_date + timedelta(days=days)
            payments = Payment.query.filter(
                Payment.end_date == target,
                Payment.is_deleted == False,
            ).all()
            for p in payments:
                if p.client and p.client.email and p.client.is_active:
                    ok = NotificationService.send_expiry_warning(p, days)
                    sent += 1 if ok else 0
                    errors += 0 if ok else 1

        # Avisos de membresía expirada (vencieron "ayer" según la fecha ref)
        yesterday = ref_date - timedelta(days=1)
        expired = Payment.query.filter(
            Payment.end_date == yesterday,
            Payment.is_deleted == False,
        ).all()
        for p in expired:
            if p.client and p.client.email and p.client.is_active:
                ok = NotificationService.send_expired_notice(p)
                sent += 1 if ok else 0
                errors += 0 if ok else 1

        msg = f'Job ejecutado con fecha {ref_date}. Enviados: {sent}'
        if errors:
            msg += f', fallidos: {errors} (revisa Notificaciones)'
            flash(msg, 'warning')
        else:
            flash(msg, 'success')

    except Exception as exc:
        logger.error(f'[email_test] Error ejecutando job: {exc}', exc_info=True)
        flash(f'Error al ejecutar el job: {str(exc)[:200]}', 'danger')

    return redirect(url_for('email_test.index'))


@email_test_bp.route('/send-test', methods=['POST'])
@login_required
@role_required('admin')
def send_test():
    """Envía un email de prueba directo a un cliente específico."""
    tipo = request.form.get('tipo')
    payment_id = request.form.get('payment_id', type=int)

    if not payment_id:
        flash('Selecciona un pago.', 'danger')
        return redirect(url_for('email_test.index'))

    payment = Payment.query.get_or_404(payment_id)

    try:
        from services.notification_service import NotificationService

        if tipo == 'confirmacion':
            ok = NotificationService.send_payment_confirmation(payment)
            label = 'Confirmación de pago'
        elif tipo == 'aviso_3':
            ok = NotificationService.send_expiry_warning(payment, 3)
            label = 'Aviso 3 días antes'
        elif tipo == 'aviso_1':
            ok = NotificationService.send_expiry_warning(payment, 1)
            label = 'Aviso 1 día antes'
        elif tipo == 'expirado':
            ok = NotificationService.send_expired_notice(payment)
            label = 'Membresía expirada'
        else:
            flash('Tipo de email inválido.', 'danger')
            return redirect(url_for('email_test.index'))

        if ok:
            flash(f'✅ Email "{label}" enviado a {payment.client.email}', 'success')
        else:
            flash(f'❌ Falló el envío de "{label}". Revisa BREVO_API_KEY y MAIL_FROM en Render.', 'danger')

    except Exception as exc:
        flash(f'Error: {str(exc)[:200]}', 'danger')

    return redirect(url_for('email_test.index'))
