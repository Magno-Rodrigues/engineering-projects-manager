"""Main routes module."""
import logging
from datetime import datetime
from flask import Blueprint, redirect, url_for, render_template, jsonify
from flask_login import current_user, login_required
from app import db
from app.constants import VALID_MODULES, MODULES_METADATA
from app.services.permission_service import PermissionService
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Personalized welcome dashboard."""
    now = datetime.now()
    hour = now.hour

    if 5 <= hour < 12:
        greeting = 'Bom dia'
    elif 12 <= hour < 18:
        greeting = 'Boa tarde'
    else:
        greeting = 'Boa noite'

    months_pt = [
        'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
    ]
    formatted_date = f'{now.day} de {months_pt[now.month - 1]} de {now.year}, {now.strftime("%H:%M")}'

    is_admin = current_user.role == 'admin'
    available_modules = []
    for module_name in VALID_MODULES:
        if module_name == 'admin' and not is_admin:
            continue
        meta = MODULES_METADATA.get(module_name, {})
        if is_admin:
            has_access = True
        else:
            has_access = PermissionService.has_module_access_via_functions(current_user.id, module_name)
        route_url = None
        if has_access:
            try:
                route_url = url_for(meta.get('route_name', ''))
            except Exception:
                route_url = '#'
        available_modules.append({
            'name': module_name,
            'label': meta.get('label', module_name.capitalize()),
            'description': meta.get('description', ''),
            'color': meta.get('color', 'gray'),
            'icon': meta.get('icon', 'folder'),
            'has_access': has_access,
            'url': route_url,
        })

    return render_template(
        'dashboard.html',
        greeting=greeting,
        formatted_date=formatted_date,
        available_modules=available_modules,
    )


@main_bp.route('/close-welcome', methods=['POST'])
@login_required
def close_welcome():
    """Mark first login as complete."""
    try:
        current_user.first_login = False
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Database error in close_welcome: %s", str(e), exc_info=True)
        return jsonify({'status': 'error'}), 500
    return jsonify({'status': 'ok'})