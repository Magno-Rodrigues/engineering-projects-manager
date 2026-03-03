"""Import routes — upload, preview, confirm and history endpoints."""
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required

from app.models.project import Project
from app.services.import_service import ImportService

import_bp = Blueprint('import', __name__, url_prefix='/projects')

_ALLOWED_EXTENSIONS = {'xml', 'xls', 'xlsx'}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


def _allowed(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in _ALLOWED_EXTENSIONS


def _get_project_or_abort(project_id: int):
    """Return project if current user is admin or owner, else return None."""
    project = Project.query.get(project_id)
    if project is None:
        flash('Projeto não encontrado.', 'error')
        return None
    if current_user.role != 'admin' and project.owner_id != current_user.id:
        flash('Acesso não autorizado.', 'error')
        return None
    return project


@import_bp.route('/<int:project_id>/import', methods=['GET', 'POST'])
@login_required
def index(project_id: int):
    """Upload form for MS Project / Primavera P6 files."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    if request.method == 'POST':
        import_type = request.form.get('import_type', 'ms_project')
        file = request.files.get('file')

        if not file or not file.filename:
            flash('Nenhum arquivo selecionado.', 'error')
            return redirect(url_for('import.index', project_id=project_id))

        if not _allowed(file.filename):
            flash('Tipo de arquivo não suportado. Use .xml, .xls ou .xlsx.', 'error')
            return redirect(url_for('import.index', project_id=project_id))

        content = file.read()
        if len(content) > _MAX_BYTES:
            flash('Arquivo excede o limite de 10 MB.', 'error')
            return redirect(url_for('import.index', project_id=project_id))

        data, errors = ImportService.parse_file(content, file.filename, import_type)

        if errors:
            for err in errors:
                flash(err, 'error')
            return redirect(url_for('import.index', project_id=project_id))

        # Store parsed data in session for confirmation step
        session['import_preview'] = {
            'file_name': file.filename,
            'import_type': import_type,
            'tasks': data.get('tasks', [])[:50],  # preview up to 50 tasks
            'wbs_items': data.get('wbs_items', []),
            'resources': data.get('resources', []),
            'budgets': data.get('budgets', []),
        }
        return redirect(url_for('import.preview', project_id=project_id))

    return render_template('projects/import/index.html', project=project)


@import_bp.route('/<int:project_id>/import/preview', methods=['GET', 'POST'])
@login_required
def preview(project_id: int):
    """Show parsed data before confirming import."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    preview_data = session.get('import_preview')
    if not preview_data:
        flash('Nenhum arquivo em preview. Faça o upload primeiro.', 'error')
        return redirect(url_for('import.index', project_id=project_id))

    if request.method == 'POST':
        action = request.form.get('action', 'confirm')
        if action == 'cancel':
            session.pop('import_preview', None)
            flash('Importação cancelada.', 'info')
            return redirect(url_for('import.index', project_id=project_id))

        # Re-parse to get full data (not just preview slice)
        # We rely on what's stored; for production you'd re-parse from storage.
        full_data = {k: preview_data[k] for k in ('tasks', 'wbs_items', 'resources', 'budgets')}
        log, error = ImportService.import_data(
            project_id=project_id,
            created_by=current_user.id,
            file_name=preview_data['file_name'],
            import_type=preview_data['import_type'],
            data=full_data,
        )
        session.pop('import_preview', None)
        if error:
            flash(f'Erro na importação: {error}', 'error')
        else:
            flash(
                f'Importação concluída: {log.total_tasks_imported} tarefa(s) e '
                f'{log.total_items_imported} item(s) WBS importados.',
                'success',
            )
        return redirect(url_for('import.log', project_id=project_id))

    return render_template('projects/import/preview.html', project=project, data=preview_data)


@import_bp.route('/<int:project_id>/import/log')
@login_required
def log(project_id: int):
    """Import history for a project."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    logs = ImportService.get_import_logs(project_id)
    return render_template('projects/import/log.html', project=project, logs=logs)


@import_bp.route('/<int:project_id>/import/log/<int:log_id>/rollback', methods=['POST'])
@login_required
def rollback(project_id: int, log_id: int):
    """Rollback (mark as failed) a specific import log."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    success, error = ImportService.rollback_import(log_id)
    if success:
        flash('Importação marcada como revertida.', 'success')
    else:
        flash(f'Erro ao reverter: {error}', 'error')
    return redirect(url_for('import.log', project_id=project_id))
