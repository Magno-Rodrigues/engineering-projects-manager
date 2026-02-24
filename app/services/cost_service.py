"""Cost management service (PMBOK - Custo)."""
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple, Dict, Any
from app import db
from app.models.cost import BudgetLine, CostVariance, CostBaseline


class CostService:
    """Service class for cost management operations."""

    @staticmethod
    def _parse_decimal(value: Any) -> Tuple[Optional[Decimal], Optional[str]]:
        """Parse a decimal value."""
        if value is None or value == '':
            return Decimal('0'), None
        try:
            result = Decimal(str(value))
            if result < 0:
                return None, 'Value cannot be negative.'
            return result, None
        except InvalidOperation:
            return None, 'Invalid numeric value.'

    # -------------------------
    # Budget Lines
    # -------------------------

    @staticmethod
    def get_budget_lines(project_id: int) -> List[BudgetLine]:
        """Return all budget lines for a project."""
        return BudgetLine.query.filter_by(project_id=project_id).all()

    @staticmethod
    def get_budget_line(budget_line_id: int) -> Optional[BudgetLine]:
        """Return a budget line by ID."""
        return db.session.get(BudgetLine, budget_line_id)

    @staticmethod
    def create_budget_line(
        project_id: int,
        title: str,
        planned_value,
        description: str = None,
        category: str = None,
        actual_cost=None,
        wbs_item_id: int = None,
        activity_id: int = None,
        reference_date=None,
        created_by: int = None,
    ) -> Tuple[Optional[BudgetLine], Optional[str]]:
        """Create a new budget line."""
        if not title:
            return None, 'Title is required.'
        pv, err = CostService._parse_decimal(planned_value)
        if err:
            return None, f'Planned value: {err}'
        if pv <= 0:
            return None, 'Planned value must be positive.'
        ac, err = CostService._parse_decimal(actual_cost)
        if err:
            return None, f'Actual cost: {err}'
        line = BudgetLine(
            project_id=project_id,
            title=title,
            description=description,
            category=category,
            planned_value=pv,
            actual_cost=ac,
            wbs_item_id=wbs_item_id,
            activity_id=activity_id,
            reference_date=reference_date,
            created_by=created_by,
        )
        db.session.add(line)
        db.session.commit()
        return line, None

    @staticmethod
    def update_budget_line(
        budget_line_id: int,
        data: Dict[str, Any],
        updated_by: int = None,
    ) -> Tuple[Optional[BudgetLine], Optional[str]]:
        """Update an existing budget line."""
        line = db.session.get(BudgetLine, budget_line_id)
        if not line:
            return None, 'Budget line not found.'
        for key in ('planned_value', 'actual_cost'):
            if key in data:
                val, err = CostService._parse_decimal(data[key])
                if err:
                    return None, f'{key}: {err}'
                data[key] = val
        allowed_fields = {
            'title', 'description', 'category', 'planned_value',
            'actual_cost', 'reference_date', 'status',
        }
        for key, value in data.items():
            if key in allowed_fields:
                setattr(line, key, value if value != '' else None)
        if not line.title:
            db.session.rollback()
            return None, 'Title is required.'
        line.updated_by = updated_by
        db.session.commit()
        return line, None

    @staticmethod
    def delete_budget_line(budget_line_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a budget line."""
        line = db.session.get(BudgetLine, budget_line_id)
        if not line:
            return False, 'Budget line not found.'
        db.session.delete(line)
        db.session.commit()
        return True, None

    # -------------------------
    # Cost Variance (EV Metrics)
    # -------------------------

    @staticmethod
    def get_cost_variances(project_id: int) -> List[CostVariance]:
        """Return all cost variance records for a project."""
        return CostVariance.query.filter_by(project_id=project_id).order_by(CostVariance.reference_date).all()

    @staticmethod
    def create_cost_variance(
        project_id: int,
        reference_date,
        planned_value,
        earned_value,
        actual_cost,
        notes: str = None,
        created_by: int = None,
    ) -> Tuple[Optional[CostVariance], Optional[str]]:
        """Create a cost variance record."""
        if not reference_date:
            return None, 'Reference date is required.'
        pv, err = CostService._parse_decimal(planned_value)
        if err:
            return None, f'Planned value: {err}'
        ev, err = CostService._parse_decimal(earned_value)
        if err:
            return None, f'Earned value: {err}'
        ac, err = CostService._parse_decimal(actual_cost)
        if err:
            return None, f'Actual cost: {err}'
        cv = CostVariance(
            project_id=project_id,
            reference_date=reference_date,
            planned_value=pv,
            earned_value=ev,
            actual_cost=ac,
            notes=notes,
            created_by=created_by,
        )
        db.session.add(cv)
        db.session.commit()
        return cv, None

    @staticmethod
    def get_cost_variance_summary(project_id: int) -> Dict[str, Any]:
        """Calculate cost variance summary from budget lines."""
        lines = BudgetLine.query.filter_by(project_id=project_id).all()
        total_pv = sum(float(line.planned_value or 0) for line in lines)
        total_ac = sum(float(line.actual_cost or 0) for line in lines)
        return {
            'total_planned_value': total_pv,
            'total_actual_cost': total_ac,
            'cost_variance': total_pv - total_ac,
            'budget_lines': len(lines),
        }

    # -------------------------
    # S-Curve data
    # -------------------------

    @staticmethod
    def get_s_curve_data(project_id: int) -> List[Dict[str, Any]]:
        """Return cost variance data ordered by date for S-curve chart."""
        records = CostVariance.query.filter_by(project_id=project_id).order_by(
            CostVariance.reference_date
        ).all()
        result = []
        cumulative_pv = Decimal('0')
        cumulative_ev = Decimal('0')
        cumulative_ac = Decimal('0')
        for record in records:
            cumulative_pv += record.planned_value or Decimal('0')
            cumulative_ev += record.earned_value or Decimal('0')
            cumulative_ac += record.actual_cost or Decimal('0')
            result.append({
                'date': record.reference_date.isoformat(),
                'pv': float(record.planned_value or 0),
                'ev': float(record.earned_value or 0),
                'ac': float(record.actual_cost or 0),
                'cumulative_pv': float(cumulative_pv),
                'cumulative_ev': float(cumulative_ev),
                'cumulative_ac': float(cumulative_ac),
            })
        return result

    # -------------------------
    # Cost Baselines
    # -------------------------

    @staticmethod
    def get_cost_baselines(project_id: int) -> List[CostBaseline]:
        """Return all cost baselines for a project."""
        return CostBaseline.query.filter_by(project_id=project_id).all()

    @staticmethod
    def create_cost_baseline(
        project_id: int,
        name: str,
        total_budget,
        description: str = None,
        created_by: int = None,
    ) -> Tuple[Optional[CostBaseline], Optional[str]]:
        """Create a new cost baseline."""
        if not name:
            return None, 'Name is required.'
        budget, err = CostService._parse_decimal(total_budget)
        if err:
            return None, f'Budget: {err}'
        if budget <= 0:
            return None, 'Budget must be positive.'
        baseline = CostBaseline(
            project_id=project_id,
            name=name,
            description=description,
            total_budget=budget,
            created_by=created_by,
        )
        db.session.add(baseline)
        db.session.commit()
        return baseline, None
