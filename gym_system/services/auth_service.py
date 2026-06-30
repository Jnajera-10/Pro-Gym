import bcrypt
from database.models.user import User
from database.db import db
import pytz
from datetime import datetime, timedelta

BOGOTA = pytz.timezone('America/Bogota')
MAX_ATTEMPTS = 5

class AuthService:
    @staticmethod
    def authenticate(username, password):
        user = User.query.filter_by(username=username, is_active=True).first()
        if not user:
            return None, 'Usuario o contraseña incorrectos.'
        now = datetime.now(BOGOTA)
        if user.locked_until and user.locked_until > now:
            return None, f'Cuenta bloqueada hasta {user.locked_until.strftime("%H:%M")}.'
        if bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            user.failed_attempts = 0
            user.last_login = now
            db.session.commit()
            return user, None
        user.failed_attempts += 1
        if user.failed_attempts >= MAX_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=15)
        db.session.commit()
        remaining = MAX_ATTEMPTS - user.failed_attempts
        return None, f'Contraseña incorrecta. Intentos restantes: {max(0, remaining)}.'

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def send_reset_email(email):
        from services.notification_service import NotificationService
        user = User.query.filter_by(email=email).first()
        if user:
            NotificationService.send_password_reset(user)
