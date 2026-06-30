"""
Cola en memoria para agrupar eventos (pagos, ventas, eliminaciones, etc.)
y enviarlos al dueño en UN solo mensaje de WhatsApp por hora, en vez de
un mensaje por cada evento.

Esto evita chocar con el límite de CallMeBot (25 mensajes / 4 horas).

Uso:
    from services.notification_queue import queue_event
    queue_event('pago', "Juan Pérez - $50.000 (Mensual)")

El job hourly_summary_job.py vacía la cola cada hora y manda el resumen.
"""
import threading

_lock = threading.Lock()

# Cada item: {'tipo': 'pago' | 'pago_pendiente' | 'pago_eliminado' | 'venta' | 'venta_pendiente' | 'venta_cobrada', 'texto': str}
_queue = []


def queue_event(tipo: str, texto: str):
    """Agrega un evento a la cola en memoria. Thread-safe."""
    with _lock:
        _queue.append({'tipo': tipo, 'texto': texto})


def pop_all():
    """Devuelve todos los eventos acumulados y vacía la cola."""
    with _lock:
        items = list(_queue)
        _queue.clear()
        return items


def pending_count() -> int:
    with _lock:
        return len(_queue)
