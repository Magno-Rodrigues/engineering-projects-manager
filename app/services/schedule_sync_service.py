"""Schedule sync service — imports schedule data into EAP and provides analysis."""
from datetime import datetime, date, timezone
from typing import Any, Dict, List, Optional, Tuple

from app import db
from app.models.import_log import ImportLog
from app.models.pep import (
    PEPPhase, PEPStage, PEPActivity, PEPActivityLog, PEPChangeLog,
)
from app.models.schedule_sync import ScheduleImportRecord


class ScheduleSyncService:
    """Service for syncing imported schedule data with the PEP/EAP structure."""

    # -----------------------------------------------------------------------
    # Feature 1: Import schedule tasks to EAP
    # -----------------------------------------------------------------------

    @staticmethod
    def import_to_eap(
        project_id: int,
        import_log_id: int,
        created_by: int,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Create PEP Phase/Stage/Activity records from an import log.

        Returns (summary_dict, error_message).
        """
        import_log = db.session.get(ImportLog, import_log_id)
        if not import_log or import_log.project_id != project_id:
            return None, 'Registro de importação não encontrado.'
        if import_log.status != 'success':
            return None, 'Apenas importações bem-sucedidas podem ser importadas para o EAP.'

        records = (
            ScheduleImportRecord.query
            .filter_by(import_log_id=import_log_id, is_summary=False)
            .all()
        )
        if not records:
            return None, 'Nenhuma tarefa encontrada nesta importação.'

        try:
            # Create one Phase for the entire import
            import_type_label = (
                'MS Project' if import_log.import_type == 'ms_project' else 'Primavera P6'
            )
            file_base = import_log.file_name.rsplit('.', 1)[0] if '.' in import_log.file_name else import_log.file_name
            phase_name = f'{file_base} ({import_type_label})'

            # Determine date range
            starts = [r.actual_start for r in records if r.actual_start]
            ends = [r.actual_end for r in records if r.actual_end]
            phase_start = min(starts) if starts else None
            phase_end = max(ends) if ends else None

            phase = PEPPhase(
                project_id=project_id,
                name=phase_name[:128],
                description=f'Importado de {import_log.file_name} em {import_log.created_at.strftime("%d/%m/%Y")}',
                start_date=phase_start,
                end_date=phase_end,
                status='in_progress',
                sequence=0,
            )
            db.session.add(phase)
            db.session.flush()

            # Create a single default Stage under the Phase
            stage = PEPStage(
                phase_id=phase.id,
                name='Tarefas Importadas',
                description='Atividades importadas automaticamente do cronograma',
                start_date=phase_start,
                end_date=phase_end,
                status='in_progress',
                sequence=0,
            )
            db.session.add(stage)
            db.session.flush()

            # Create one PEPActivity per schedule record
            activities_created = 0
            for record in records:
                # Determine status from progress
                if record.progress >= 100:
                    status = 'completed'
                elif record.progress > 0:
                    status = 'in_progress'
                else:
                    status = 'pending'

                activity = PEPActivity(
                    stage_id=stage.id,
                    name=record.task_name[:128],
                    duration_hours=record.duration_hours,
                    status=status,
                    progress=record.progress,
                    start_date=record.actual_start,
                    end_date=record.actual_end,
                    external_task_id=record.external_task_id,
                    last_synced_at=datetime.now(timezone.utc),
                )
                # Calculate variance if planned dates are available
                if record.planned_end and record.actual_end:
                    variance_days = (record.actual_end - record.planned_end).days
                    if record.planned_start and record.planned_end:
                        total_planned_days = max((record.planned_end - record.planned_start).days, 1)
                        activity.variance_percentage = round(
                            variance_days / total_planned_days * 100, 2
                        )

                db.session.add(activity)
                db.session.flush()

                # Link the record back to the created activity
                record.pep_activity_id = activity.id

                # Log activity creation
                log_entry = PEPActivityLog(
                    activity_id=activity.id,
                    change_description=f'Atividade criada por importação de cronograma: {import_log.file_name}',
                    sync_source='schedule',
                    created_by=created_by,
                )
                db.session.add(log_entry)
                activities_created += 1

            # Global change log
            change_log = PEPChangeLog(
                project_id=project_id,
                entity_type='activity',
                change_description=(
                    f'Importadas {activities_created} atividades do cronograma '
                    f'"{import_log.file_name}" para o EAP'
                ),
                created_by=created_by,
            )
            db.session.add(change_log)
            db.session.commit()

            return {
                'phase_name': phase_name,
                'phase_id': phase.id,
                'stage_id': stage.id,
                'activities_created': activities_created,
                'import_file': import_log.file_name,
            }, None

        except Exception as exc:
            db.session.rollback()
            return None, str(exc)

    # -----------------------------------------------------------------------
    # Feature 1b: EAP → Schedule sync (bidirectional)
    # -----------------------------------------------------------------------

    @staticmethod
    def sync_activity_to_schedule(
        activity: PEPActivity,
        changed_by: int,
        old_status: Optional[str] = None,
        old_progress: Optional[int] = None,
    ) -> None:
        """Sync PEPActivity changes back to ScheduleImportRecord.

        Should be called after updating an activity in the EAP.
        """
        if not activity.external_task_id:
            return

        record = (
            ScheduleImportRecord.query
            .filter_by(project_id=activity.stage.phase.project_id)
            .filter_by(external_task_id=activity.external_task_id)
            .filter_by(pep_activity_id=activity.id)
            .first()
        )
        if not record:
            return

        changes = []
        if old_status is not None and old_status != activity.status:
            changes.append(f'status: {old_status} → {activity.status}')
        if old_progress is not None and old_progress != activity.progress:
            changes.append(f'progresso: {old_progress}% → {activity.progress}%')

        if not changes:
            return

        # Update the schedule record to reflect EAP changes
        if activity.progress != record.progress:
            record.progress = activity.progress

        # Log the sync
        log_entry = PEPActivityLog(
            activity_id=activity.id,
            change_description='Sincronizado EAP → Cronograma: ' + '; '.join(changes),
            old_value=str(old_status or old_progress),
            new_value=str(activity.status if old_status is not None else activity.progress),
            sync_source='eap',
            created_by=changed_by,
        )
        db.session.add(log_entry)
        activity.last_synced_at = datetime.now(timezone.utc)

    # -----------------------------------------------------------------------
    # Feature 2: Real-time Alerts
    # -----------------------------------------------------------------------

    @staticmethod
    def get_alerts(project_id: int) -> Dict[str, Any]:
        """Return alert summary for the project.

        Returns counts of adiantadas/no_prazo/atrasadas and list of critical tasks.
        """
        records = (
            ScheduleImportRecord.query
            .filter_by(project_id=project_id, is_summary=False)
            .order_by(ScheduleImportRecord.created_at.desc())
            .all()
        )

        adiantadas = []
        no_prazo = []
        atrasadas = []
        today = date.today()

        for record in records:
            status = record.schedule_status
            days_overdue = 0
            if record.actual_end and record.planned_end:
                days_overdue = (record.actual_end - record.planned_end).days
            elif record.actual_end and record.actual_end < today and record.progress < 100:
                days_overdue = (today - record.actual_end).days

            item = {
                'id': record.id,
                'task_name': record.task_name,
                'planned_end': record.planned_end.isoformat() if record.planned_end else None,
                'actual_end': record.actual_end.isoformat() if record.actual_end else None,
                'progress': record.progress,
                'days_overdue': days_overdue,
                'pep_activity_id': record.pep_activity_id,
                'suggestion': build_suggestion(record, days_overdue),
            }

            if status == 'adiantada':
                adiantadas.append(item)
            elif status == 'atrasada':
                atrasadas.append(item)
            else:
                no_prazo.append(item)

        # Sort atrasadas by severity (most overdue first)
        atrasadas.sort(key=lambda x: x['days_overdue'], reverse=True)

        return {
            'adiantadas': adiantadas,
            'no_prazo': no_prazo,
            'atrasadas': atrasadas,
            'total': len(records),
            'count_adiantadas': len(adiantadas),
            'count_no_prazo': len(no_prazo),
            'count_atrasadas': len(atrasadas),
        }

    # -----------------------------------------------------------------------
    # Feature 3: Variance Analysis
    # -----------------------------------------------------------------------

    @staticmethod
    def get_variance_analysis(project_id: int) -> Dict[str, Any]:
        """Calculate variance analysis data for the project.

        Returns: SPI, variance by severity, monthly trend.
        """
        records = (
            ScheduleImportRecord.query
            .filter_by(project_id=project_id, is_summary=False)
            .all()
        )

        if not records:
            return {
                'spi': None,
                'tasks_by_severity': {'critical': [], 'moderate': [], 'minor': [], 'on_track': []},
                'monthly_trend': [],
                'total_tasks': 0,
                'avg_variance_pct': 0.0,
            }

        tasks_with_variance = []
        total_planned_days = 0
        total_actual_days = 0

        severity_groups: Dict[str, List[Dict]] = {
            'critical': [],   # variance > 20%
            'moderate': [],   # 10% < variance <= 20%
            'minor': [],      # 0% < variance <= 10%
            'on_track': [],   # variance <= 0%
        }

        monthly_data: Dict[str, Dict[str, float]] = {}

        for record in records:
            if not (record.planned_start and record.planned_end):
                continue

            planned_duration = max((record.planned_end - record.planned_start).days, 1)
            actual_duration = None
            variance_pct = 0.0

            if record.actual_start and record.actual_end:
                actual_duration = max((record.actual_end - record.actual_start).days, 1)
                variance_days = (record.actual_end - record.planned_end).days
                variance_pct = round(variance_days / planned_duration * 100, 2)
                total_planned_days += planned_duration
                total_actual_days += actual_duration

            item = {
                'id': record.id,
                'task_name': record.task_name,
                'planned_start': record.planned_start.isoformat() if record.planned_start else None,
                'planned_end': record.planned_end.isoformat() if record.planned_end else None,
                'actual_start': record.actual_start.isoformat() if record.actual_start else None,
                'actual_end': record.actual_end.isoformat() if record.actual_end else None,
                'planned_duration_days': planned_duration,
                'actual_duration_days': actual_duration,
                'variance_percentage': variance_pct,
                'progress': record.progress,
                'pep_activity_id': record.pep_activity_id,
            }
            tasks_with_variance.append(item)

            # Categorize by severity
            if variance_pct > 20:
                severity_groups['critical'].append(item)
            elif variance_pct > 10:
                severity_groups['moderate'].append(item)
            elif variance_pct > 0:
                severity_groups['minor'].append(item)
            else:
                severity_groups['on_track'].append(item)

            # Monthly trend (by planned_end month)
            if record.planned_end:
                month_key = record.planned_end.strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = {'planned': 0.0, 'actual': 0.0, 'count': 0}
                monthly_data[month_key]['planned'] += planned_duration
                if actual_duration:
                    monthly_data[month_key]['actual'] += actual_duration
                monthly_data[month_key]['count'] += 1

        # SPI = total planned / total actual (>1 = ahead, <1 = behind)
        spi = round(total_planned_days / total_actual_days, 3) if total_actual_days > 0 else None

        # Average variance
        variances = [t['variance_percentage'] for t in tasks_with_variance]
        avg_variance = round(sum(variances) / len(variances), 2) if variances else 0.0

        # Build monthly trend list (sorted by month)
        monthly_trend = []
        for month_key in sorted(monthly_data.keys()):
            d = monthly_data[month_key]
            spi_month = round(d['planned'] / d['actual'], 3) if d['actual'] > 0 else None
            monthly_trend.append({
                'month': month_key,
                'label': month_label(month_key),
                'planned_days': round(d['planned'], 1),
                'actual_days': round(d['actual'], 1),
                'spi': spi_month,
                'count': d['count'],
            })

        return {
            'spi': spi,
            'tasks_by_severity': severity_groups,
            'monthly_trend': monthly_trend,
            'total_tasks': len(tasks_with_variance),
            'avg_variance_pct': avg_variance,
        }

    # -----------------------------------------------------------------------
    # Feature 4: Sync History
    # -----------------------------------------------------------------------

    @staticmethod
    def get_sync_history(activity_id: int) -> List[Dict[str, Any]]:
        """Return the sync audit trail for a specific PEPActivity."""
        logs = (
            PEPActivityLog.query
            .filter_by(activity_id=activity_id)
            .order_by(PEPActivityLog.created_at.desc())
            .all()
        )
        return [
            {
                'id': log.id,
                'change_description': log.change_description,
                'old_value': log.old_value,
                'new_value': log.new_value,
                'sync_source': log.sync_source,
                'created_by': getattr(log.author, 'full_name', None) or 'Sistema',
                'created_at': log.created_at.isoformat(),
            }
            for log in logs
        ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_suggestion(record: ScheduleImportRecord, days_overdue: int) -> Optional[str]:
    """Build an actionable suggestion for a delayed task."""
    if days_overdue <= 0:
        return None
    if record.progress < 25:
        return f'Aumentar recursos para "{record.task_name}" — progresso muito baixo ({record.progress}%).'
    if days_overdue > 14:
        return f'Revisar escopo ou realocar equipe para "{record.task_name}" — {days_overdue} dias de atraso.'
    return f'Monitorar de perto "{record.task_name}" — {days_overdue} dias de atraso.'


def month_label(month_key: str) -> str:
    """Convert YYYY-MM to a readable label like 'Jan/2024'."""
    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    try:
        year, month = month_key.split('-')
        return f'{month_names[int(month) - 1]}/{year}'
    except (ValueError, IndexError):
        return month_key
