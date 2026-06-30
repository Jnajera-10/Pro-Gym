from flask import Blueprint
from controllers.expense_controller import ExpenseController
from utils.security import login_required, admin_required

expense_bp = Blueprint('expenses', __name__, url_prefix='/expenses')

# Solo admin puede ver y gestionar egresos
expense_bp.add_url_rule('/',        'index',  admin_required(ExpenseController.index),  methods=['GET'])
expense_bp.add_url_rule('/create',  'create', admin_required(ExpenseController.create), methods=['POST'])
expense_bp.add_url_rule('/<int:expense_id>/delete', 'delete',
                        admin_required(ExpenseController.delete), methods=['POST'])
