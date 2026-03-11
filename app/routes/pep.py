"""PEP (Project Execution Plan) routes."""
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models.project import Project
from app.models.user import User
from app.models.pep import (
    PEPPhase, PEPStage, PEPActivity, PEPActivityLog,
    PEPRisk, PEPRiskLog,
    PEPResourceAllocation, PEPResourceCapacity,
    PEPBaseline, PEPVariation,
    PEPDecisionLog, PEPChangeLog, PEPComment,
)
from app.utils.pep_charts import (
    build_gantt_chart,
    build_scurve_chart,
    build_risk_matrix_chart,
    cache_invalidate_project,
)

pep_bp = Blueprint('pep', __name__, url_prefix='/projects/<int:project_id>/pep')


def _get_project_or_404(project_id: int) -> Project:
    """Return the project or abort with 404."""
    return Project.query.get_or_404(project_id)


def _parse_date(date_str):
    """Parse a date string YYYY-MM-DD into a date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _log_change(project_id: int, entity_type: str, description: str) -> None:
    """Insert a PEPChangeLog entry and invalidate dashboard chart cache."""
    entry = PEPChangeLog(
        project_id=project_id,
        entity_type=entity_type,
        change_description=description,
        created_by=current_user.id,
    )
    db.session.add(entry)
    cache_invalidate_project(project_id)


# ---------------------------------------------------------------------------
# PEP Dashboard
# ---------------------------------------------------------------------------

def _get_gantt_data(phases):
    """Build Gantt chart task list from phases and stages."""
    tasks = []
    today_str = date.today().isoformat()

    for phase in phases:
        start = phase.start_date.isoformat() if phase.start_date else today_str
        end = phase.end_date.isoformat() if phase.end_date else today_str

        if end < start:
            end = start

        tasks.append({
            'id': f'phase_{phase.id}',
            'name': phase.name,
            'start': start,
            'end': end,
            'progress': _phase_progress(phase),
            'dependencies': '',
            'custom_class': f'phase-level status-{phase.status}',
        })

        for stage in phase.stages.all():
            s_start = stage.start_date.isoformat() if stage.start_date else start
            s_end = stage.end_date.isoformat() if stage.end_date else end

            if s_end < s_start:
                s_end = s_start

            tasks.append({
                'id': f'stage_{stage.id}',
                'name': f'  {stage.name}',
                'start': s_start,
                'end': s_end,
                'progress': _stage_progress(stage),
                'dependencies': f'phase_{phase.id}',
                'custom_class': f'stage-level status-{stage.status}',
            })

    return tasks


def _phase_progress(phase) -> int:
    """Calculate average progress of activities in a phase (0-100)."""
    total = 0
    total_progress = 0
    for stage in phase.stages.all():
        for act in stage.activities.all():
            total += 1
            total_progress += act.progress or 0
    return int(total_progress / total) if total else 0


def _stage_progress(stage) -> int:
    """Calculate average progress of activities in a stage (0-100)."""
    activities = stage.activities.all()
    if not activities:
        return 0
    return int(sum(a.progress or 0 for a in activities) / len(activities))


def _get_scurve_data(phases, project):
    """Calculate S-curve data (planned vs actual) for the project.

    Returns a dict with keys: periods, planned, actual, labels.
    Uses weekly periods for projects <= 90 days, monthly otherwise.
    """
    activities = []
    for phase in phases:
        for stage in phase.stages.all():
            for act in stage.activities.all():
                if act.start_date and act.end_date and act.duration_hours:
                    activities.append(act)

    if not activities:
        return {'periods': [], 'planned': [], 'actual': [], 'labels': []}

    proj_start = min(a.start_date for a in activities)
    proj_end = max(a.end_date for a in activities)

    if hasattr(project, 'start_date') and project.start_date:
        proj_start = min(proj_start, project.start_date)
    if hasattr(project, 'end_date') and project.end_date:
        proj_end = max(proj_end, project.end_date)

    duration_days = (proj_end - proj_start).days or 1

    if duration_days > 90:
        period_days = 30
        label_fmt = 'Mês {n}'
    else:
        period_days = 7
        label_fmt = 'Sem. {n}'

    periods = []
    cursor = proj_start
    while cursor <= proj_end:
        periods.append(cursor)
        cursor += timedelta(days=period_days)
    if not periods or periods[-1] < proj_end:
        periods.append(proj_end)

    total_hours = sum(float(a.duration_hours) for a in activities)
    if total_hours == 0:
        return {'periods': [], 'planned': [], 'actual': [], 'labels': []}

    planned_data = []
    actual_data = []
    labels = []

    for n, period_end in enumerate(periods, 1):
        cum_planned = 0.0
        cum_actual = 0.0
        for act in activities:
            hours = float(act.duration_hours)
            act_duration = (act.end_date - act.start_date).days or 1

            if act.start_date <= period_end:
                planned_end = min(act.end_date, period_end)
                overlap_days = max((planned_end - act.start_date).days, 0)
                planned_completion_ratio = min(overlap_days / act_duration, 1.0)
                cum_planned += hours * planned_completion_ratio

            earned = hours * ((act.progress or 0) / 100.0)
            if act.end_date <= period_end:
                cum_actual += earned
            elif act.start_date <= period_end:
                elapsed = (period_end - act.start_date).days
                actual_completion_ratio = min(elapsed / act_duration, 1.0)
                cum_actual += earned * actual_completion_ratio

        planned_data.append(round(cum_planned / total_hours * 100, 1))
        actual_data.append(round(cum_actual / total_hours * 100, 1))
        labels.append(label_fmt.format(n=n))

    return {
        'periods': [p.isoformat() for p in periods],
        'planned': planned_data,
        'actual': actual_data,
        'labels': labels,
    }




@pep_bp.route('/')
@login_required
def dashboard(project_id: int):
    """Main PEP dashboard."""
    project = _get_project_or_404(project_id)

    phases = PEPPhase.query.filter_by(project_id=project_id).order_by(PEPPhase.sequence).all()
    risks = PEPRisk.query.filter_by(project_id=project_id).all()
    baselines = PEPBaseline.query.filter_by(project_id=project_id).order_by(
        PEPBaseline.baseline_date.desc()
    ).all()
    recent_changes = (
        PEPChangeLog.query.filter_by(project_id=project_id)
        .order_by(PEPChangeLog.created_at.desc())
        .limit(10)
        .all()
    )

    # Summary stats
    total_activities = 0
    completed_activities = 0
    for phase in phases:
        for stage in phase.stages:
            for activity in stage.activities:
                total_activities += 1
                if activity.status == 'completed':
                    completed_activities += 1

    overall_progress = (
        int(completed_activities / total_activities * 100) if total_activities else 0
    )

    risk_counts = {'green': 0, 'yellow': 0, 'red': 0}
    for risk in risks:
        risk_counts[risk.risk_color] += 1

    # Resource utilisation summary
    all_allocations = (
        db.session.query(PEPResourceAllocation)
        .join(PEPActivity, PEPResourceAllocation.activity_id == PEPActivity.id)
        .join(PEPStage, PEPActivity.stage_id == PEPStage.id)
        .join(PEPPhase, PEPStage.phase_id == PEPPhase.id)
        .filter(PEPPhase.project_id == project_id)
        .all()
    )
    total_allocated_hours = sum(float(a.allocated_hours or 0) for a in all_allocations)

    # Gantt and S-curve data (pre-computed for template)
    gantt_tasks = _get_gantt_data(phases)
    scurve_data = _get_scurve_data(phases, project)

    # Plotly interactive chart JSON (cached per project)
    gantt_json = build_gantt_chart(phases, project_id=project_id)
    scurve_json = build_scurve_chart(scurve_data, project_id=project_id)
    risk_matrix_json = build_risk_matrix_chart(risks, project_id=project_id)

    return render_template(
        'pep/dashboard.html',
        project=project,
        phases=phases,
        risks=risks,
        baselines=baselines,
        recent_changes=recent_changes,
        overall_progress=overall_progress,
        total_activities=total_activities,
        completed_activities=completed_activities,
        risk_counts=risk_counts,
        total_allocated_hours=total_allocated_hours,
        gantt_tasks=gantt_tasks,
        scurve_data=scurve_data,
        gantt_json=gantt_json,
        scurve_json=scurve_json,
        risk_matrix_json=risk_matrix_json,
    )


# ---------------------------------------------------------------------------
# Dashboard charts endpoint (JSON)
# ---------------------------------------------------------------------------

_VALID_CHART_TYPES = {'gantt', 'scurve', 'risk_matrix'}


@pep_bp.route('/dashboard/charts/<chart_type>')
@login_required
def dashboard_chart(project_id: int, chart_type: str):
    """Return a Plotly chart figure as JSON for the given *chart_type*.

    Supported values for ``chart_type``:
    - ``gantt``       – Gantt chart (fases e etapas)
    - ``scurve``      – Curva S (progresso acumulado)
    - ``risk_matrix`` – Matriz de Riscos (probabilidade × impacto)

    Query parameters:
        refresh (bool): pass ``?refresh=1`` to bypass the cache.

    Returns:
        JSON response ``{"data": [...], "layout": {...}}`` on success,
        or ``{"error": "..."}`` with an appropriate HTTP status code.
    """
    if chart_type not in _VALID_CHART_TYPES:
        abort(400, description=f"Tipo de gráfico inválido: {chart_type!r}. "
                               f"Opções: {sorted(_VALID_CHART_TYPES)}")

    project = _get_project_or_404(project_id)
    phases = PEPPhase.query.filter_by(project_id=project_id).order_by(PEPPhase.sequence).all()

    # Allow callers to force cache refresh
    if request.args.get('refresh'):
        cache_invalidate_project(project_id)

    if chart_type == 'gantt':
        json_str = build_gantt_chart(phases, project_id=project_id)
    elif chart_type == 'scurve':
        scurve_data = _get_scurve_data(phases, project)
        json_str = build_scurve_chart(scurve_data, project_id=project_id)
    else:  # risk_matrix
        risks = PEPRisk.query.filter_by(project_id=project_id).all()
        json_str = build_risk_matrix_chart(risks, project_id=project_id)

    if json_str is None:
        return jsonify({'error': 'Dados insuficientes para gerar o gráfico.'}), 404

    import json as _json
    return jsonify(_json.loads(json_str))


# ---------------------------------------------------------------------------
# EAP (Estrutura Analítica do Projeto)
# ---------------------------------------------------------------------------

@pep_bp.route('/eap')
@login_required
def eap(project_id: int):
    """EAP management page."""
    project = _get_project_or_404(project_id)
    phases = PEPPhase.query.filter_by(project_id=project_id).order_by(PEPPhase.sequence).all()
    users = User.query.order_by(User.full_name).all()
    return render_template('pep/eap.html', project=project, phases=phases, users=users)


# ---- Phase CRUD ----

@pep_bp.route('/eap/phases/new', methods=['GET', 'POST'])
@login_required
def create_phase(project_id: int):
    """Create a new EAP phase."""
    project = _get_project_or_404(project_id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Nome da fase é obrigatório.', 'error')
            return redirect(url_for('pep.eap', project_id=project_id))

        phase = PEPPhase(
            project_id=project_id,
            name=name,
            description=request.form.get('description', '').strip() or None,
            start_date=_parse_date(request.form.get('start_date')),
            end_date=_parse_date(request.form.get('end_date')),
            status=request.form.get('status', 'pending'),
            sequence=int(request.form.get('sequence', 0) or 0),
        )
        db.session.add(phase)
        _log_change(project_id, 'phase', f'Fase criada: {name}')
        db.session.commit()
        flash('Fase criada com sucesso.', 'success')
        return redirect(url_for('pep.eap', project_id=project_id))

    return render_template('pep/phase_form.html', project=project, phase=None)


@pep_bp.route('/eap/phases/<int:phase_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_phase(project_id: int, phase_id: int):
    """Edit an EAP phase."""
    project = _get_project_or_404(project_id)
    phase = PEPPhase.query.get_or_404(phase_id)
    if request.method == 'POST':
        phase.name = request.form.get('name', phase.name).strip()
        phase.description = request.form.get('description', '').strip() or None
        phase.start_date = _parse_date(request.form.get('start_date'))
        phase.end_date = _parse_date(request.form.get('end_date'))
        phase.status = request.form.get('status', phase.status)
        phase.sequence = int(request.form.get('sequence', phase.sequence) or 0)
        _log_change(project_id, 'phase', f'Fase editada: {phase.name}')
        db.session.commit()
        flash('Fase atualizada com sucesso.', 'success')
        return redirect(url_for('pep.eap', project_id=project_id))

    return render_template('pep/phase_form.html', project=project, phase=phase)


@pep_bp.route('/eap/phases/<int:phase_id>/delete', methods=['POST'])
@login_required
def delete_phase(project_id: int, phase_id: int):
    """Delete an EAP phase."""
    _get_project_or_404(project_id)
    phase = PEPPhase.query.get_or_404(phase_id)
    _log_change(project_id, 'phase', f'Fase removida: {phase.name}')
    db.session.delete(phase)
    db.session.commit()
    flash('Fase removida.', 'success')
    return redirect(url_for('pep.eap', project_id=project_id))


# ---- Stage CRUD ----

@pep_bp.route('/eap/phases/<int:phase_id>/stages/new', methods=['GET', 'POST'])
@login_required
def create_stage(project_id: int, phase_id: int):
    """Create a new EAP stage inside a phase."""
    project = _get_project_or_404(project_id)
    phase = PEPPhase.query.get_or_404(phase_id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Nome da etapa é obrigatório.', 'error')
            return redirect(url_for('pep.eap', project_id=project_id))

        stage = PEPStage(
            phase_id=phase_id,
            name=name,
            description=request.form.get('description', '').strip() or None,
            start_date=_parse_date(request.form.get('start_date')),
            end_date=_parse_date(request.form.get('end_date')),
            status=request.form.get('status', 'pending'),
            sequence=int(request.form.get('sequence', 0) or 0),
        )
        db.session.add(stage)
        _log_change(project_id, 'stage', f'Etapa criada: {name} (fase: {phase.name})')
        db.session.commit()
        flash('Etapa criada com sucesso.', 'success')
        return redirect(url_for('pep.eap', project_id=project_id))

    return render_template('pep/stage_form.html', project=project, phase=phase, stage=None)


@pep_bp.route('/eap/stages/<int:stage_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_stage(project_id: int, stage_id: int):
    """Edit an EAP stage."""
    project = _get_project_or_404(project_id)
    stage = PEPStage.query.get_or_404(stage_id)
    phase = stage.phase
    if request.method == 'POST':
        stage.name = request.form.get('name', stage.name).strip()
        stage.description = request.form.get('description', '').strip() or None
        stage.start_date = _parse_date(request.form.get('start_date'))
        stage.end_date = _parse_date(request.form.get('end_date'))
        stage.status = request.form.get('status', stage.status)
        stage.sequence = int(request.form.get('sequence', stage.sequence) or 0)
        _log_change(project_id, 'stage', f'Etapa editada: {stage.name}')
        db.session.commit()
        flash('Etapa atualizada com sucesso.', 'success')
        return redirect(url_for('pep.eap', project_id=project_id))

    return render_template('pep/stage_form.html', project=project, phase=phase, stage=stage)


@pep_bp.route('/eap/stages/<int:stage_id>/delete', methods=['POST'])
@login_required
def delete_stage(project_id: int, stage_id: int):
    """Delete an EAP stage."""
    _get_project_or_404(project_id)
    stage = PEPStage.query.get_or_404(stage_id)
    _log_change(project_id, 'stage', f'Etapa removida: {stage.name}')
    db.session.delete(stage)
    db.session.commit()
    flash('Etapa removida.', 'success')
    return redirect(url_for('pep.eap', project_id=project_id))


# ---- Activity CRUD ----

@pep_bp.route('/eap/stages/<int:stage_id>/activities/new', methods=['GET', 'POST'])
@login_required
def create_activity(project_id: int, stage_id: int):
    """Create a new activity inside a stage."""
    project = _get_project_or_404(project_id)
    stage = PEPStage.query.get_or_404(stage_id)
    users = User.query.order_by(User.full_name).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Nome da atividade é obrigatório.', 'error')
            return redirect(url_for('pep.eap', project_id=project_id))

        resp_raw = request.form.get('responsible_user_id')
        responsible_user_id = int(resp_raw) if resp_raw else None
        dur_raw = request.form.get('duration_hours')
        duration_hours = float(dur_raw) if dur_raw else None

        activity = PEPActivity(
            stage_id=stage_id,
            name=name,
            description=request.form.get('description', '').strip() or None,
            duration_hours=duration_hours,
            responsible_user_id=responsible_user_id,
            status=request.form.get('status', 'pending'),
            progress=int(request.form.get('progress', 0) or 0),
            dependencies=request.form.get('dependencies', '').strip() or None,
            start_date=_parse_date(request.form.get('start_date')),
            end_date=_parse_date(request.form.get('end_date')),
        )
        db.session.add(activity)
        _log_change(project_id, 'activity', f'Atividade criada: {name} (etapa: {stage.name})')
        db.session.commit()
        flash('Atividade criada com sucesso.', 'success')
        return redirect(url_for('pep.eap', project_id=project_id))

    return render_template(
        'pep/activity_form.html', project=project, stage=stage, activity=None, users=users
    )


@pep_bp.route('/eap/activities/<int:activity_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_activity(project_id: int, activity_id: int):
    """Edit a PEP activity."""
    project = _get_project_or_404(project_id)
    activity = PEPActivity.query.get_or_404(activity_id)
    stage = activity.stage
    users = User.query.order_by(User.full_name).all()

    if request.method == 'POST':
        old_status = activity.status
        activity.name = request.form.get('name', activity.name).strip()
        activity.description = request.form.get('description', '').strip() or None
        resp_raw = request.form.get('responsible_user_id')
        activity.responsible_user_id = int(resp_raw) if resp_raw else None
        dur_raw = request.form.get('duration_hours')
        activity.duration_hours = float(dur_raw) if dur_raw else None
        activity.status = request.form.get('status', activity.status)
        activity.progress = int(request.form.get('progress', activity.progress) or 0)
        activity.dependencies = request.form.get('dependencies', '').strip() or None
        activity.start_date = _parse_date(request.form.get('start_date'))
        activity.end_date = _parse_date(request.form.get('end_date'))

        if old_status != activity.status:
            log_entry = PEPActivityLog(
                activity_id=activity_id,
                change_description=f'Status alterado: {old_status} → {activity.status}',
                created_by=current_user.id,
            )
            db.session.add(log_entry)

        _log_change(project_id, 'activity', f'Atividade editada: {activity.name}')
        db.session.commit()
        flash('Atividade atualizada com sucesso.', 'success')
        return redirect(url_for('pep.eap', project_id=project_id))

    return render_template(
        'pep/activity_form.html', project=project, stage=stage, activity=activity, users=users
    )


@pep_bp.route('/eap/activities/<int:activity_id>/delete', methods=['POST'])
@login_required
def delete_activity(project_id: int, activity_id: int):
    """Delete a PEP activity."""
    _get_project_or_404(project_id)
    activity = PEPActivity.query.get_or_404(activity_id)
    _log_change(project_id, 'activity', f'Atividade removida: {activity.name}')
    db.session.delete(activity)
    db.session.commit()
    flash('Atividade removida.', 'success')
    return redirect(url_for('pep.eap', project_id=project_id))


# ---------------------------------------------------------------------------
# Risk Management
# ---------------------------------------------------------------------------

@pep_bp.route('/risks')
@login_required
def risks(project_id: int):
    """Risk management page."""
    project = _get_project_or_404(project_id)
    all_risks = PEPRisk.query.filter_by(project_id=project_id).order_by(
        (PEPRisk.probability * PEPRisk.impact).desc()
    ).all()
    users = User.query.order_by(User.full_name).all()

    # Build matrix: rows = probability 5→1, cols = impact 1→5
    matrix = {}
    for p in range(1, 6):
        for i in range(1, 6):
            matrix[(p, i)] = []
    for risk in all_risks:
        key = (risk.probability, risk.impact)
        if key in matrix:
            matrix[key].append(risk)

    return render_template(
        'pep/risks.html',
        project=project,
        risks=all_risks,
        matrix=matrix,
        users=users,
    )


@pep_bp.route('/risks/new', methods=['GET', 'POST'])
@login_required
def create_risk(project_id: int):
    """Create a new risk."""
    project = _get_project_or_404(project_id)
    users = User.query.order_by(User.full_name).all()

    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        if not description:
            flash('Descrição do risco é obrigatória.', 'error')
            return redirect(url_for('pep.risks', project_id=project_id))

        prob = int(request.form.get('probability', 1))
        imp = int(request.form.get('impact', 1))
        owner_raw = request.form.get('owner_id')

        risk = PEPRisk(
            project_id=project_id,
            description=description,
            probability=max(1, min(5, prob)),
            impact=max(1, min(5, imp)),
            status=request.form.get('status', 'identified'),
            mitigation_plan=request.form.get('mitigation_plan', '').strip() or None,
            owner_id=int(owner_raw) if owner_raw else None,
        )
        db.session.add(risk)
        _log_change(project_id, 'risk', f'Risco criado: {description[:60]}')
        db.session.commit()
        flash('Risco cadastrado com sucesso.', 'success')
        return redirect(url_for('pep.risks', project_id=project_id))

    return render_template('pep/risk_form.html', project=project, risk=None, users=users)


@pep_bp.route('/risks/<int:risk_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_risk(project_id: int, risk_id: int):
    """Edit a risk."""
    project = _get_project_or_404(project_id)
    risk = PEPRisk.query.get_or_404(risk_id)
    users = User.query.order_by(User.full_name).all()

    if request.method == 'POST':
        old_prob = risk.probability
        old_imp = risk.impact
        risk.description = request.form.get('description', risk.description).strip()
        risk.probability = max(1, min(5, int(request.form.get('probability', risk.probability))))
        risk.impact = max(1, min(5, int(request.form.get('impact', risk.impact))))
        risk.status = request.form.get('status', risk.status)
        risk.mitigation_plan = request.form.get('mitigation_plan', '').strip() or None
        owner_raw = request.form.get('owner_id')
        risk.owner_id = int(owner_raw) if owner_raw else None

        if old_prob != risk.probability or old_imp != risk.impact:
            log_entry = PEPRiskLog(
                risk_id=risk_id,
                change_description=(
                    f'Nível alterado: P{old_prob}×I{old_imp} → P{risk.probability}×I{risk.impact}'
                ),
                created_by=current_user.id,
            )
            db.session.add(log_entry)

        _log_change(project_id, 'risk', f'Risco editado: {risk.description[:60]}')
        db.session.commit()
        flash('Risco atualizado com sucesso.', 'success')
        return redirect(url_for('pep.risks', project_id=project_id))

    return render_template('pep/risk_form.html', project=project, risk=risk, users=users)


@pep_bp.route('/risks/<int:risk_id>/delete', methods=['POST'])
@login_required
def delete_risk(project_id: int, risk_id: int):
    """Delete a risk."""
    _get_project_or_404(project_id)
    risk = PEPRisk.query.get_or_404(risk_id)
    _log_change(project_id, 'risk', f'Risco removido: {risk.description[:60]}')
    db.session.delete(risk)
    db.session.commit()
    flash('Risco removido.', 'success')
    return redirect(url_for('pep.risks', project_id=project_id))


# ---------------------------------------------------------------------------
# Resource Allocation
# ---------------------------------------------------------------------------

@pep_bp.route('/resources')
@login_required
def resources(project_id: int):
    """Resource allocation page."""
    project = _get_project_or_404(project_id)
    users = User.query.order_by(User.full_name).all()

    # Gather all allocations for this project
    allocations = (
        db.session.query(PEPResourceAllocation)
        .join(PEPActivity, PEPResourceAllocation.activity_id == PEPActivity.id)
        .join(PEPStage, PEPActivity.stage_id == PEPStage.id)
        .join(PEPPhase, PEPStage.phase_id == PEPPhase.id)
        .filter(PEPPhase.project_id == project_id)
        .all()
    )

    capacities = PEPResourceCapacity.query.filter(
        PEPResourceCapacity.user_id.in_([u.id for u in users])
    ).all()

    # Allocation summary per user
    user_hours = {}
    for alloc in allocations:
        user_hours[alloc.user_id] = user_hours.get(alloc.user_id, 0) + float(
            alloc.allocated_hours or 0
        )

    phases = PEPPhase.query.filter_by(project_id=project_id).order_by(PEPPhase.sequence).all()

    return render_template(
        'pep/resources.html',
        project=project,
        users=users,
        allocations=allocations,
        capacities=capacities,
        user_hours=user_hours,
        phases=phases,
    )


@pep_bp.route('/resources/allocations/new', methods=['GET', 'POST'])
@login_required
def create_allocation(project_id: int):
    """Create a new resource allocation."""
    project = _get_project_or_404(project_id)
    users = User.query.order_by(User.full_name).all()
    phases = PEPPhase.query.filter_by(project_id=project_id).order_by(PEPPhase.sequence).all()

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        activity_id = request.form.get('activity_id')
        hours_raw = request.form.get('allocated_hours')

        if not user_id or not activity_id or not hours_raw:
            flash('Usuário, atividade e horas são obrigatórios.', 'error')
            return redirect(url_for('pep.resources', project_id=project_id))

        allocation = PEPResourceAllocation(
            activity_id=int(activity_id),
            user_id=int(user_id),
            allocated_hours=float(hours_raw),
            start_date=_parse_date(request.form.get('start_date')),
            end_date=_parse_date(request.form.get('end_date')),
        )
        db.session.add(allocation)
        _log_change(project_id, 'resource_allocation', f'Alocação criada para usuário {user_id}')
        db.session.commit()
        flash('Alocação criada com sucesso.', 'success')
        return redirect(url_for('pep.resources', project_id=project_id))

    return render_template(
        'pep/allocation_form.html',
        project=project,
        allocation=None,
        users=users,
        phases=phases,
    )


@pep_bp.route('/resources/allocations/<int:allocation_id>/delete', methods=['POST'])
@login_required
def delete_allocation(project_id: int, allocation_id: int):
    """Delete a resource allocation."""
    _get_project_or_404(project_id)
    allocation = PEPResourceAllocation.query.get_or_404(allocation_id)
    _log_change(project_id, 'resource_allocation', f'Alocação removida (id={allocation_id})')
    db.session.delete(allocation)
    db.session.commit()
    flash('Alocação removida.', 'success')
    return redirect(url_for('pep.resources', project_id=project_id))


@pep_bp.route('/resources/capacity/new', methods=['GET', 'POST'])
@login_required
def create_capacity(project_id: int):
    """Create/update resource capacity for a team member."""
    project = _get_project_or_404(project_id)
    users = User.query.order_by(User.full_name).all()

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        hours_raw = request.form.get('available_hours_per_day')
        start_raw = request.form.get('start_date')
        end_raw = request.form.get('end_date')

        if not user_id or not hours_raw or not start_raw or not end_raw:
            flash('Todos os campos de capacidade são obrigatórios.', 'error')
            return redirect(url_for('pep.resources', project_id=project_id))

        capacity = PEPResourceCapacity(
            user_id=int(user_id),
            available_hours_per_day=float(hours_raw),
            start_date=_parse_date(start_raw),
            end_date=_parse_date(end_raw),
        )
        db.session.add(capacity)
        db.session.commit()
        flash('Capacidade registrada com sucesso.', 'success')
        return redirect(url_for('pep.resources', project_id=project_id))

    return render_template(
        'pep/capacity_form.html', project=project, users=users
    )


# ---------------------------------------------------------------------------
# Baseline & Monitoring
# ---------------------------------------------------------------------------

@pep_bp.route('/baseline')
@login_required
def baseline(project_id: int):
    """Baseline management page."""
    project = _get_project_or_404(project_id)
    baselines = PEPBaseline.query.filter_by(project_id=project_id).order_by(
        PEPBaseline.baseline_date.desc()
    ).all()
    return render_template('pep/baseline.html', project=project, baselines=baselines)


@pep_bp.route('/baseline/new', methods=['GET', 'POST'])
@login_required
def create_baseline(project_id: int):
    """Create a new baseline snapshot."""
    project = _get_project_or_404(project_id)

    if request.method == 'POST':
        name = request.form.get('name', 'Baseline').strip()
        date_raw = request.form.get('baseline_date')
        if not date_raw:
            flash('Data do baseline é obrigatória.', 'error')
            return redirect(url_for('pep.baseline', project_id=project_id))

        cost_raw = request.form.get('total_cost')
        dur_raw = request.form.get('total_duration')

        bl = PEPBaseline(
            project_id=project_id,
            name=name,
            total_cost=float(cost_raw) if cost_raw else None,
            total_duration=int(dur_raw) if dur_raw else None,
            baseline_date=_parse_date(date_raw),
            status='active',
            created_by=current_user.id,
        )
        db.session.add(bl)
        _log_change(project_id, 'baseline', f'Baseline criado: {name}')
        db.session.commit()
        flash('Baseline criado com sucesso.', 'success')
        return redirect(url_for('pep.baseline', project_id=project_id))

    return render_template('pep/baseline_form.html', project=project, baseline_obj=None)


@pep_bp.route('/baseline/<int:baseline_id>/lock', methods=['POST'])
@login_required
def lock_baseline(project_id: int, baseline_id: int):
    """Lock a baseline to prevent further changes."""
    _get_project_or_404(project_id)
    bl = PEPBaseline.query.get_or_404(baseline_id)
    bl.status = 'locked'
    _log_change(project_id, 'baseline', f'Baseline bloqueado: {bl.name}')
    db.session.commit()
    flash('Baseline bloqueado.', 'success')
    return redirect(url_for('pep.baseline', project_id=project_id))


@pep_bp.route('/baseline/<int:baseline_id>/delete', methods=['POST'])
@login_required
def delete_baseline(project_id: int, baseline_id: int):
    """Delete a baseline (only if not locked)."""
    _get_project_or_404(project_id)
    bl = PEPBaseline.query.get_or_404(baseline_id)
    if bl.is_locked:
        flash('Não é possível remover um baseline bloqueado.', 'error')
        return redirect(url_for('pep.baseline', project_id=project_id))
    _log_change(project_id, 'baseline', f'Baseline removido: {bl.name}')
    db.session.delete(bl)
    db.session.commit()
    flash('Baseline removido.', 'success')
    return redirect(url_for('pep.baseline', project_id=project_id))


# ---------------------------------------------------------------------------
# Documentation & History
# ---------------------------------------------------------------------------

@pep_bp.route('/documentation')
@login_required
def documentation(project_id: int):
    """Documentation center page."""
    project = _get_project_or_404(project_id)
    decision_logs = PEPDecisionLog.query.filter_by(project_id=project_id).order_by(
        PEPDecisionLog.created_at.desc()
    ).all()
    change_logs = PEPChangeLog.query.filter_by(project_id=project_id).order_by(
        PEPChangeLog.created_at.desc()
    ).all()
    users = User.query.order_by(User.full_name).all()
    return render_template(
        'pep/documentation.html',
        project=project,
        decision_logs=decision_logs,
        change_logs=change_logs,
        users=users,
    )


@pep_bp.route('/documentation/decisions/new', methods=['GET', 'POST'])
@login_required
def create_decision(project_id: int):
    """Register a new project decision."""
    project = _get_project_or_404(project_id)
    users = User.query.order_by(User.full_name).all()

    if request.method == 'POST':
        decision = request.form.get('decision', '').strip()
        if not decision:
            flash('Decisão é obrigatória.', 'error')
            return redirect(url_for('pep.documentation', project_id=project_id))

        owner_raw = request.form.get('owner_id')
        entry = PEPDecisionLog(
            project_id=project_id,
            decision=decision,
            justification=request.form.get('justification', '').strip() or None,
            owner_id=int(owner_raw) if owner_raw else None,
            created_by=current_user.id,
        )
        db.session.add(entry)
        _log_change(project_id, 'decision', f'Decisão registrada: {decision[:60]}')
        db.session.commit()
        flash('Decisão registrada com sucesso.', 'success')
        return redirect(url_for('pep.documentation', project_id=project_id))

    return render_template('pep/decision_form.html', project=project, users=users)


@pep_bp.route('/documentation/decisions/<int:decision_id>/delete', methods=['POST'])
@login_required
def delete_decision(project_id: int, decision_id: int):
    """Delete a decision log entry."""
    _get_project_or_404(project_id)
    entry = PEPDecisionLog.query.get_or_404(decision_id)
    db.session.delete(entry)
    _log_change(project_id, 'decision', f'Decisão removida (id={decision_id})')
    db.session.commit()
    flash('Decisão removida.', 'success')
    return redirect(url_for('pep.documentation', project_id=project_id))

# ---------------------------------------------------------------------------
# API endpoints (JSON) for dashboard data
# ---------------------------------------------------------------------------

@pep_bp.route('/api/progress')
@login_required
def api_progress(project_id: int):
    """Return S-curve progress data (planned vs actual) as JSON."""
    project = _get_project_or_404(project_id)
    phases = PEPPhase.query.filter_by(project_id=project_id).order_by(PEPPhase.sequence).all()
    data = _get_scurve_data(phases, project)
    return jsonify(data)


@pep_bp.route('/api/gantt')
@login_required
def api_gantt(project_id: int):
    """Return Gantt chart task data as JSON."""
    _get_project_or_404(project_id)
    phases = PEPPhase.query.filter_by(project_id=project_id).order_by(PEPPhase.sequence).all()
    return jsonify(_get_gantt_data(phases))
