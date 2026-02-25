"""Time entry (apontamentos) routes."""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.services.timeentry_service import TimeEntryService
from app.services.project_service import ProjectService
from app.models.time_entry import HOUR_TYPES

timeentry_bp = Blueprint('timeentry', __name__, url_prefix='/apontamentos')


def _parse_date(date_str):
    """Parse a date string (YYYY-MM-DD) into a date object or return None."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _parse_int(value):
    """Parse a string to int or return None."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_hours(hours_str):
    """Normalize hours from HH:MM to HH:MM:SS by appending :00 if seconds are missing."""
    if hours_str and len(hours_str) == 5 and hours_str[2] == ':':
        return hours_str + ':00'
    return hours_str


# ── Measurement Cycle routes (admin only) ─────────────────────────────────────

@timeentry_bp.route('/ciclos/')
@login_required
@admin_required
def cycles_index():
    """List all measurement cycles (admin only)."""
    cycles = TimeEntryService.get_all_cycles()
    return render_template('apontamentos/ciclos/index.html', cycles=cycles)


@timeentry_bp.route('/ciclos/new', methods=['GET', 'POST'])
@login_required
@admin_required
def cycles_create():
    """Create a new measurement cycle (admin only)."""
    if request.method == 'POST':
        start_day = _parse_int(request.form.get('start_day'))
        start_date = _parse_date(request.form.get('start_date'))
        end_date = _parse_date(request.form.get('end_date'))
        is_active = bool(request.form.get('is_active'))

        cycle, error = TimeEntryService.create_cycle(
            start_day=start_day or 0,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
            created_by=current_user.id,
        )
        if cycle:
            flash('Ciclo de medição criado com sucesso.', 'success')
            return redirect(url_for('timeentry.cycles_index'))
        flash(error, 'error')
    return render_template('apontamentos/ciclos/form.html', cycle=None)


@timeentry_bp.route('/ciclos/<int:cycle_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def cycles_edit(cycle_id: int):
    """Edit an existing measurement cycle (admin only)."""
    cycle = TimeEntryService.get_cycle(cycle_id)
    if not cycle:
        flash('Ciclo de medição não encontrado.', 'error')
        return redirect(url_for('timeentry.cycles_index'))

    if request.method == 'POST':
        start_day = _parse_int(request.form.get('start_day'))
        start_date = _parse_date(request.form.get('start_date'))
        end_date = _parse_date(request.form.get('end_date'))
        is_active = bool(request.form.get('is_active'))

        updated, error = TimeEntryService.update_cycle(cycle_id, {
            'start_day': start_day or cycle.start_day,
            'start_date': start_date or cycle.start_date,
            'end_date': end_date or cycle.end_date,
            'is_active': is_active,
        })
        if updated:
            flash('Ciclo de medição atualizado com sucesso.', 'success')
            return redirect(url_for('timeentry.cycles_index'))
        flash(error, 'error')
    return render_template('apontamentos/ciclos/form.html', cycle=cycle)


# ── Time Entry routes ──────────────────────────────────────────────────────────

@timeentry_bp.route('/')
@login_required
def index():
    """List time entries."""
    is_admin = current_user.role == 'admin'
    project_id = _parse_int(request.args.get('project_id'))
    cycle_id = _parse_int(request.args.get('cycle_id'))
    work_date = _parse_date(request.args.get('work_date'))

    entries = TimeEntryService.get_time_entries(
        user_id=current_user.id,
        is_admin=is_admin,
        project_id=project_id,
        cycle_id=cycle_id,
        work_date=work_date,
    )
    projects = ProjectService.get_user_projects(current_user.id, include_all=is_admin)
    cycles = TimeEntryService.get_all_cycles()
    active_cycle = TimeEntryService.get_active_cycle()
    return render_template(
        'apontamentos/index.html',
        entries=entries,
        projects=projects,
        cycles=cycles,
        active_cycle=active_cycle,
        selected_project_id=project_id,
        selected_cycle_id=cycle_id,
        selected_work_date=request.args.get('work_date', ''),
    )


@timeentry_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new time entry."""
    is_admin = current_user.role == 'admin'
    projects = ProjectService.get_user_projects(current_user.id, include_all=is_admin)
    active_cycle = TimeEntryService.get_active_cycle()

    if request.method == 'POST':
        work_date = _parse_date(request.form.get('work_date'))
        entry, error = TimeEntryService.create_time_entry(
            project_id=_parse_int(request.form.get('project_id')),
            user_id=current_user.id,
            main_activity=request.form.get('main_activity'),
            work_date=work_date,
            hours_worked=_normalize_hours(request.form.get('hours_worked')),
            hour_type=request.form.get('hour_type'),
            discipline=request.form.get('discipline'),
            sub_activity=request.form.get('sub_activity'),
            observation=request.form.get('observation'),
        )
        if entry:
            flash('Apontamento criado com sucesso.', 'success')
            return redirect(url_for('timeentry.index'))
        flash(error, 'error')

    return render_template(
        'apontamentos/create.html',
        projects=projects,
        active_cycle=active_cycle,
        hour_types=HOUR_TYPES,
    )


@timeentry_bp.route('/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(entry_id: int):
    """Edit an existing time entry."""
    entry = TimeEntryService.get_time_entry(entry_id)
    if not entry:
        flash('Apontamento não encontrado.', 'error')
        return redirect(url_for('timeentry.index'))

    is_admin = current_user.role == 'admin'

    # Permission check before rendering
    if not is_admin and entry.user_id != current_user.id:
        flash('Você não tem permissão para editar este apontamento.', 'error')
        return redirect(url_for('timeentry.index'))

    projects = ProjectService.get_user_projects(current_user.id, include_all=is_admin)
    active_cycle = TimeEntryService.get_active_cycle()

    # Block non-admin from editing entries whose work_date is outside the active cycle
    if not is_admin and (
        not active_cycle or
        not (active_cycle.start_date <= entry.work_date <= active_cycle.end_date)
    ):
        flash('Apenas o administrador pode editar apontamentos de ciclos anteriores.', 'error')
        return redirect(url_for('timeentry.index'))

    if request.method == 'POST':
        work_date = _parse_date(request.form.get('work_date'))
        data = {
            'project_id': _parse_int(request.form.get('project_id')),
            'discipline': request.form.get('discipline'),
            'main_activity': request.form.get('main_activity'),
            'sub_activity': request.form.get('sub_activity'),
            'work_date': work_date,
            'hours_worked': _normalize_hours(request.form.get('hours_worked')),
            'hour_type': request.form.get('hour_type'),
            'observation': request.form.get('observation'),
        }
        updated, error = TimeEntryService.update_time_entry(
            entry_id=entry_id,
            data=data,
            is_admin=is_admin,
            current_user_id=current_user.id,
        )
        if updated:
            flash('Apontamento atualizado com sucesso.', 'success')
            return redirect(url_for('timeentry.index'))
        flash(error, 'error')

    return render_template(
        'apontamentos/edit.html',
        entry=entry,
        projects=projects,
        active_cycle=active_cycle,
        hour_types=HOUR_TYPES,
    )


@timeentry_bp.route('/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete(entry_id: int):
    """Delete a time entry."""
    is_admin = current_user.role == 'admin'
    success, error = TimeEntryService.delete_time_entry(
        entry_id=entry_id,
        is_admin=is_admin,
        current_user_id=current_user.id,
    )
    if success:
        flash('Apontamento excluído com sucesso.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('timeentry.index'))
