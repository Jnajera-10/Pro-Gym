from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.models.user import User
from database.models.client import Client
from database.models.payment import Payment
from database.db import db
from utils.security import hash_password, login_required, role_required
from datetime import datetime
import pytz

BOGOTA = pytz.timezone('America/Bogota')

user_bp = Blueprint('user', __name__, url_prefix='/user')


def _enrich_users(users):
    """
    Agrega a cada usuario sus datos de membresía activa si tiene
    un cliente vinculado por email o nombre.
    Esto permite mostrar días restantes en la tabla de usuarios.
    """
    today = datetime.now(BOGOTA).date()
    enriched = []
    for u in users:
        # Buscar cliente por email (campo más confiable)
        client = None
        if u.email:
            client = Client.query.filter_by(email=u.email, is_active=True).first()
        # Si no hay match por email, buscar por nombre exacto
        if not client and u.full_name:
            client = Client.query.filter_by(full_name=u.full_name, is_active=True).first()

        active_payment = None
        if client:
            active_payment = (
                Payment.query
                .filter(
                    Payment.client_id  == client.id,
                    Payment.is_deleted == False,
                    Payment.start_date <= today,
                    Payment.end_date   >= today,
                )
                .order_by(Payment.end_date.desc())
                .first()
            )

        # Agregar atributos dinámicos al objeto para el template
        u.active_plan = active_payment.membership.name if active_payment else None
        u.days_left   = (active_payment.end_date - today).days if active_payment else None
        enriched.append(u)
    return enriched


@user_bp.route('/')
@login_required
@role_required('admin')
def index():
    users = User.query.order_by(User.full_name).all()
    users = _enrich_users(users)
    return render_template('users/users.html', users=users)


@user_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    if request.method == 'POST':
        # Verificar duplicados
        if User.query.filter_by(username=request.form['username']).first():
            flash('Ese nombre de usuario ya existe.', 'danger')
            return render_template('users/create_user.html')
        if User.query.filter_by(email=request.form['email']).first():
            flash('Ese email ya está registrado.', 'danger')
            return render_template('users/create_user.html')

        user = User(
            username      = request.form['username'].strip(),
            email         = request.form['email'].strip().lower(),
            password_hash = hash_password(request.form['password']),
            full_name     = request.form['full_name'].strip(),
            role          = request.form['role'],
        )
        db.session.add(user)
        db.session.commit()
        flash(f'Usuario "{user.username}" creado correctamente.', 'success')
        return redirect(url_for('user.index'))
    return render_template('users/create_user.html')


@user_bp.route('/<int:user_id>/deactivate', methods=['POST'])
@login_required
@role_required('admin')
def deactivate(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('No se puede desactivar un administrador.', 'danger')
        return redirect(url_for('user.index'))
    user.is_active = False
    db.session.commit()
    flash(f'Usuario "{user.username}" desactivado.', 'warning')
    return redirect(url_for('user.index'))
