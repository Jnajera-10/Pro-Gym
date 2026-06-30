from database.models.sales import Sale, SaleItem
from database.models.inventory import Product
from database.db import db
from services.inventory_service import InventoryService
from services.audit_service import AuditService
from services.notification_queue import queue_event
import pytz
from datetime import datetime

BOGOTA = pytz.timezone('America/Bogota')


def _fmt(value):
    """Formatea número con puntos como separador de miles (estilo colombiano)."""
    return f"{int(value):,}".replace(',', '.')


class SalesService:
    @staticmethod
    def create_sale(client_id, items_data, payment_method, notes=None, is_pending=False):
        for item in items_data:
            product = Product.query.get(item['product_id'])
            if not product:
                raise ValueError(f'Producto {item["product_id"]} no encontrado.')
            if product.quantity < item['quantity']:
                raise ValueError(f'Stock insuficiente para "{product.name}". '
                                 f'Disponible: {product.quantity}, solicitado: {item["quantity"]}.')

        try:
            payment_status = 'pendiente' if is_pending else 'pagado'
            total = 0
            sale = Sale(
                client_id=client_id,
                payment_method=payment_method,
                notes=notes,
                total=0,
                payment_status=payment_status,
            )
            db.session.add(sale)
            db.session.flush()

            lines_whatsapp = []
            lines_audit = []

            for item in items_data:
                product = Product.query.get(item['product_id'])
                subtotal = product.sale_price * item['quantity']
                total += subtotal
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=item['quantity'],
                    unit_price=product.sale_price,
                    subtotal=subtotal
                )
                db.session.add(sale_item)
                product.quantity -= item['quantity']
                mov_class = InventoryService.build_movement(product.id, item['quantity'], 'Venta')
                db.session.add(mov_class)

                lines_whatsapp.append(f"  • {product.name} x{item['quantity']} = ${_fmt(subtotal)}")
                lines_audit.append(f"{product.name} x{item['quantity']} (${_fmt(subtotal)})")

            sale.total = total
            db.session.commit()

            # ── WhatsApp (encolado, se envía en el resumen horario) ────
            try:
                nombres = []
                for item in items_data:
                    prod = Product.query.get(item['product_id'])
                    if prod:
                        nombres.append(f"{prod.name} x{item['quantity']}")
                productos_str = ", ".join(nombres)

                texto = (
                    f"{productos_str} — ${_fmt(total)} ({payment_method})"
                    + (f" [{notes}]" if notes else "")
                )
                if is_pending:
                    queue_event('venta_pendiente', texto)
                else:
                    queue_event('venta', texto)
            except Exception as wa_exc:
                print(f'[WHATSAPP] Error encolando notificación de venta: {wa_exc}')

            # ── Auditoría ─────────────────────────────────────────────
            try:
                detalle = " | ".join(lines_audit)
                estado = "PENDIENTE" if is_pending else "PAGADO"
                AuditService.log(
                    action='VENTA',
                    table_name='sales',
                    record_id=sale.id,
                    old_value=None,
                    new_value=f"[{estado}] Total: ${_fmt(total)} | Pago: {payment_method} | {detalle}"
                )
            except Exception as audit_exc:
                print(f'[AUDIT] Error al registrar auditoría de venta: {audit_exc}')

            return sale

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def mark_as_paid(sale):
        """Marca una venta pendiente como pagada."""
        if sale.payment_status == 'pendiente':
            sale.payment_status = 'pagado'
            db.session.commit()
            return True
        return False
