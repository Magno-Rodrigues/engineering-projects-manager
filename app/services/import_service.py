"""Import service — orchestrates file parsing and database persistence."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from app import db
from app.models.financial_budget import FinancialBudget, FinancialBudgetItem
from app.models.import_log import ImportLog
from app.models.task import Task
from app.models.wbs_item import WBSItem
from app.services.importers.ms_project_importer import MSProjectImporter
from app.services.importers.primavera_importer import PrimaveraImporter
from app.services.wbs_service import WBSService


class ImportService:
    """Orchestrate import of MS Project / Primavera P6 files into the database."""

    @staticmethod
    def parse_file(
        file_content: bytes,
        file_name: str,
        import_type: str,
    ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """Parse a project plan file and return (data, errors).

        data keys: tasks, wbs_items, resources, budgets
        """
        if import_type == 'ms_project':
            importer = MSProjectImporter()
        elif import_type == 'primavera':
            importer = PrimaveraImporter()
        else:
            return None, [f'Unknown import type: {import_type}']

        data = importer.parse(file_content, file_name)
        errors = importer.errors + importer.validate(data)
        return data, errors

    @staticmethod
    def _clear_previous_import_data(project_id: int) -> None:
        """Delete all previously imported tasks, WBS items, and budgets for a project.

        This ensures each new import replaces the previous plan data.
        """
        # Delete imported tasks
        Task.query.filter_by(project_id=project_id, source='import').delete(
            synchronize_session=False
        )
        db.session.flush()

        # Nullify self-referential parent_id first to avoid FK constraint violations,
        # then delete all imported WBS items.
        WBSItem.query.filter_by(project_id=project_id, source='import').update(
            {'parent_id': None}, synchronize_session=False
        )
        db.session.flush()
        WBSItem.query.filter_by(project_id=project_id, source='import').delete(
            synchronize_session=False
        )
        db.session.flush()

        # Delete previously imported budget baselines
        FinancialBudget.query.filter_by(
            project_id=project_id, source='import'
        ).delete(synchronize_session=False)
        db.session.flush()

    @staticmethod
    def import_data(
        project_id: int,
        created_by: int,
        file_name: str,
        import_type: str,
        data: Dict[str, Any],
        lock_baseline: bool = False,
    ) -> Tuple[Optional[ImportLog], Optional[str]]:
        """Persist parsed data into the database inside a transaction.

        Returns the ImportLog record on success or (None, error) on failure.
        Each import replaces the previous imported plan data for the project.
        If lock_baseline is True, the created budget baseline is locked (status='closed').
        """
        log = ImportLog(
            project_id=project_id,
            created_by=created_by,
            import_type=import_type,
            file_name=file_name,
            status='pending',
        )
        db.session.add(log)
        db.session.flush()

        try:
            # Replace previous imported data before inserting fresh data
            ImportService._clear_previous_import_data(project_id)

            # WBS items
            wbs_items = data.get('wbs_items', [])
            WBSService.bulk_create_wbs_items(project_id, created_by, wbs_items, source='import')

            # Tasks
            tasks_imported = 0
            for t in data.get('tasks', []):
                if t.get('summary'):
                    continue
                task = Task(
                    project_id=project_id,
                    title=t.get('name', 'Untitled'),
                    description=None,
                    status='todo',
                    start_date=_parse_date(t.get('start')),
                    due_date=_parse_date(t.get('finish')),
                    estimated_effort=t.get('estimated_effort'),
                    progress=int(t.get('percent_complete') or 0),
                    source='import',
                )
                db.session.add(task)
                tasks_imported += 1

            # Budget baseline
            budgets = data.get('budgets', [])
            if budgets:
                budget = FinancialBudget(
                    project_id=project_id,
                    total_planned_budget=_sum_budgets(budgets),
                    currency='BRL',
                    baseline_date=datetime.now(timezone.utc),
                    created_by=created_by,
                    notes=f'Imported from {file_name}',
                    status='closed' if lock_baseline else 'active',
                    source='import',
                )
                db.session.add(budget)
                db.session.flush()
                for b in budgets:
                    amount = _to_decimal(b.get('planned_amount'))
                    if amount is None:
                        continue
                    item = FinancialBudgetItem(
                        budget_id=budget.id,
                        description=b.get('description', ''),
                        planned_amount=amount,
                        category=b.get('category', 'other'),
                        planned_date_start=_parse_date(b.get('planned_date_start')),
                        planned_date_end=_parse_date(b.get('planned_date_end')),
                    )
                    db.session.add(item)

            log.status = 'success'
            log.total_tasks_imported = tasks_imported
            log.total_items_imported = len(wbs_items)
            db.session.commit()
            return log, None

        except Exception as exc:  # pragma: no cover
            db.session.rollback()
            log.status = 'failed'
            log.error_message = str(exc)
            db.session.add(log)
            db.session.commit()
            return None, str(exc)

    @staticmethod
    def get_import_logs(project_id: int) -> List[ImportLog]:
        """Return all import logs for a project, newest first."""
        return (
            ImportLog.query.filter_by(project_id=project_id)
            .order_by(ImportLog.created_at.desc())
            .all()
        )

    @staticmethod
    def get_logs_report(
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[ImportLog]:
        """Return import logs with optional filters, newest first.

        Supports filtering by user, project, and submission date range.
        Used for admin reporting and data analysis.
        """
        from sqlalchemy.orm import joinedload

        query = ImportLog.query.options(
            joinedload(ImportLog.creator),
            joinedload(ImportLog.project),
        )
        if user_id:
            query = query.filter(ImportLog.created_by == user_id)
        if project_id:
            query = query.filter(ImportLog.project_id == project_id)
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(ImportLog.created_at >= start_dt)
            except (ValueError, TypeError):
                pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(ImportLog.created_at < end_dt)
            except (ValueError, TypeError):
                pass
        return query.order_by(ImportLog.created_at.desc()).all()

    @staticmethod
    def rollback_import(log_id: int) -> Tuple[bool, Optional[str]]:
        """Mark an import log as rolled back (data removal is manual)."""
        log = db.session.get(ImportLog, log_id)
        if log is None:
            return False, 'Import log not found.'
        if log.status != 'success':
            return False, 'Only successful imports can be rolled back.'
        log.status = 'failed'
        log.error_message = 'Rolled back by user.'
        db.session.commit()
        return True, None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(value: Optional[str]):
    """Parse ISO date string to a date object or return None."""
    if not value:
        return None
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(value[:10], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            continue
    return None


def _to_decimal(value) -> Optional[Decimal]:
    try:
        d = Decimal(str(value))
        return d if d >= 0 else None
    except (InvalidOperation, TypeError):
        return None


def _sum_budgets(budgets: List[Dict[str, Any]]) -> Decimal:
    total = Decimal('0')
    for b in budgets:
        d = _to_decimal(b.get('planned_amount'))
        if d:
            total += d
    return total if total > 0 else Decimal('0')
