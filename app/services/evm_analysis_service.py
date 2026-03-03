"""EVM analysis service."""
from datetime import date
from typing import Any, Dict, List, Optional
from app.services.financial_service import FinancialEVMService


class EVMAnalysisService:
    """Service class for EVM analysis and charting data."""

    @staticmethod
    def get_scurve_data(project_id: int) -> List[Dict[str, Any]]:
        """Return PV, EV, AC series sorted by date for S-curve chart."""
        reports = FinancialEVMService.get_project_evm_reports(project_id)
        reports = sorted(reports, key=lambda r: r.report_date)
        return [
            {
                'date': r.report_date.strftime('%Y-%m-%d'),
                'pv': float(r.pv),
                'ev': float(r.ev),
                'ac': float(r.ac),
            }
            for r in reports
        ]

    @staticmethod
    def get_performance_trend(project_id: int) -> List[Dict[str, Any]]:
        """Return CPI and SPI trend across time."""
        reports = FinancialEVMService.get_project_evm_reports(project_id)
        reports = sorted(reports, key=lambda r: r.report_date)
        return [
            {
                'date': r.report_date.strftime('%Y-%m-%d'),
                'cpi': r.cpi,
                'spi': r.spi,
            }
            for r in reports
        ]

    @staticmethod
    def get_evm_summary(project_id: int) -> Optional[Dict[str, Any]]:
        """Return latest EVM values plus calculated indices and projections."""
        reports = FinancialEVMService.get_project_evm_reports(project_id)
        if not reports:
            return None
        latest = sorted(reports, key=lambda r: r.report_date)[-1]
        return {
            'report_date': latest.report_date.strftime('%Y-%m-%d'),
            'bac': float(latest.bac),
            'ac': float(latest.ac),
            'ev': float(latest.ev),
            'pv': float(latest.pv),
            'cpi': latest.cpi,
            'spi': latest.spi,
            'cost_variance': float(latest.cost_variance),
            'schedule_variance': float(latest.schedule_variance),
            'eac': latest.calculated_eac,
            'etc': latest.calculated_etc,
        }

    @staticmethod
    def get_variance_analysis(project_id: int) -> List[Dict[str, Any]]:
        """Return cost variance and schedule variance analysis across time."""
        reports = FinancialEVMService.get_project_evm_reports(project_id)
        reports = sorted(reports, key=lambda r: r.report_date)
        return [
            {
                'date': r.report_date.strftime('%Y-%m-%d'),
                'cost_variance': float(r.cost_variance),
                'schedule_variance': float(r.schedule_variance),
                'cpi': r.cpi,
                'spi': r.spi,
            }
            for r in reports
        ]

    @staticmethod
    def get_schedule_comparison(project_id: int) -> List[Dict[str, Any]]:
        """Return planned vs actual schedule progress for each task.

        For every task that has both ``start_date`` and ``due_date`` set, the
        method calculates the *expected* progress percentage at today's date
        (linear interpolation between start and end) and compares it with the
        task's recorded *actual* progress.  Tasks whose planned window has not
        yet started are treated as 0 % expected; tasks past their due date are
        treated as 100 % expected.

        Returns a list of dicts, one per qualifying task, sorted by
        ``start_date``.  Each dict contains:

        * ``task_id`` – primary key of the task
        * ``title`` – task title
        * ``start_date`` – planned start (ISO string)
        * ``due_date`` – planned end (ISO string)
        * ``actual_progress`` – recorded ``progress`` value (0-100)
        * ``expected_progress`` – computed expected progress at today (0-100)
        * ``variance`` – actual_progress minus expected_progress
        * ``status`` – task status string
        """
        from app.models.task import Task
        tasks = (
            Task.query
            .filter_by(project_id=project_id)
            .filter(Task.start_date.isnot(None), Task.due_date.isnot(None))
            .order_by(Task.start_date)
            .all()
        )
        today = date.today()
        result = []
        for task in tasks:
            start = task.start_date
            end = task.due_date
            if end <= start:
                # Inverted or zero-length date range — skip as invalid configuration.
                continue
            if today <= start:
                expected = 0.0
            elif today >= end:
                expected = 100.0
            else:
                total_days = (end - start).days  # guaranteed > 0 by the end > start check above
                elapsed_days = (today - start).days
                expected = round(elapsed_days / total_days * 100, 1)
            actual = task.progress or 0
            result.append({
                'task_id': task.id,
                'title': task.title,
                'start_date': start.strftime('%Y-%m-%d'),
                'due_date': end.strftime('%Y-%m-%d'),
                'actual_progress': actual,
                'expected_progress': expected,
                'variance': round(actual - expected, 1),
                'status': task.status,
            })
        return result
