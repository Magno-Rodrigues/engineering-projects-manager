"""Tests for the financial module: models and services."""
import pytest
from decimal import Decimal
from datetime import date
from app import db
from app.models.supplier import Supplier
from app.models.cost_center import CostCenter
from app.models.financial_budget import FinancialBudget, FinancialBudgetItem
from app.models.financial_transaction import FinancialTransaction
from app.models.financial_earned_value import FinancialEarnedValue
from app.models.project import Project
from app.models.user import User
from app.services.financial_service import (
    SupplierService,
    CostCenterService,
    FinancialBudgetService,
    FinancialTransactionService,
    FinancialEVMService,
)


@pytest.fixture(scope='function')
def fin_user(app, db):
    """Create a user for financial tests."""
    with app.app_context():
        user = User(username='fin_user', email='fin@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        uid = user.id
        yield uid
        u = db.session.get(User, uid)
        if u:
            db.session.delete(u)
            db.session.commit()


@pytest.fixture(scope='function')
def fin_project(app, db, fin_user):
    """Create a project for financial tests."""
    with app.app_context():
        project = Project(name='Financial Test Project', owner_id=fin_user)
        db.session.add(project)
        db.session.commit()
        pid = project.id
        yield pid
        p = db.session.get(Project, pid)
        if p:
            db.session.delete(p)
            db.session.commit()


class TestSupplierService:
    """Tests for SupplierService."""

    def test_create_supplier_success(self, app, db):
        """Test creating a supplier successfully."""
        with app.app_context():
            s, error = SupplierService.create_supplier(name='Acme Corp')
            assert error is None
            assert s is not None
            assert s.name == 'Acme Corp'
            db.session.delete(s)
            db.session.commit()

    def test_create_supplier_missing_name(self, app, db):
        """Test that missing name returns an error."""
        with app.app_context():
            s, error = SupplierService.create_supplier(name='')
            assert s is None
            assert error is not None

    def test_create_supplier_duplicate_name(self, app, db):
        """Test that duplicate name returns an error."""
        with app.app_context():
            s1, _ = SupplierService.create_supplier(name='UniqueSupplier')
            s2, error = SupplierService.create_supplier(name='UniqueSupplier')
            assert s2 is None
            assert 'already exists' in error.lower()
            db.session.delete(s1)
            db.session.commit()

    def test_get_all_suppliers(self, app, db):
        """Test listing all active suppliers."""
        with app.app_context():
            s1, _ = SupplierService.create_supplier(name='SupplierA')
            s2, _ = SupplierService.create_supplier(name='SupplierB')
            suppliers = SupplierService.get_all_suppliers()
            names = [s.name for s in suppliers]
            assert 'SupplierA' in names
            assert 'SupplierB' in names
            db.session.delete(s1)
            db.session.delete(s2)
            db.session.commit()

    def test_delete_supplier_success(self, app, db):
        """Test deleting a supplier."""
        with app.app_context():
            s, _ = SupplierService.create_supplier(name='ToDeleteSupplier')
            sid = s.id
            success, error = SupplierService.delete_supplier(sid)
            assert success is True
            assert error is None
            assert db.session.get(Supplier, sid) is None

    def test_delete_supplier_not_found(self, app, db):
        """Test deleting a non-existent supplier returns an error."""
        with app.app_context():
            success, error = SupplierService.delete_supplier(99999)
            assert success is False
            assert 'not found' in error.lower()


class TestFinancialBudgetService:
    """Tests for FinancialBudgetService."""

    def test_create_budget_success(self, app, db, fin_project, fin_user):
        """Test creating a budget successfully."""
        with app.app_context():
            budget, error = FinancialBudgetService.create_budget(
                project_id=fin_project,
                total_planned_budget='100000',
                baseline_date='2026-01-01',
                created_by=fin_user,
            )
            assert error is None
            assert budget is not None
            assert budget.total_planned_budget == Decimal('100000')
            assert budget.currency == 'BRL'
            db.session.delete(budget)
            db.session.commit()

    def test_create_budget_invalid_project(self, app, db, fin_user):
        """Test creating a budget for a non-existent project."""
        with app.app_context():
            budget, error = FinancialBudgetService.create_budget(
                project_id=99999,
                total_planned_budget='1000',
                baseline_date='2026-01-01',
                created_by=fin_user,
            )
            assert budget is None
            assert 'not found' in error.lower()

    def test_create_budget_missing_date(self, app, db, fin_project, fin_user):
        """Test that missing baseline date returns an error."""
        with app.app_context():
            budget, error = FinancialBudgetService.create_budget(
                project_id=fin_project,
                total_planned_budget='1000',
                baseline_date=None,
                created_by=fin_user,
            )
            assert budget is None
            assert error is not None

    def test_add_budget_item_success(self, app, db, fin_project, fin_user):
        """Test adding an item to a budget."""
        with app.app_context():
            budget, _ = FinancialBudgetService.create_budget(
                project_id=fin_project,
                total_planned_budget='50000',
                baseline_date='2026-01-01',
                created_by=fin_user,
            )
            item, error = FinancialBudgetService.add_budget_item(
                budget_id=budget.id,
                description='Software licenses',
                planned_amount='5000',
                category='service',
            )
            assert error is None
            assert item is not None
            assert item.description == 'Software licenses'
            assert item.planned_amount == Decimal('5000')
            db.session.delete(budget)
            db.session.commit()

    def test_add_budget_item_invalid_category(self, app, db, fin_project, fin_user):
        """Test that an invalid category returns an error."""
        with app.app_context():
            budget, _ = FinancialBudgetService.create_budget(
                project_id=fin_project,
                total_planned_budget='50000',
                baseline_date='2026-01-01',
                created_by=fin_user,
            )
            item, error = FinancialBudgetService.add_budget_item(
                budget_id=budget.id,
                description='Test',
                planned_amount='1000',
                category='invalid_cat',
            )
            assert item is None
            assert 'category' in error.lower()
            db.session.delete(budget)
            db.session.commit()

    def test_get_active_budget(self, app, db, fin_project, fin_user):
        """Test retrieving the active budget for a project."""
        with app.app_context():
            budget, _ = FinancialBudgetService.create_budget(
                project_id=fin_project,
                total_planned_budget='75000',
                baseline_date='2026-02-01',
                created_by=fin_user,
            )
            active = FinancialBudgetService.get_active_budget(fin_project)
            assert active is not None
            assert active.id == budget.id
            db.session.delete(budget)
            db.session.commit()

    def test_lock_baseline_success(self, app, db, fin_project, fin_user):
        """Test locking a budget baseline."""
        with app.app_context():
            budget, _ = FinancialBudgetService.create_budget(
                project_id=fin_project,
                total_planned_budget='80000',
                baseline_date='2026-03-01',
                created_by=fin_user,
            )
            assert budget.is_locked is False
            ok, error = FinancialBudgetService.lock_baseline(budget.id)
            assert ok is True
            assert error is None
            refreshed = db.session.get(FinancialBudget, budget.id)
            assert refreshed.is_locked is True
            assert refreshed.status == 'closed'
            db.session.delete(refreshed)
            db.session.commit()

    def test_lock_baseline_already_locked(self, app, db, fin_project, fin_user):
        """Test that locking an already-locked baseline returns an error."""
        with app.app_context():
            budget, _ = FinancialBudgetService.create_budget(
                project_id=fin_project,
                total_planned_budget='50000',
                baseline_date='2026-04-01',
                created_by=fin_user,
            )
            FinancialBudgetService.lock_baseline(budget.id)
            ok, error = FinancialBudgetService.lock_baseline(budget.id)
            assert ok is False
            assert error is not None
            db.session.delete(db.session.get(FinancialBudget, budget.id))
            db.session.commit()

    def test_lock_baseline_not_found(self, app, db):
        """Test locking a non-existent budget."""
        with app.app_context():
            ok, error = FinancialBudgetService.lock_baseline(99999)
            assert ok is False
            assert 'not found' in error.lower()

    def test_add_item_to_locked_budget_fails(self, app, db, fin_project, fin_user):
        """Test that adding items to a locked budget is rejected."""
        with app.app_context():
            budget, _ = FinancialBudgetService.create_budget(
                project_id=fin_project,
                total_planned_budget='60000',
                baseline_date='2026-05-01',
                created_by=fin_user,
            )
            FinancialBudgetService.lock_baseline(budget.id)
            item, error = FinancialBudgetService.add_budget_item(
                budget_id=budget.id,
                description='New item',
                planned_amount='1000',
                category='other',
            )
            assert item is None
            assert 'locked' in error.lower()
            db.session.delete(db.session.get(FinancialBudget, budget.id))
            db.session.commit()

    def test_delete_item_from_locked_budget_fails(self, app, db, fin_project, fin_user):
        """Test that deleting items from a locked budget is rejected."""
        from app.models.financial_budget import FinancialBudgetItem
        with app.app_context():
            budget, _ = FinancialBudgetService.create_budget(
                project_id=fin_project,
                total_planned_budget='70000',
                baseline_date='2026-06-01',
                created_by=fin_user,
            )
            item, _ = FinancialBudgetService.add_budget_item(
                budget_id=budget.id,
                description='Item to protect',
                planned_amount='7000',
                category='labor',
            )
            FinancialBudgetService.lock_baseline(budget.id)
            ok, error = FinancialBudgetService.delete_budget_item(item.id)
            assert ok is False
            assert 'locked' in error.lower()
            db.session.delete(db.session.get(FinancialBudget, budget.id))
            db.session.commit()

    def test_create_revision_success(self, app, db, fin_project, fin_user):
        """Test creating a new revision from a locked baseline."""
        with app.app_context():
            budget, _ = FinancialBudgetService.create_budget(
                project_id=fin_project,
                total_planned_budget='90000',
                baseline_date='2026-07-01',
                created_by=fin_user,
            )
            FinancialBudgetService.add_budget_item(
                budget_id=budget.id,
                description='Original item',
                planned_amount='9000',
                category='material',
            )
            FinancialBudgetService.lock_baseline(budget.id)
            new_budget, error = FinancialBudgetService.create_revision(
                budget.id, created_by=fin_user, notes='Revisão 1'
            )
            assert error is None
            assert new_budget is not None
            assert new_budget.status == 'active'
            original = db.session.get(FinancialBudget, budget.id)
            assert original.status == 'revised'
            # New budget should have a copy of the items
            assert new_budget.items.count() == 1
            db.session.delete(new_budget)
            db.session.delete(original)
            db.session.commit()

    def test_create_revision_unlocked_fails(self, app, db, fin_project, fin_user):
        """Test that creating a revision of an unlocked budget returns an error."""
        with app.app_context():
            budget, _ = FinancialBudgetService.create_budget(
                project_id=fin_project,
                total_planned_budget='40000',
                baseline_date='2026-08-01',
                created_by=fin_user,
            )
            new_budget, error = FinancialBudgetService.create_revision(budget.id)
            assert new_budget is None
            assert error is not None
            db.session.delete(budget)
            db.session.commit()

    def test_create_revision_not_found(self, app, db):
        """Test creating a revision for a non-existent budget."""
        with app.app_context():
            new_budget, error = FinancialBudgetService.create_revision(99999)
            assert new_budget is None
            assert 'not found' in error.lower()


class TestFinancialTransactionService:
    """Tests for FinancialTransactionService."""

    def test_create_expense_success(self, app, db, fin_project, fin_user):
        """Test creating an expense transaction successfully."""
        with app.app_context():
            txn, error = FinancialTransactionService.create_transaction(
                project_id=fin_project,
                type='expense',
                description='Office supplies',
                amount='250.50',
                category='material',
                transaction_date='2026-02-15',
                created_by=fin_user,
            )
            assert error is None
            assert txn is not None
            assert txn.amount == Decimal('250.50')
            assert txn.type == 'expense'
            db.session.delete(txn)
            db.session.commit()

    def test_create_transaction_invalid_type(self, app, db, fin_project, fin_user):
        """Test that an invalid type returns an error."""
        with app.app_context():
            txn, error = FinancialTransactionService.create_transaction(
                project_id=fin_project,
                type='invalid_type',
                description='Test',
                amount='100',
                category='other',
                transaction_date='2026-02-15',
            )
            assert txn is None
            assert 'type' in error.lower()

    def test_create_transaction_invalid_project(self, app, db, fin_user):
        """Test creating a transaction for a non-existent project."""
        with app.app_context():
            txn, error = FinancialTransactionService.create_transaction(
                project_id=99999,
                type='expense',
                description='Test',
                amount='100',
                category='other',
                transaction_date='2026-02-15',
            )
            assert txn is None
            assert 'not found' in error.lower()

    def test_create_transaction_negative_amount(self, app, db, fin_project, fin_user):
        """Test that a negative amount returns an error."""
        with app.app_context():
            txn, error = FinancialTransactionService.create_transaction(
                project_id=fin_project,
                type='expense',
                description='Test',
                amount='-100',
                category='other',
                transaction_date='2026-02-15',
            )
            assert txn is None
            assert error is not None

    def test_create_transaction_duplicate_invoice(self, app, db, fin_project, fin_user):
        """Test that duplicate invoice_number per project returns an error."""
        with app.app_context():
            txn1, _ = FinancialTransactionService.create_transaction(
                project_id=fin_project,
                type='expense',
                description='First',
                amount='100',
                category='other',
                transaction_date='2026-02-15',
                invoice_number='INV-001',
            )
            txn2, error = FinancialTransactionService.create_transaction(
                project_id=fin_project,
                type='expense',
                description='Second',
                amount='200',
                category='other',
                transaction_date='2026-02-16',
                invoice_number='INV-001',
            )
            assert txn2 is None
            assert 'invoice' in error.lower()
            db.session.delete(txn1)
            db.session.commit()

    def test_get_project_summary(self, app, db, fin_project, fin_user):
        """Test getting financial summary for a project."""
        with app.app_context():
            t1, _ = FinancialTransactionService.create_transaction(
                project_id=fin_project, type='expense', description='Expense',
                amount='1000', category='material', transaction_date='2026-01-10',
                payment_status='completed',
            )
            t2, _ = FinancialTransactionService.create_transaction(
                project_id=fin_project, type='revenue', description='Revenue',
                amount='1500', category='other', transaction_date='2026-01-15',
                payment_status='completed',
            )
            summary = FinancialTransactionService.get_project_summary(fin_project)
            assert summary['total_expenses'] == 1000.0
            assert summary['total_revenues'] == 1500.0
            assert summary['net_cash_flow'] == 500.0
            db.session.delete(t1)
            db.session.delete(t2)
            db.session.commit()

    def test_get_monthly_cash_flow(self, app, db, fin_project, fin_user):
        """Test monthly cash flow aggregation."""
        with app.app_context():
            t1, _ = FinancialTransactionService.create_transaction(
                project_id=fin_project, type='expense', description='Jan expense',
                amount='500', category='material', transaction_date='2026-01-10',
            )
            t2, _ = FinancialTransactionService.create_transaction(
                project_id=fin_project, type='revenue', description='Jan revenue',
                amount='800', category='other', transaction_date='2026-01-20',
            )
            monthly = FinancialTransactionService.get_monthly_cash_flow(fin_project)
            jan_rows = [r for r in monthly if r['month'] == '2026-01']
            assert len(jan_rows) == 1
            assert jan_rows[0]['outflows'] == 500.0
            assert jan_rows[0]['inflows'] == 800.0
            assert jan_rows[0]['net_cash_flow'] == 300.0
            db.session.delete(t1)
            db.session.delete(t2)
            db.session.commit()

    def test_delete_transaction_success(self, app, db, fin_project, fin_user):
        """Test deleting a transaction."""
        with app.app_context():
            txn, _ = FinancialTransactionService.create_transaction(
                project_id=fin_project, type='expense', description='To delete',
                amount='100', category='other', transaction_date='2026-01-01',
            )
            tid = txn.id
            success, error = FinancialTransactionService.delete_transaction(tid)
            assert success is True
            assert db.session.get(FinancialTransaction, tid) is None


class TestFinancialEVMService:
    """Tests for FinancialEVMService."""

    def test_create_evm_report_success(self, app, db, fin_project):
        """Test creating an EVM report successfully."""
        with app.app_context():
            report, error = FinancialEVMService.create_evm_report(
                project_id=fin_project,
                report_date='2026-02-01',
                bac='100000',
                ac='40000',
                ev='45000',
                pv='50000',
            )
            assert error is None
            assert report is not None
            assert report.bac == Decimal('100000')
            # CPI = EV/AC = 45000/40000 = 1.125
            assert abs(report.cpi - 1.125) < 0.001
            # SPI = EV/PV = 45000/50000 = 0.9
            assert abs(report.spi - 0.9) < 0.001
            db.session.delete(report)
            db.session.commit()

    def test_create_evm_report_invalid_project(self, app, db):
        """Test creating an EVM report for a non-existent project."""
        with app.app_context():
            report, error = FinancialEVMService.create_evm_report(
                project_id=99999,
                report_date='2026-02-01',
                bac='100000', ac='40000', ev='45000', pv='50000',
            )
            assert report is None
            assert 'not found' in error.lower()

    def test_create_evm_report_duplicate_date(self, app, db, fin_project):
        """Test that duplicate date per project returns an error."""
        with app.app_context():
            r1, _ = FinancialEVMService.create_evm_report(
                project_id=fin_project, report_date='2026-03-01',
                bac='100000', ac='40000', ev='45000', pv='50000',
            )
            r2, error = FinancialEVMService.create_evm_report(
                project_id=fin_project, report_date='2026-03-01',
                bac='100000', ac='40000', ev='45000', pv='50000',
            )
            assert r2 is None
            assert 'already exists' in error.lower()
            db.session.delete(r1)
            db.session.commit()

    def test_evm_properties(self, app, db, fin_project):
        """Test EVM computed properties (CPI, SPI, variances)."""
        with app.app_context():
            report, _ = FinancialEVMService.create_evm_report(
                project_id=fin_project,
                report_date='2026-04-01',
                bac='200000',
                ac='60000',
                ev='80000',
                pv='100000',
            )
            # CV = EV - AC = 80000 - 60000 = 20000
            assert report.cost_variance == Decimal('20000')
            # SV = EV - PV = 80000 - 100000 = -20000
            assert report.schedule_variance == Decimal('-20000')
            # EAC = BAC / CPI = 200000 / (80000/60000) = 150000
            assert abs(report.calculated_eac - 150000.0) < 1.0
            db.session.delete(report)
            db.session.commit()

    def test_delete_evm_report_success(self, app, db, fin_project):
        """Test deleting an EVM report."""
        with app.app_context():
            report, _ = FinancialEVMService.create_evm_report(
                project_id=fin_project, report_date='2026-05-01',
                bac='100000', ac='40000', ev='45000', pv='50000',
            )
            rid = report.id
            success, error = FinancialEVMService.delete_evm_report(rid)
            assert success is True
            assert db.session.get(FinancialEarnedValue, rid) is None

    def test_delete_evm_report_not_found(self, app, db):
        """Test deleting a non-existent EVM report returns an error."""
        with app.app_context():
            success, error = FinancialEVMService.delete_evm_report(99999)
            assert success is False
            assert 'not found' in error.lower()


class TestFinancialEarnedValueModel:
    """Tests for FinancialEarnedValue model properties."""

    def test_repr(self, app, db, fin_project):
        """Test string representation."""
        with app.app_context():
            evm = FinancialEarnedValue(
                project_id=fin_project,
                report_date=date(2026, 1, 1),
                bac=Decimal('100000'),
                ac=Decimal('50000'),
                ev=Decimal('60000'),
                pv=Decimal('70000'),
            )
            assert 'FinancialEarnedValue' in repr(evm)

    def test_cpi_zero_ac(self, app, db):
        """Test CPI returns 0 when AC is 0."""
        with app.app_context():
            evm = FinancialEarnedValue(
                report_date=date(2026, 1, 1),
                bac=Decimal('100000'),
                ac=Decimal('0'),
                ev=Decimal('50000'),
                pv=Decimal('50000'),
            )
            assert evm.cpi == 0.0

    def test_spi_zero_pv(self, app, db):
        """Test SPI returns 0 when PV is 0."""
        with app.app_context():
            evm = FinancialEarnedValue(
                report_date=date(2026, 1, 1),
                bac=Decimal('100000'),
                ac=Decimal('50000'),
                ev=Decimal('50000'),
                pv=Decimal('0'),
            )
            assert evm.spi == 0.0
