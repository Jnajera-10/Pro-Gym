from database.models.payment import Payment, PaymentItem, _get_shift
from database.models.membership import Membership
from database.models.client import Client
from database.models.attendance import Attendance
from database.models.inventory import Product, StockMovement
from database.db import db
import pytz
from datetime import datetime, timedelta

BOGOTA = pytz.timezone('America/Bogota')


class PaymentService:

    @staticmethod
    def register_payment(form_data):
        membership = Membership.query.get(form_data['membership_id'])
        if not membership:
            return None, None, 'Membresía no encontrada.'

        start_date = datetime.strptime(form_data['start_date'], '%Y-%m-%d').date()
        end_date   = start_date + timedelta(days=membership.duration_days - 1)

        form_data = dict(form_data)
        if membership.membership_type == 'diario':
            diario_client = Client.query.filter_by(document_number='DIARIO-0000').first()
            if not diario_client:
                diario_client = Client(
                    full_name='DIARIO', document_type='otro',
                    document_number='DIARIO-0000', is_active=True,
                    notes='Cliente especial para pagos diarios.',
                )
                db.session.add(diario_client)
                db.session.flush()
            form_data['client_id'] = str(diario_client.id)

        partner_client_id = None
        partner_payment   = None
        if membership.is_couple_plan:
            raw_partner = form_data.get('partner_client_id', '').strip()
            if not raw_partner:
                return None, None, 'El Plan Pareja requiere seleccionar un segundo cliente.'
            partner_client_id = int(raw_partner)
            if partner_client_id == int(form_data['client_id']):
                return None, None, 'Los dos clientes del Plan Pareja deben ser diferentes.'
            partner = Client.query.get(partner_client_id)
            if not partner or not partner.is_active:
                return None, None, 'El segundo cliente del Plan Pareja no existe o está inactivo.'

        if membership.is_student_plan:
            if form_data.get('is_student') != 'on':
                return None, None, 'El Plan Estudiantil es exclusivo para bachilleres. Confirma el requisito.'

        # ── Cantidad de personas (plan diario) ────────────────────
        try:
            daily_quantity = max(1, int(form_data.get('daily_quantity', 1) or 1))
        except (ValueError, TypeError):
            daily_quantity = 1

        cash_received = None
        cash_change   = None

        split_parts = []
        for i in range(1, 5):
            m = form_data.get(f'method_{i}', '').strip()
            a = form_data.get(f'amount_{i}', '').strip()
            if m and a:
                try:
                    split_parts.append((m, float(a)))
                except ValueError:
                    pass

        if not split_parts:
            m = form_data.get('payment_method', 'efectivo')
            try:
                a = float(form_data.get('amount', 0))
            except (ValueError, TypeError):
                a = 0
            split_parts = [(m, a)]

        amount_val = sum(a for _, a in split_parts) if split_parts else 0
        if amount_val == 0:
            try:
                amount_val = float(form_data.get('amount', 0))
            except (ValueError, TypeError):
                amount_val = 0

        # Último fallback: si amount_val sigue en 0, calcular desde el precio
        # del plan × cantidad de personas (evita que pagos queden guardados como $0)
        if amount_val == 0 and membership and membership.price:
            try:
                daily_qty_fb = max(1, int(form_data.get('daily_quantity', 1) or 1))
                amount_val = float(membership.price) * daily_qty_fb
            except (ValueError, TypeError):
                amount_val = float(membership.price)

        # Si hay un solo método con monto 0 pero amount_val ya se resolvió,
        # actualizar split_parts antes de serializar para que WhatsApp muestre el monto correcto.
        if len(split_parts) == 1 and split_parts[0][1] == 0 and amount_val > 0:
            split_parts = [(split_parts[0][0], amount_val)]

        from utils.helpers import serialize_payment_split
        payment_method_str = serialize_payment_split(split_parts)


        efectivo_amount = sum(a for m, a in split_parts if m == 'efectivo')
        if efectivo_amount > 0:
            try:
                cash_received = float(form_data.get('cash_received') or 0) or None
                if cash_received:
                    cash_change = max(0, cash_received - efectivo_amount)
            except (ValueError, TypeError):
                pass

        raw_payment_date = form_data.get('payment_date', '').strip()
        if raw_payment_date:
            try:
                payment_date = datetime.strptime(raw_payment_date, '%Y-%m-%d').date()
            except ValueError:
                payment_date = datetime.now(BOGOTA).date()
        else:
            payment_date = datetime.now(BOGOTA).date()

        is_pending = form_data.get('is_pending') == 'on'
        payment_status = 'pendiente' if is_pending else 'pagado'

        # ── Productos del inventario ───────────────────────────────
        product_ids = form_data.getlist('inv_product_id') if hasattr(form_data, 'getlist') else []
        inv_quantities = form_data.getlist('inv_quantity') if hasattr(form_data, 'getlist') else []

        inv_items = []
        inv_total = 0.0
        for pid_str, qty_str in zip(product_ids, inv_quantities):
            try:
                pid = int(pid_str)
                qty = int(qty_str)
                if qty <= 0:
                    continue
                product = Product.query.get(pid)
                if not product or not product.is_active:
                    continue
                if product.quantity < qty:
                    return None, None, f'Stock insuficiente para "{product.name}". Disponible: {product.quantity}.'
                subtotal = product.sale_price * qty
                inv_items.append({'product': product, 'qty': qty, 'unit_price': product.sale_price, 'subtotal': subtotal})
                inv_total += subtotal
            except (ValueError, TypeError):
                continue

        total_amount = amount_val + inv_total

        payment = Payment(
            client_id        = int(form_data['client_id']),
            membership_id    = int(form_data['membership_id']),
            amount           = total_amount,
            payment_date     = payment_date,
            start_date       = start_date,
            end_date         = end_date,
            payment_method   = payment_method_str,
            notes            = form_data.get('notes'),
            partner_client_id= partner_client_id,
            shift            = form_data.get('shift', _get_shift()),
            cash_received    = cash_received,
            cash_change      = cash_change,
            payment_status   = payment_status,
            daily_quantity   = daily_quantity,
        )
        db.session.add(payment)
        db.session.flush()

        # Guardar items de inventario
        for item in inv_items:
            pi = PaymentItem(
                payment_id = payment.id,
                product_id = item['product'].id,
                quantity   = item['qty'],
                unit_price = item['unit_price'],
                subtotal   = item['subtotal'],
            )
            db.session.add(pi)
            # Descontar stock
            item['product'].quantity -= item['qty']
            db.session.add(StockMovement(
                product_id    = item['product'].id,
                movement_type = 'salida',
                quantity      = item['qty'],
                reason        = f'Venta con membresía #{payment.id}',
            ))

        if membership.is_couple_plan and partner_client_id:
            primary_method = payment_method_str.split(':')[0].split('|')[0].strip()
            partner_payment = Payment(
                client_id        = partner_client_id,
                membership_id    = int(form_data['membership_id']),
                amount           = 0,
                start_date       = start_date,
                end_date         = end_date,
                payment_method   = primary_method,
                notes            = f'Plan Pareja — vinculado al pago del cliente #{form_data["client_id"]}',
                partner_client_id= int(form_data['client_id']),
                payment_status   = payment_status,
            )
            db.session.add(partner_payment)

        db.session.commit()

        now_bogota = datetime.now(BOGOTA)
        today      = now_bogota.date()
        diario_id  = None
        _dc = Client.query.filter_by(document_number='DIARIO-0000').first()
        if _dc:
            diario_id = _dc.id

        for client_id_att in set(filter(None, [int(form_data['client_id']), partner_client_id])):
            if client_id_att == diario_id:
                continue
            ya_asistio = Attendance.query.filter(
                Attendance.client_id == client_id_att,
                db.func.date(Attendance.check_in) == today,
            ).first()
            if not ya_asistio:
                db.session.add(Attendance(
                    client_id = client_id_att,
                    check_in  = now_bogota,
                    notes     = 'Asistencia registrada automáticamente al pagar',
                ))

        db.session.commit()
        return payment, partner_payment, None

    @staticmethod
    def mark_as_paid(payment):
        if payment.payment_status == 'pendiente':
            payment.payment_status = 'pagado'
            db.session.commit()
            return True
        return False

    @staticmethod
    def today_income():
        today = datetime.now(BOGOTA).date()
        payments = Payment.query.filter(
            Payment.payment_date == today,
            Payment.is_deleted   == False,
            Payment.payment_status == 'pagado',
        ).all()
        return sum(p.amount for p in payments)

    @staticmethod
    def month_income():
        now = datetime.now(BOGOTA)
        from sqlalchemy import extract
        payments = Payment.query.filter(
            extract('month', Payment.payment_date) == now.month,
            extract('year',  Payment.payment_date) == now.year,
            Payment.is_deleted == False,
            Payment.payment_status == 'pagado',
        ).all()
        return sum(p.amount for p in payments)

    @staticmethod
    def month_payments_raw():
        now = datetime.now(BOGOTA)
        from sqlalchemy import extract
        return Payment.query.filter(
            extract('month', Payment.payment_date) == now.month,
            extract('year',  Payment.payment_date) == now.year,
            Payment.is_deleted == False,
            Payment.payment_status == 'pagado',
        ).all()

    @staticmethod
    def income_since(since_date):
        payments = Payment.query.filter(
            Payment.payment_date >= since_date,
            Payment.is_deleted   == False,
            Payment.payment_status == 'pagado',
        ).all()
        return sum(p.amount for p in payments)

    @staticmethod
    def payments_since_raw(since_date):
        return Payment.query.filter(
            Payment.payment_date >= since_date,
            Payment.is_deleted   == False,
            Payment.payment_status == 'pagado',
        ).all()

    @staticmethod
    def soft_delete_payment(payment):
        payment.is_deleted = True
        mirror = None
        if payment.partner_client_id:
            mirror = Payment.query.filter(
                Payment.client_id == payment.partner_client_id,
                Payment.partner_client_id == payment.client_id,
                Payment.membership_id == payment.membership_id,
                Payment.start_date == payment.start_date,
                Payment.end_date == payment.end_date,
                Payment.is_deleted == False,
                Payment.id != payment.id,
            ).first()
            if mirror:
                mirror.is_deleted = True
        return mirror
