from flask import request, redirect, url_for, flash, render_template, session
from database.models.expense import Expense
from database.db import db
from services.audit_service import AuditService
import pytz
from datetime import datetime

BOGOTA = pytz.timezone('America/Bogota')


class ExpenseController:

    @staticmethod
    def index():
        """Lista de egresos del mes actual (visible solo desde dashboard o aquí)."""
        expenses = (
            Expense.query
            .order_by(Expense.date.desc(), Expense.created_at.desc())
            .limit(100)
            .all()
        )
        return render_template('expenses/expenses.html', expenses=expenses)

    @staticmethod
    def create():
        """Registra un egreso. Solo admin (protegido en la ruta)."""
        try:
            amount = float(request.form.get('amount', 0))
            if amount <= 0:
                flash('El monto del egreso debe ser mayor a cero.', 'danger')
                return redirect(url_for('dashboard.index'))

            description = request.form.get('description', '').strip()
            if not description:
                flash('La descripción del egreso es obligatoria.', 'danger')
                return redirect(url_for('dashboard.index'))

            raw_date = request.form.get('expense_date', '').strip()
            if raw_date:
                expense_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
            else:
                expense_date = datetime.now(BOGOTA).date()

            expense = Expense(
                date        = expense_date,
                amount      = amount,
                description = description,
                category    = request.form.get('category', '').strip() or None,
                created_by  = session.get('user_id'),
            )
            db.session.add(expense)
            db.session.commit()
            AuditService.log('create', 'expenses', expense.id, None,
                             f'${amount:,.0f} — {description}')
            flash(f'✅ Egreso de ${amount:,.0f} registrado.', 'success')
        except (ValueError, TypeError) as e:
            db.session.rollback()
            flash(f'Error al registrar egreso: {e}', 'danger')

        return redirect(url_for('dashboard.index'))

    @staticmethod
    def delete(expense_id):
        expense = Expense.query.get_or_404(expense_id)
        desc = f'${expense.amount:,.0f} — {expense.description}'
        db.session.delete(expense)
        db.session.commit()
        AuditService.log('delete', 'expenses', expense_id, desc, 'ELIMINADO')
        flash('Egreso eliminado.', 'warning')
        return redirect(url_for('dashboard.index'))
