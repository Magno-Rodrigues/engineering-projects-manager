"""Financial service for the financial module."""
from datetime import datetime, date, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from app import db
from app.models.cost_center import CostCenter
from app.models.project_cost_center import ProjectCostCenter
from app.models.financial_budget import FinancialBudget, FinancialBudgetItem, BUDGET_CATEGORIES, BUDGET_STATUSES
from app.models.financial_earned_value import FinancialEarnedValue
from app.models.financial_transaction import (
    FinancialTransaction, TRANSACTION_TYPES, TRANSACTION_CATEGORIES,
    PAYMENT_STATUSES, PAYMENT_METHODS,
)
from app.models.project import Project
from app.models.supplier import Supplier


def _parse_decimal(value: Any) -> Tuple[Optional[Decimal], Optional[str]]:
    """Parse a decimal value from form input.

    Returns:
        A tuple of (Decimal, None) on success or (None, error_message) on failure.
    """
    if value is None or value == '':
        return None, None
    try:
        result = Decimal(str(value))
        if result < 0:
            return None, 'Value cannot be negative.'
        return result, None
    except InvalidOperation:
        return None, 'Invalid numeric value.'


class SupplierService:
    """Service class for supplier operations."""

    @staticmethod
    def get_all_suppliers() -> List[Supplier]:
        """Return all active suppliers."""
        return Supplier.query.filter_by(status='active').order_by(Supplier.name).all()

    @staticmethod
    def get_supplier(supplier_id: int) -> Optional[Supplier]:
        """Return a supplier by ID."""
        return db.session.get(Supplier, supplier_id)

    @staticmethod
    def create_supplier(
        name: str,
        cnpj: str = None,
        contact_person: str = None,
        email: str = None,
        phone: str = None,
        address: str = None,
        city: str = None,
        state: str = None,
    ) -> Tuple[Optional[Supplier], Optional[str]]:
        """Create a new supplier."""
        if not name or not name.strip():
            return None, 'Supplier name is required.'
        if Supplier.query.filter_by(name=name.strip()).first():
            return None, 'A supplier with this name already exists.'
        supplier = Supplier(
            name=name.strip(),
            cnpj=cnpj or None,
            contact_person=contact_person or None,
            email=email or None,
            phone=phone or None,
            address=address or None,
            city=city or None,
            state=state or None,
        )
        db.session.add(supplier)
        db.session.commit()
        return supplier, None

    @staticmethod
    def delete_supplier(supplier_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a supplier by ID."""
        supplier = db.session.get(Supplier, supplier_id)
        if not supplier:
            return False, 'Supplier not found.'
        db.session.delete(supplier)
        db.session.commit()
        return True, None


class CostCenterService:
    """Service class for cost center operations."""

    @staticmethod
    def get_project_cost_centers(project_id: int) -> List[CostCenter]:
        """Return all cost centers for a project."""
        return (
            CostCenter.query
            .join(ProjectCostCenter, ProjectCostCenter.cost_center_id == CostCenter.id)
            .filter(ProjectCostCenter.project_id == project_id)
            .order_by(CostCenter.name)
            .all()
        )

    @staticmethod
    def get_cost_center(cost_center_id: int) -> Optional[CostCenter]:
        """Return a cost center by ID."""
        return db.session.get(CostCenter, cost_center_id)

    @staticmethod
    def create_cost_center(
        project_id: int,
        name: str,
        description: str = None,
        manager_id: int = None,
        budget_allocation: Any = None,
    ) -> Tuple[Optional[CostCenter], Optional[str]]:
        """Create a new cost center for a project."""
        if not db.session.get(Project, project_id):
            return None, 'Project not found.'
        if not name or not name.strip():
            return None, 'Cost center name is required.'
        budget_val, err = _parse_decimal(budget_allocation)
        if err:
            return None, f'Budget allocation: {err}'
        cc = CostCenter(
            name=name.strip(),
            description=description or None,
            manager_id=manager_id or None,
            budget_allocation=budget_val,
        )
        pcc = ProjectCostCenter(project_id=project_id, cost_center=cc)
        db.session.add(cc)
        db.session.add(pcc)
        db.session.commit()
        return cc, None

    @staticmethod
    def delete_cost_center(cost_center_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a cost center by ID."""
        cc = db.session.get(CostCenter, cost_center_id)
        if not cc:
            return False, 'Cost center not found.'
        db.session.delete(cc)
        db.session.commit()
        return True, None


class FinancialBudgetService:
    """Service class for financial budget operations."""

    @staticmethod
    def get_project_budgets(project_id: int) -> List[FinancialBudget]:
        """Return all budgets for a project."""
        return FinancialBudget.query.filter_by(project_id=project_id).order_by(
            FinancialBudget.baseline_date.desc()
        ).all()

    @staticmethod
    def get_active_budget(project_id: int) -> Optional[FinancialBudget]:
        """Return the active budget for a project, if any."""
        return FinancialBudget.query.filter_by(
            project_id=project_id, status='active'
        ).order_by(FinancialBudget.baseline_date.desc()).first()

    @staticmethod
    def get_budget(budget_id: int) -> Optional[FinancialBudget]:
        """Return a budget by ID."""
        return db.session.get(FinancialBudget, budget_id)

    @staticmethod
    def create_budget(
        project_id: int,
        total_planned_budget: Any,
        baseline_date: Any,
        created_by: int = None,
        currency: str = 'BRL',
        notes: str = None,
    ) -> Tuple[Optional[FinancialBudget], Optional[str]]:
        """Create a new financial budget for a project."""
        if not db.session.get(Project, project_id):
            return None, 'Project not found.'
        budget_val, err = _parse_decimal(total_planned_budget)
        if err:
            return None, f'Budget: {err}'
        if budget_val is None:
            return None, 'Total planned budget is required.'
        if not baseline_date:
            return None, 'Baseline date is required.'
        if isinstance(baseline_date, str):
            try:
                baseline_date = datetime.strptime(baseline_date, '%Y-%m-%d')
            except ValueError:
                return None, 'Invalid baseline date format.'
        budget = FinancialBudget(
            project_id=project_id,
            total_planned_budget=budget_val,
            currency=currency or 'BRL',
            baseline_date=baseline_date,
            created_by=created_by,
            notes=notes or None,
        )
        db.session.add(budget)
        db.session.commit()
        return budget, None

    @staticmethod
    def lock_baseline(budget_id: int) -> Tuple[bool, Optional[str]]:
        """Lock (freeze) a budget baseline by setting its status to 'closed'.

        Once locked, no items can be added or deleted.
        Returns (True, None) on success or (False, error) on failure.
        """
        budget = db.session.get(FinancialBudget, budget_id)
        if not budget:
            return False, 'Budget not found.'
        if budget.is_locked:
            return False, 'Budget is already locked.'
        budget.status = 'closed'
        db.session.commit()
        return True, None

    @staticmethod
    def create_revision(
        budget_id: int,
        created_by: int = None,
        notes: str = None,
    ) -> Tuple[Optional['FinancialBudget'], Optional[str]]:
        """Create a new revision of a locked budget baseline.

        The original budget is marked as 'revised' and a new 'active' budget
        is created copying all items from the original.
        Returns (new_budget, None) on success or (None, error) on failure.
        """
        original = db.session.get(FinancialBudget, budget_id)
        if not original:
            return None, 'Budget not found.'
        if not original.is_locked:
            return None, 'Only locked baselines can be revised. Lock the baseline first.'

        # Mark original as revised
        original.status = 'revised'

        # Create the new budget as a copy
        new_budget = FinancialBudget(
            project_id=original.project_id,
            total_planned_budget=original.total_planned_budget,
            currency=original.currency,
            baseline_date=datetime.now(timezone.utc),
            created_by=created_by,
            status='active',
            notes=notes or f'Revisão de orçamento #{original.id}',
        )
        db.session.add(new_budget)
        db.session.flush()

        # Copy all items
        for item in original.items.all():
            new_item = FinancialBudgetItem(
                budget_id=new_budget.id,
                description=item.description,
                planned_amount=item.planned_amount,
                category=item.category,
                cost_center_id=item.cost_center_id,
                planned_date_start=item.planned_date_start,
                planned_date_end=item.planned_date_end,
            )
            db.session.add(new_item)

        db.session.commit()
        return new_budget, None

    @staticmethod
    def add_budget_item(
        budget_id: int,
        description: str,
        planned_amount: Any,
        category: str = 'other',
        cost_center_id: int = None,
        planned_date_start: Any = None,
        planned_date_end: Any = None,
    ) -> Tuple[Optional[FinancialBudgetItem], Optional[str]]:
        """Add a line item to an existing budget."""
        budget = db.session.get(FinancialBudget, budget_id)
        if not budget:
            return None, 'Budget not found.'
        if budget.is_locked:
            return None, 'Cannot add items to a locked baseline.'
        if not description or not description.strip():
            return None, 'Description is required.'
        if category not in BUDGET_CATEGORIES:
            return None, f'Invalid category. Must be one of: {", ".join(BUDGET_CATEGORIES)}.'
        amount_val, err = _parse_decimal(planned_amount)
        if err:
            return None, f'Planned amount: {err}'
        if amount_val is None:
            return None, 'Planned amount is required.'

        def _parse_date(d):
            if not d:
                return None
            if isinstance(d, (date, datetime)):
                return d
            try:
                return datetime.strptime(d, '%Y-%m-%d').date()
            except ValueError:
                return None

        item = FinancialBudgetItem(
            budget_id=budget_id,
            description=description.strip(),
            planned_amount=amount_val,
            category=category,
            cost_center_id=cost_center_id or None,
            planned_date_start=_parse_date(planned_date_start),
            planned_date_end=_parse_date(planned_date_end),
        )
        db.session.add(item)
        db.session.commit()
        return item, None

    @staticmethod
    def delete_budget_item(item_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a budget item by ID."""
        item = db.session.get(FinancialBudgetItem, item_id)
        if not item:
            return False, 'Budget item not found.'
        if item.budget.is_locked:
            return False, 'Cannot delete items from a locked baseline.'
        db.session.delete(item)
        db.session.commit()
        return True, None


class FinancialTransactionService:
    """Service class for financial transaction operations."""

    @staticmethod
    def get_project_transactions(
        project_id: int,
        transaction_type: str = None,
    ) -> List[FinancialTransaction]:
        """Return all transactions for a project, optionally filtered by type."""
        query = FinancialTransaction.query.filter_by(project_id=project_id)
        if transaction_type:
            query = query.filter_by(type=transaction_type)
        return query.order_by(FinancialTransaction.transaction_date.desc()).all()

    @staticmethod
    def get_transaction(transaction_id: int) -> Optional[FinancialTransaction]:
        """Return a transaction by ID."""
        return db.session.get(FinancialTransaction, transaction_id)

    @staticmethod
    def create_transaction(
        project_id: int,
        type: str,
        description: str,
        amount: Any,
        category: str,
        transaction_date: Any,
        created_by: int = None,
        cost_center_id: int = None,
        payment_status: str = 'pending',
        payment_method: str = None,
        supplier_id: int = None,
        invoice_number: str = None,
        reference_document: str = None,
        notes: str = None,
    ) -> Tuple[Optional[FinancialTransaction], Optional[str]]:
        """Create a new financial transaction."""
        if not db.session.get(Project, project_id):
            return None, 'Project not found.'
        if type not in TRANSACTION_TYPES:
            return None, f'Invalid type. Must be one of: {", ".join(TRANSACTION_TYPES)}.'
        if not description or not description.strip():
            return None, 'Description is required.'
        if category not in TRANSACTION_CATEGORIES:
            return None, f'Invalid category. Must be one of: {", ".join(TRANSACTION_CATEGORIES)}.'
        if payment_status not in PAYMENT_STATUSES:
            return None, f'Invalid payment status. Must be one of: {", ".join(PAYMENT_STATUSES)}.'

        amount_val, err = _parse_decimal(amount)
        if err:
            return None, f'Amount: {err}'
        if amount_val is None:
            return None, 'Amount is required.'

        if not transaction_date:
            return None, 'Transaction date is required.'
        if isinstance(transaction_date, str):
            try:
                transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d').date()
            except ValueError:
                return None, 'Invalid transaction date format.'

        # Check unique invoice per project
        if invoice_number and invoice_number.strip():
            inv = invoice_number.strip()
            existing = FinancialTransaction.query.filter_by(
                project_id=project_id, invoice_number=inv
            ).first()
            if existing:
                return None, 'A transaction with this invoice number already exists for this project.'
        else:
            inv = None

        txn = FinancialTransaction(
            project_id=project_id,
            type=type,
            description=description.strip(),
            amount=amount_val,
            category=category,
            transaction_date=transaction_date,
            created_by=created_by,
            cost_center_id=cost_center_id or None,
            payment_status=payment_status,
            payment_method=payment_method or None,
            supplier_id=supplier_id or None,
            invoice_number=inv,
            reference_document=reference_document or None,
            notes=notes or None,
        )
        db.session.add(txn)
        db.session.commit()
        return txn, None

    @staticmethod
    def delete_transaction(transaction_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a transaction by ID."""
        txn = db.session.get(FinancialTransaction, transaction_id)
        if not txn:
            return False, 'Transaction not found.'
        db.session.delete(txn)
        db.session.commit()
        return True, None

    @staticmethod
    def update_transaction(transaction_id: int, **kwargs) -> Tuple[Optional['FinancialTransaction'], Optional[str]]:
        """Update a transaction. Returns (transaction, error)."""
        from datetime import datetime as _dt
        txn = db.session.get(FinancialTransaction, transaction_id)
        if not txn:
            return None, 'Transaction not found.'
        allowed = ('description', 'amount', 'category', 'transaction_date', 'cost_center_id',
                   'payment_status', 'payment_method', 'supplier_id', 'invoice_number',
                   'reference_document', 'notes')
        for key, val in kwargs.items():
            if key in allowed and val is not None:
                if key == 'amount':
                    val, err = _parse_decimal(val)
                    if err:
                        return None, f'Amount: {err}'
                elif key == 'transaction_date' and isinstance(val, str):
                    try:
                        val = _dt.strptime(val, '%Y-%m-%d').date()
                    except ValueError:
                        return None, 'Invalid transaction date format.'
                setattr(txn, key, val)
        db.session.commit()
        return txn, None

    @staticmethod
    def get_project_summary(project_id: int) -> Dict[str, Any]:
        """Return a summary of revenues, expenses and net cash flow for a project."""
        transactions = FinancialTransaction.query.filter_by(project_id=project_id).all()
        total_expenses = sum(
            float(t.amount) for t in transactions
            if t.type in ('expense', 'payment') and t.payment_status != 'cancelled'
        )
        total_revenues = sum(
            float(t.amount) for t in transactions
            if t.type in ('revenue', 'receipt') and t.payment_status != 'cancelled'
        )
        return {
            'total_expenses': total_expenses,
            'total_revenues': total_revenues,
            'net_cash_flow': total_revenues - total_expenses,
            'transaction_count': len(transactions),
        }

    @staticmethod
    def get_monthly_cash_flow(project_id: int) -> List[Dict[str, Any]]:
        """Return monthly cash flow aggregates for a project."""
        transactions = FinancialTransaction.query.filter_by(project_id=project_id).filter(
            FinancialTransaction.payment_status != 'cancelled'
        ).order_by(FinancialTransaction.transaction_date).all()

        monthly: Dict[str, Dict[str, float]] = {}
        for txn in transactions:
            key = txn.transaction_date.strftime('%Y-%m')
            if key not in monthly:
                monthly[key] = {'month': key, 'inflows': 0.0, 'outflows': 0.0}
            if txn.type in ('revenue', 'receipt'):
                monthly[key]['inflows'] += float(txn.amount)
            else:
                monthly[key]['outflows'] += float(txn.amount)

        result = []
        accumulated = 0.0
        for key in sorted(monthly.keys()):
            row = monthly[key]
            net = row['inflows'] - row['outflows']
            accumulated += net
            result.append({
                'month': row['month'],
                'inflows': row['inflows'],
                'outflows': row['outflows'],
                'net_cash_flow': net,
                'accumulated_cash_flow': accumulated,
            })
        return result


class FinancialEVMService:
    """Service class for EVM (Earned Value Management) operations."""

    @staticmethod
    def get_project_evm_reports(project_id: int) -> List[FinancialEarnedValue]:
        """Return all EVM reports for a project."""
        return FinancialEarnedValue.query.filter_by(project_id=project_id).order_by(
            FinancialEarnedValue.report_date.desc()
        ).all()

    @staticmethod
    def get_evm_report(report_id: int) -> Optional[FinancialEarnedValue]:
        """Return an EVM report by ID."""
        return db.session.get(FinancialEarnedValue, report_id)

    @staticmethod
    def create_evm_report(
        project_id: int,
        report_date: Any,
        bac: Any,
        ac: Any,
        ev: Any,
        pv: Any,
        eac: Any = None,
        etc: Any = None,
        notes: str = None,
    ) -> Tuple[Optional[FinancialEarnedValue], Optional[str]]:
        """Create a new EVM report for a project."""
        if not db.session.get(Project, project_id):
            return None, 'Project not found.'
        if not report_date:
            return None, 'Report date is required.'
        if isinstance(report_date, str):
            try:
                report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
            except ValueError:
                return None, 'Invalid report date format.'

        # Check uniqueness
        existing = FinancialEarnedValue.query.filter_by(
            project_id=project_id, report_date=report_date
        ).first()
        if existing:
            return None, 'An EVM report already exists for this project on this date.'

        for label, val in [('BAC', bac), ('AC', ac), ('EV', ev), ('PV', pv)]:
            v, err = _parse_decimal(val)
            if err:
                return None, f'{label}: {err}'
            if v is None:
                return None, f'{label} is required.'

        bac_val, _ = _parse_decimal(bac)
        ac_val, _ = _parse_decimal(ac)
        ev_val, _ = _parse_decimal(ev)
        pv_val, _ = _parse_decimal(pv)
        eac_val, err = _parse_decimal(eac)
        if err:
            return None, f'EAC: {err}'
        etc_val, err = _parse_decimal(etc)
        if err:
            return None, f'ETC: {err}'

        report = FinancialEarnedValue(
            project_id=project_id,
            report_date=report_date,
            bac=bac_val,
            ac=ac_val,
            ev=ev_val,
            pv=pv_val,
            eac=eac_val,
            etc=etc_val,
            notes=notes or None,
        )
        db.session.add(report)
        db.session.commit()
        return report, None

    @staticmethod
    def delete_evm_report(report_id: int) -> Tuple[bool, Optional[str]]:
        """Delete an EVM report by ID."""
        report = db.session.get(FinancialEarnedValue, report_id)
        if not report:
            return False, 'EVM report not found.'
        db.session.delete(report)
        db.session.commit()
        return True, None
