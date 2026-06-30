# Agrega esto en app.py o en un nuevo archivo routes/zkbio_routes.py

from flask import Blueprint, jsonify
from database.db import db
from database.models.client import Client
from database.models.payment import Payment
from datetime import date
from sqlalchemy import func

zkbio_bp = Blueprint('zkbio', __name__)


@zkbio_bp.route('/api/zkbio/membresias-activas', methods=['GET'])
def membresias_activas():
    """
    Devuelve todos los clientes con su membresía activa más reciente.
    El agente local usa esto para sincronizar ZKBio.
    """
    hoy = date.today()

    # Subconsulta: último pago por cliente
    ultimo_pago = (
        db.session.query(
            Payment.client_id,
            func.max(Payment.end_date).label('max_end_date'),
        )
        .filter(Payment.is_deleted == False)
        .group_by(Payment.client_id)
        .subquery()
    )

    # Join con clientes
    resultados = (
        db.session.query(Client, Payment)
        .join(Payment, Payment.client_id == Client.id)
        .join(
            ultimo_pago,
            (ultimo_pago.c.client_id == Payment.client_id) &
            (ultimo_pago.c.max_end_date == Payment.end_date),
        )
        .filter(Client.is_active == True)
        .filter(Payment.is_deleted == False)
        .all()
    )

    data = []
    for cliente, pago in resultados:
        data.append({
            "zkbio_id":   cliente.document_number,  # el 'id' en ZKBio = cédula
            "cedula":     cliente.document_number,
            "nombre":     cliente.full_name,
            "start_date": str(pago.start_date),
            "end_date":   str(pago.end_date),
            "activo":     pago.end_date >= hoy,
        })

    return jsonify(data)
