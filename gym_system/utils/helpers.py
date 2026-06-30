def format_currency(value):
    return f'${value:,.0f}'

def days_until(date):
    from utils.colombia_time import today_bogota
    delta = date - today_bogota()
    return delta.days

def membership_status(end_date):
    days = days_until(end_date)
    if days < 0:
        return 'vencido'
    if days <= 3:
        return 'por_vencer'
    return 'activo'


# ── Pago mixto: parsear/serializar método de pago ─────────────────
# Formato guardado en payment_method: "efectivo:3000|nequi:2000"
# Si es un método simple (sin "|"), se trata como antes.

def parse_payment_split(payment_method_str, fallback_amount=None):
    """
    Retorna lista de (metodo, monto) desde el string guardado.
    Ej: "efectivo:3000|nequi:2000" → [('efectivo', 3000.0), ('nequi', 2000.0)]
    Ej: "efectivo" → [('efectivo', None)]
    Si se pasa fallback_amount, los métodos sin monto usan ese valor.
    """
    if not payment_method_str:
        return [('efectivo', float(fallback_amount) if fallback_amount is not None else None)]
    parts = []
    for chunk in payment_method_str.split('|'):
        chunk = chunk.strip()
        if ':' in chunk:
            method, amount_str = chunk.split(':', 1)
            try:
                parts.append((method.strip(), float(amount_str.strip())))
            except ValueError:
                parts.append((method.strip(), float(fallback_amount) if fallback_amount is not None else None))
        else:
            parts.append((chunk, float(fallback_amount) if fallback_amount is not None else None))
    return parts


def serialize_payment_split(methods_amounts):
    """
    Serializa lista de (metodo, monto) al formato de almacenamiento.
    Ej: [('efectivo', 3000), ('nequi', 2000)] → "efectivo:3000|nequi:2000"
    """
    parts = []
    for m, a in methods_amounts:
        if not m:
            continue
        if a is not None:
            parts.append(f'{m}:{int(a)}')
        else:
            parts.append(m)
    return '|'.join(parts)


def primary_payment_method(payment_method_str):
    """Retorna el primer método (para compatibilidad con filtros existentes)."""
    parts = parse_payment_split(payment_method_str)
    return parts[0][0] if parts else 'efectivo'
