"""Main routes module."""
from datetime import datetime
from flask import Blueprint, redirect, url_for, render_template
from flask_login import current_user, login_required

main_bp = Blueprint('main', __name__)

_MONTHS_PT = [
    '', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
]


def _get_greeting(hour: int) -> str:
    """Return a time-appropriate Portuguese greeting."""
    if hour < 12:
        return 'Bom dia'
    if hour < 18:
        return 'Boa tarde'
    return 'Boa noite'


@main_bp.route('/')
def index():
    """Home page route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
<<<<<<< HEAD
    """User dashboard with personalised welcome message."""
    now = datetime.now()
    formatted_date = f'{now.day} de {_MONTHS_PT[now.month]} de {now.year}'
    formatted_time = now.strftime('%H:%M')
    greeting = _get_greeting(now.hour)
    display_name = current_user.full_name or current_user.username
    return render_template(
        'dashboard.html',
        formatted_date=formatted_date,
        formatted_time=formatted_time,
        greeting=greeting,
        display_name=display_name,
=======
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

    from app.models.project import Project
    from app.models.task import Task
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    pending_tasks = Task.query.filter_by(status='pending').count()

    return render_template(
        'dashboard.html',
        greeting=greeting,
        formatted_date=formatted_date,
        recent_projects=recent_projects,
        pending_tasks=pending_tasks,
>>>>>>> 339a9e0aa632b01f6eb535e14e2417c96de2eec1
    )