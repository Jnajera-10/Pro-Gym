from app import application
from database.db import db
from database.models.client import Client
from sqlalchemy import text

with application.app_context():
    # ── Migraciones de columnas / tablas (idempotentes) ──────────────
    with db.engine.connect() as conn:
        conn.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS shift VARCHAR(10) DEFAULT 'manana'"))
        conn.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS cash_received FLOAT"))
        conn.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS cash_change FLOAT"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cash_registers (
                id SERIAL PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                opening_cash FLOAT NOT NULL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          SERIAL PRIMARY KEY,
                date        DATE NOT NULL,
                amount      FLOAT NOT NULL,
                description VARCHAR(255) NOT NULL,
                category    VARCHAR(80),
                created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at  TIMESTAMP
            )
        """))
        conn.commit()
    print("OK — migraciones de columnas aplicadas")

    # ── Crear cliente especial DIARIO si no existe ───────────────────
    diario = Client.query.filter_by(document_number='DIARIO-0000').first()
    if not diario:
        diario = Client(
            full_name       = 'DIARIO',
            document_type   = 'otro',
            document_number = 'DIARIO-0000',
            is_active       = True,
            notes           = 'Cliente especial para pagos diarios sin registro individual.',
        )
        db.session.add(diario)
        db.session.commit()
        print("OK — Cliente DIARIO creado con ID:", diario.id)
    else:
        print("OK — Cliente DIARIO ya existía con ID:", diario.id)

    print("OK — migraciones aplicadas correctamente")
