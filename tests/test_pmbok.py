"""Tests for PMBOK constraint services (scope, schedule, cost)."""
import pytest
from app.models.scope import Requirement, WBSItem, ScopeChange
from app.models.schedule import Activity, Milestone
from app.models.cost import BudgetLine, CostVariance, CostBaseline
from app.services.scope_service import ScopeService
from app.services.schedule_service import ScheduleService
from app.services.cost_service import CostService


class TestScopeService:
    """Tests for ScopeService."""

    def test_create_requirement(self, app, db):
        """Test creating a requirement."""
        with app.app_context():
            req, error = ScopeService.create_requirement(
                project_id=1, title='Test Requirement', priority='high'
            )
            assert error is None
            assert req is not None
            assert req.title == 'Test Requirement'
            assert req.priority == 'high'
            assert req.status == 'draft'
            db.session.delete(req)
            db.session.commit()

    def test_create_requirement_missing_title(self, app, db):
        """Test that creating a requirement without a title returns an error."""
        with app.app_context():
            req, error = ScopeService.create_requirement(project_id=1, title='')
            assert req is None
            assert error is not None

    def test_create_wbs_item(self, app, db):
        """Test creating a WBS item."""
        with app.app_context():
            item, error = ScopeService.create_wbs_item(
                project_id=1, title='1.0 Project Management', code='1.0'
            )
            assert error is None
            assert item is not None
            assert item.level == 1
            db.session.delete(item)
            db.session.commit()

    def test_create_wbs_child_item(self, app, db):
        """Test creating a child WBS item increases level."""
        with app.app_context():
            parent, _ = ScopeService.create_wbs_item(project_id=1, title='Parent', code='1.0')
            child, error = ScopeService.create_wbs_item(
                project_id=1, title='Child', code='1.1', parent_id=parent.id
            )
            assert error is None
            assert child.level == 2
            db.session.delete(child)
            db.session.delete(parent)
            db.session.commit()

    def test_create_scope_change(self, app, db):
        """Test creating a scope change request."""
        with app.app_context():
            change, error = ScopeService.create_scope_change(
                project_id=1, title='Add new feature', reason='Client request'
            )
            assert error is None
            assert change is not None
            assert change.status == 'pending'
            db.session.delete(change)
            db.session.commit()

    def test_approve_scope_change(self, app, db):
        """Test approving a scope change."""
        with app.app_context():
            change, _ = ScopeService.create_scope_change(project_id=1, title='Test change')
            approved, error = ScopeService.approve_scope_change(change.id, approved_by=1)
            assert error is None
            assert approved.status == 'approved'
            db.session.delete(approved)
            db.session.commit()

    def test_reject_scope_change(self, app, db):
        """Test rejecting a scope change."""
        with app.app_context():
            change, _ = ScopeService.create_scope_change(project_id=1, title='Test change')
            rejected, error = ScopeService.reject_scope_change(change.id, updated_by=1)
            assert error is None
            assert rejected.status == 'rejected'
            db.session.delete(rejected)
            db.session.commit()

    def test_cannot_approve_already_approved(self, app, db):
        """Test that approving an already-approved change returns an error."""
        with app.app_context():
            change, _ = ScopeService.create_scope_change(project_id=1, title='Test')
            ScopeService.approve_scope_change(change.id, approved_by=1)
            _, error = ScopeService.approve_scope_change(change.id, approved_by=1)
            assert error is not None
            db.session.delete(change)
            db.session.commit()

    def test_delete_nonexistent_requirement(self, app, db):
        """Test deleting a nonexistent requirement."""
        with app.app_context():
            success, error = ScopeService.delete_requirement(99999)
            assert success is False
            assert error is not None


class TestScheduleService:
    """Tests for ScheduleService."""

    def test_create_activity(self, app, db):
        """Test creating an activity."""
        with app.app_context():
            activity, error = ScheduleService.create_activity(
                project_id=1, title='Design phase', estimated_duration=10
            )
            assert error is None
            assert activity is not None
            assert activity.estimated_duration == 10
            db.session.delete(activity)
            db.session.commit()

    def test_create_activity_missing_title(self, app, db):
        """Test that creating an activity without a title returns an error."""
        with app.app_context():
            activity, error = ScheduleService.create_activity(project_id=1, title='')
            assert activity is None
            assert error is not None

    def test_create_activity_negative_duration(self, app, db):
        """Test that negative duration returns an error."""
        with app.app_context():
            activity, error = ScheduleService.create_activity(
                project_id=1, title='Test', estimated_duration=-5
            )
            assert activity is None
            assert error is not None

    def test_create_activity_invalid_dates(self, app, db):
        """Test that end before start returns an error."""
        from datetime import date
        with app.app_context():
            activity, error = ScheduleService.create_activity(
                project_id=1,
                title='Test',
                start_date=date(2025, 6, 1),
                end_date=date(2025, 1, 1),
            )
            assert activity is None
            assert error is not None

    def test_create_milestone(self, app, db):
        """Test creating a milestone."""
        with app.app_context():
            ms, error = ScheduleService.create_milestone(
                project_id=1, title='Phase 1 complete'
            )
            assert error is None
            assert ms is not None
            assert ms.status == 'pending'
            db.session.delete(ms)
            db.session.commit()

    def test_calculate_schedule_variance(self, app, db):
        """Test schedule variance calculation."""
        with app.app_context():
            variance = ScheduleService.calculate_schedule_variance(99999)
            assert variance['total_activities'] == 0

    def test_no_circular_dependency(self, app, db):
        """Test that circular dependency detection works."""
        with app.app_context():
            a1, _ = ScheduleService.create_activity(project_id=1, title='A1')
            a2, _ = ScheduleService.create_activity(project_id=1, title='A2')
            dep, error = ScheduleService.add_dependency(a1.id, a2.id)
            assert error is None
            # Now try to create reverse (circular)
            dep2, error2 = ScheduleService.add_dependency(a2.id, a1.id)
            assert dep2 is None
            assert error2 is not None
            db.session.delete(dep)
            db.session.delete(a2)
            db.session.delete(a1)
            db.session.commit()

    def test_delete_nonexistent_activity(self, app, db):
        """Test deleting a nonexistent activity."""
        with app.app_context():
            success, error = ScheduleService.delete_activity(99999)
            assert success is False
            assert error is not None


class TestCostService:
    """Tests for CostService."""

    def test_create_budget_line(self, app, db):
        """Test creating a budget line."""
        with app.app_context():
            line, error = CostService.create_budget_line(
                project_id=1, title='Labor costs', planned_value='10000.00'
            )
            assert error is None
            assert line is not None
            assert float(line.planned_value) == 10000.0
            db.session.delete(line)
            db.session.commit()

    def test_create_budget_line_missing_title(self, app, db):
        """Test that a missing title returns an error."""
        with app.app_context():
            line, error = CostService.create_budget_line(
                project_id=1, title='', planned_value='1000'
            )
            assert line is None
            assert error is not None

    def test_create_budget_line_zero_value(self, app, db):
        """Test that zero planned value returns an error."""
        with app.app_context():
            line, error = CostService.create_budget_line(
                project_id=1, title='Test', planned_value='0'
            )
            assert line is None
            assert error is not None

    def test_create_budget_line_negative_value(self, app, db):
        """Test that negative planned value returns an error."""
        with app.app_context():
            line, error = CostService.create_budget_line(
                project_id=1, title='Test', planned_value='-100'
            )
            assert line is None
            assert error is not None

    def test_create_cost_variance(self, app, db):
        """Test creating a cost variance record."""
        from datetime import date
        with app.app_context():
            cv, error = CostService.create_cost_variance(
                project_id=1,
                reference_date=date(2025, 6, 1),
                planned_value='5000',
                earned_value='4000',
                actual_cost='4500',
            )
            assert error is None
            assert cv is not None
            assert float(cv.cost_variance) == -500.0  # EV - AC = 4000 - 4500
            assert float(cv.schedule_variance) == -1000.0  # EV - PV = 4000 - 5000
            db.session.delete(cv)
            db.session.commit()

    def test_cost_variance_cpi(self, app, db):
        """Test CPI calculation."""
        from datetime import date
        with app.app_context():
            cv, _ = CostService.create_cost_variance(
                project_id=1,
                reference_date=date(2025, 7, 1),
                planned_value='5000',
                earned_value='4000',
                actual_cost='5000',
            )
            assert cv.cpi is not None
            assert float(cv.cpi) == 0.8  # EV/AC = 4000/5000
            db.session.delete(cv)
            db.session.commit()

    def test_create_cost_baseline(self, app, db):
        """Test creating a cost baseline."""
        with app.app_context():
            baseline, error = CostService.create_cost_baseline(
                project_id=1, name='Baseline Rev 1', total_budget='100000'
            )
            assert error is None
            assert baseline is not None
            assert float(baseline.total_budget) == 100000.0
            db.session.delete(baseline)
            db.session.commit()

    def test_create_cost_baseline_zero_budget(self, app, db):
        """Test that zero budget returns an error."""
        with app.app_context():
            baseline, error = CostService.create_cost_baseline(
                project_id=1, name='Test', total_budget='0'
            )
            assert baseline is None
            assert error is not None

    def test_get_s_curve_data_empty(self, app, db):
        """Test S-curve data with no records."""
        with app.app_context():
            data = CostService.get_s_curve_data(99999)
            assert data == []

    def test_get_cost_variance_summary_empty(self, app, db):
        """Test cost variance summary with no budget lines."""
        with app.app_context():
            summary = CostService.get_cost_variance_summary(99999)
            assert summary['total_planned_value'] == 0
            assert summary['total_actual_cost'] == 0
            assert summary['budget_lines'] == 0

    def test_delete_nonexistent_budget_line(self, app, db):
        """Test deleting a nonexistent budget line."""
        with app.app_context():
            success, error = CostService.delete_budget_line(99999)
            assert success is False
            assert error is not None
