"""Main routes including the dashboard."""
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.services.permission_service import PermissionService

main_bp = Blueprint('main', __name__)

_MONTH_NAMES_PT = [
    '', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
]

# Module definitions: order, label, description, icon, color, url endpoint, module_name
_MODULES = [
    {
        'module_name': 'projects',
        'label': 'Projetos',
        'description': 'Gerenciamento de projetos',
        'icon': 'folder',
        'color': 'blue',
        'url_endpoint': 'projects.index',
    },
    {
        'module_name': 'timeentry',
        'label': 'Apontamentos',
        'description': 'Registro de horas',
        'icon': 'clock',
        'color': 'purple',
        'url_endpoint': 'timeentry.index',
    },
]


@main_bp.route('/')
@login_required
def index():
    """Redirect root URL to dashboard."""
    return redirect(url_for('main.dashboard'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Render the main dashboard."""
    now = datetime.now()
    hour = now.hour
    if hour < 12:
        greeting = 'Bom dia'
    elif hour < 18:
        greeting = 'Boa tarde'
    else:
        greeting = 'Boa noite'

    formatted_date = f"{now.day:02d} de {_MONTH_NAMES_PT[now.month]} de {now.year}"

    is_admin = current_user.role == 'admin'

    available_modules = []
    for mod in _MODULES:
        has_access = is_admin or PermissionService.has_module_access(
            current_user.id, mod['module_name']
        )
        available_modules.append({
            'module_name': mod['module_name'],
            'label': mod['label'],
            'description': mod['description'],
            'icon': mod['icon'],
            'color': mod['color'],
            'url': url_for(mod['url_endpoint']),
            'has_access': has_access,
        })

    return render_template(
        'dashboard.html',
        greeting=greeting,
        formatted_date=formatted_date,
        available_modules=available_modules,
    )