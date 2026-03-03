"""Tests for ReportingService."""
import pytest
import os
from datetime import date
from app.models.project import Project
from app.models.user import User
from app.models.financial_transaction import FinancialTransaction
from app.services.reporting_service import ReportingService


@pytest.fixture(scope='function')
def rep_user(app, db):
    with app.app_context():
        user = User(username='rep_user', email='rep@example.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()
        uid = user.id
        yield uid
        u = db.session.get(User, uid)
        if u:
            db.session.delete(u)
            db.session.commit()


@pytest.fixture(scope='function')
def rep_project(app, db, rep_user):
    with app.app_context():
        project = Project(name='Report Test Project', owner_id=rep_user)
        db.session.add(project)
        db.session.commit()
        pid = project.id
        yield pid
        p = db.session.get(Project, pid)
        if p:
            db.session.delete(p)
            db.session.commit()


class TestReportingService:

    def test_generate_excel_report_executive(self, app, db, rep_project):
        with app.app_context():
            report, error = ReportingService.generate_excel_report(rep_project, 'executive')
            assert error is None
            assert report is not None
            assert report.report_type == 'executive'
            assert report.format == 'xlsx'
            assert report.file_path is not None
            assert os.path.exists(report.file_path)
            ReportingService.delete_report(report.id)

    def test_generate_excel_report_cash_flow(self, app, db, rep_project):
        with app.app_context():
            t = FinancialTransaction(
                project_id=rep_project, type='expense', description='Test',
                amount=500, category='labor', transaction_date=date(2024, 5, 1),
                payment_status='completed',
            )
            db.session.add(t)
            db.session.commit()
            report, error = ReportingService.generate_excel_report(rep_project, 'cash_flow')
            assert error is None
            assert report is not None
            ReportingService.delete_report(report.id)
            db.session.delete(t)
            db.session.commit()

    def test_generate_excel_report_invalid_type(self, app, db, rep_project):
        with app.app_context():
            report, error = ReportingService.generate_excel_report(rep_project, 'invalid')
            assert report is None
            assert error is not None

    def test_get_project_reports(self, app, db, rep_project):
        with app.app_context():
            report, _ = ReportingService.generate_excel_report(rep_project, 'evm')
            reports = ReportingService.get_project_reports(rep_project)
            assert any(r.id == report.id for r in reports)
            ReportingService.delete_report(report.id)

    def test_delete_report(self, app, db, rep_project):
        with app.app_context():
            report, _ = ReportingService.generate_excel_report(rep_project, 'detailed')
            fpath = report.file_path
            rid = report.id
            success, error = ReportingService.delete_report(rid)
            assert success is True
            assert error is None
            if fpath:
                assert not os.path.exists(fpath)
