"""Report service."""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from app import db
from app.models.report import Report


class ReportService:
    """Service class for report operations."""

    @staticmethod
    def get_project_reports(project_id: int) -> List[Report]:
        """Return all reports for a project."""
        return Report.query.filter_by(project_id=project_id).all()

    @staticmethod
    def get_report(report_id: int) -> Optional[Report]:
        """Return a report by ID."""
        return db.session.get(Report, report_id)

    @staticmethod
    def create_report(
        title: str,
        content: str,
        report_type: str,
        project_id: int,
        author_id: int,
        report_date: Optional[date] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        executive_summary: Optional[str] = None,
        scope_complete_pct: Optional[Decimal] = None,
        schedule_variance: Optional[Decimal] = None,
        cost_variance: Optional[Decimal] = None,
        risks_identified: Optional[str] = None,
        current_issues: Optional[str] = None,
        completed_tasks_text: Optional[str] = None,
        tasks_in_progress_text: Optional[str] = None,
        next_activities: Optional[str] = None,
        corrective_actions: Optional[str] = None,
        attention_points: Optional[str] = None,
        approved_by_id: Optional[int] = None,
    ) -> Tuple[Optional[Report], Optional[str]]:
        """Create a new report.

        Returns:
            A tuple of (Report, None) on success or (None, error_message) on failure.
        """
        if not title:
            return None, 'Report title is required.'
        report = Report(
            title=title,
            content=content,
            report_type=report_type,
            project_id=project_id,
            author_id=author_id,
            report_date=report_date,
            period_start=period_start,
            period_end=period_end,
            executive_summary=executive_summary,
            scope_complete_pct=scope_complete_pct,
            schedule_variance=schedule_variance,
            cost_variance=cost_variance,
            risks_identified=risks_identified,
            current_issues=current_issues,
            completed_tasks_text=completed_tasks_text,
            tasks_in_progress_text=tasks_in_progress_text,
            next_activities=next_activities,
            corrective_actions=corrective_actions,
            attention_points=attention_points,
            approved_by_id=approved_by_id,
        )
        db.session.add(report)
        db.session.commit()
        return report, None
