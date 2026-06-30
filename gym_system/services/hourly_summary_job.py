"""
Job horario que junta todos los eventos acumulados (pagos, ventas,
eliminaciones, cobros pendientes) y envía UN solo mensaje de WhatsApp
al dueño con el resumen, en vez de un mensaje por cada evento.

Se dispara desde /health (igual que daily_report_job), pero corre
como máximo 1 vez por hora, y SOLO entre las 5:00am y las 10:00pm
(hora Bogotá). Fuera de ese rango los eventos quedan en la cola sin
enviarse, y se incluyen en el primer resumen del día (a las 5am).

Si no hubo ningún evento en la hora correspondiente, no envía nada
(para no gastar mensajes sin necesidad).
"""
import pytz
import logging
from datetime import datetime
from services.notification_queue import pop_all

BOGOTA = pytz.timezone('America/Bogota')
logger = logging.getLogger(__name__)

HORA_INICIO = 5    # 5:00 am
HORA_FIN    = 22   # 10:00 pm (no se envía después de esta hora)
LIMITE_CARACTERES = 3500  # margen de seguridad bajo los 4096 de WhatsApp

_last_run_hour_key = None  # ej. "2026-06-29-14"

ICONOS = {
    'pago': '💪',
    'pago_pendiente': '⏳',
    'pago_eliminado': '🗑️',
    'venta': '🛒',
    'venta_pendiente': '⏳',
    'venta_cobrada': '✅',
}

TITULOS = {
    'pago': 'Pagos nuevos',
    'pago_pendiente': 'Pagos pendientes',
    'pago_eliminado': 'Pagos eliminados',
    'venta': 'Ventas (inventario)',
    'venta_pendiente': 'Ventas pendientes',
    'venta_cobrada': 'Ventas cobradas',
}


def _construir_bloques(eventos):
    """Agrupa eventos por tipo y devuelve una lista de bloques de texto."""
    grupos = {}
    for ev in eventos:
        grupos.setdefault(ev['tipo'], []).append(ev['texto'])

    bloques = []
    for tipo, textos in grupos.items():
        icono = ICONOS.get(tipo, '•')
        titulo = TITULOS.get(tipo, tipo)
        lineas = "\n".join(f"  • {t}" for t in textos)
        bloques.append(f"{icono} *{titulo}* ({len(textos)})\n{lineas}")
    return bloques


def _partir_en_mensajes(bloques, encabezado, pie):
    """
    Reparte los bloques en uno o más mensajes que no superen
    LIMITE_CARACTERES. Si un bloque por sí solo ya supera el límite
    (ej. un mismo tipo de evento con muchísimas líneas en la hora),
    ese bloque se corta línea por línea en sub-bloques, conservando
    el título y el contador correctos en cada parte.
    """
    margen = len(encabezado) + len(pie)
    mensajes = []
    actual = []
    largo_actual = margen

    def _agregar(pieza):
        nonlocal actual, largo_actual
        costo = len(pieza) + 2  # separador "\n\n"
        if actual and (largo_actual + costo) > LIMITE_CARACTERES:
            mensajes.append(actual)
            actual = []
            largo_actual = margen
        actual.append(pieza)
        largo_actual += costo

    for bloque in bloques:
        if margen + len(bloque) + 2 <= LIMITE_CARACTERES:
            _agregar(bloque)
            continue

        # Bloque demasiado grande: lo partimos línea por línea
        lineas = bloque.split('\n')
        titulo_linea = lineas[0]
        items = lineas[1:]
        sub_items = []
        sub_largo = margen + len(titulo_linea) + 2
        for item in items:
            if sub_items and (sub_largo + len(item) + 1) > LIMITE_CARACTERES:
                _agregar(titulo_linea + '\n' + '\n'.join(sub_items))
                sub_items = []
                sub_largo = margen + len(titulo_linea) + 2
            sub_items.append(item)
            sub_largo += len(item) + 1
        if sub_items:
            _agregar(titulo_linea + '\n' + '\n'.join(sub_items))

    if actual:
        mensajes.append(actual)

    return mensajes


def run_hourly_summary(app):
    global _last_run_hour_key

    with app.app_context():
        now = datetime.now(BOGOTA)
        hour_key = now.strftime('%Y-%m-%d-%H')

        # Fuera del horario 5am-10pm: no enviar, dejar acumulando en la cola
        if now.hour < HORA_INICIO or now.hour >= HORA_FIN:
            return

        # Ya corrió esta hora
        if _last_run_hour_key == hour_key:
            return

        _last_run_hour_key = hour_key

        try:
            eventos = pop_all()
            if not eventos:
                logger.info(f'[hourly_summary] {hour_key} — sin eventos, no se envía nada.')
                return

            fecha_str = now.strftime('%d/%m/%Y')
            hora_str = now.strftime('%H:%M')
            bloques = _construir_bloques(eventos)

            encabezado = f"📊 *RESUMEN PRO-GYM*\n📅 {fecha_str} — {hora_str}\n{'-'*28}\n"
            pie = f"\n{'-'*28}\nTotal eventos: {len(eventos)}"

            partes = _partir_en_mensajes(bloques, encabezado, pie)

            from services.notification_service import send_whatsapp_owner

            total_partes = len(partes)
            for i, parte_bloques in enumerate(partes, start=1):
                cuerpo = "\n\n".join(parte_bloques)
                sufijo_parte = f" (parte {i}/{total_partes})" if total_partes > 1 else ""
                mensaje = f"{encabezado.rstrip(chr(10))}{sufijo_parte}\n{cuerpo}{pie}"
                send_whatsapp_owner(mensaje)

            logger.info(
                f'[hourly_summary] {hour_key} — resumen enviado '
                f'({len(eventos)} eventos, {total_partes} mensaje(s)).'
            )

        except Exception as exc:
            logger.error(f'[hourly_summary] Error generando resumen: {exc}', exc_info=True)
