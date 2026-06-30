from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.models.user import User
from database.db import db
from utils.security import login_required, hash_password
import bcrypt
import pytz
from datetime import datetime

BOGOTA = pytz.timezone('America/Bogota')

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user_id = session.get('user_id')
    user    = User.query.get_or_404(user_id)

    if request.method == 'POST':
        action = request.form.get('action')

        # ── Cambio de contraseña ──────────────────────────────────
        if action == 'change_password':
            current_pw  = request.form.get('current_password', '')
            new_pw      = request.form.get('new_password', '')
            confirm_pw  = request.form.get('confirm_password', '')

            # Validar contraseña actual
            if not bcrypt.checkpw(current_pw.encode(), user.password_hash.encode()):
                flash('La contraseña actual es incorrecta.', 'danger')
                return render_template('profile/profile.html', user=user)

            # Validar nueva contraseña
            if len(new_pw) < 6:
                flash('La nueva contraseña debe tener al menos 6 caracteres.', 'danger')
                return render_template('profile/profile.html', user=user)

            if new_pw != confirm_pw:
                flash('Las contraseñas nuevas no coinciden.', 'danger')
                return render_template('profile/profile.html', user=user)

            user.password_hash = hash_password(new_pw)
            user.updated_at    = datetime.now(BOGOTA)
            db.session.commit()
            flash('✅ Contraseña actualizada correctamente.', 'success')
            return redirect(url_for('profile.index'))

        # ── Actualizar datos personales (nombre y email) ──────────
        if action == 'update_info':
            new_name  = request.form.get('full_name', '').strip()
            new_email = request.form.get('email', '').strip().lower()

            if not new_name:
                flash('El nombre no puede estar vacío.', 'danger')
                return render_template('profile/profile.html', user=user)

            # Verificar que el email no lo use otro usuario
            if new_email and new_email != user.email:
                email_taken = User.query.filter(
                    User.email == new_email,
                    User.id    != user.id,
                ).first()
                if email_taken:
                    flash('Ese email ya está registrado por otro usuario.', 'danger')
                    return render_template('profile/profile.html', user=user)

            user.full_name  = new_name
            user.email      = new_email
            user.updated_at = datetime.now(BOGOTA)
            db.session.commit()
            flash('✅ Datos actualizados correctamente.', 'success')
            return redirect(url_for('profile.index'))

    return render_template('profile/profile.html', user=user)
