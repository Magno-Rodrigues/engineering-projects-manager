"""Report service."""
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
        return Report.query.get(report_id)

    @staticmethod
    def create_report(
        title: str,
        content: str,
        report_type: str,
        project_id: int,
        author_id: int,
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
        )
        db.session.add(report)
        db.session.commit()
        return report, None
