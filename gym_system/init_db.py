from app import application
from database.db import db
from database.models.user import User
from database.models.settings import GymSettings
import bcrypt

with application.app_context():
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        pw = bcrypt.hashpw('Admin2025!'.encode(), bcrypt.gensalt()).decode()
        admin = User(
            username='admin',
            email='admin@gimnasio.com',
            password_hash=pw,
            full_name='Administrador',
            role='admin',
            is_active=True
        )
        db.session.add(admin)

    if not GymSettings.query.first():
        settings = GymSettings(gym_name='Mi Gimnasio')
        db.session.add(settings)

    db.session.commit()
    print('✅ Base de datos lista')
    print('👤 Usuario: admin | Contraseña: Admin2025!')
