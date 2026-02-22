"""Tests for report functionality."""
import pytest
from app.models.report import Report
from app.services.report_service import ReportService


class TestReportService:
    """Tests for ReportService."""

    def test_create_report_missing_title(self, app, db):
        """Test that creating a report without a title returns an error."""
        with app.app_context():
            report, error = ReportService.create_report(
                title='',
                content='content',
                report_type='progress',
                project_id=1,
                author_id=1,
            )
            assert report is None
            assert error is not None

    def test_get_nonexistent_report(self, app, db):
        """Test that getting a non-existent report returns None."""
        with app.app_context():
            report = ReportService.get_report(99999)
            assert report is None


class TestReportModel:
    """Tests for Report model."""

    def test_report_repr(self, app, db):
        """Test report string representation."""
        with app.app_context():
            report = Report(title='My Report', project_id=1, author_id=1)
            assert 'My Report' in repr(report)
