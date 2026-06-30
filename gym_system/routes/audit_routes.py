from flask import Blueprint, render_template, request
from database.models.audit import AuditLog
from utils.security import login_required, role_required

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')
PER_PAGE = 50


@audit_bp.route('/')
@login_required
@role_required('admin')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .paginate(page=page, per_page=PER_PAGE, error_out=False)
    )
    return render_template('audit/audit.html', logs=pagination.items, pagination=pagination)
