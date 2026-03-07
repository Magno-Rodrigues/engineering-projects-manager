"""Project service."""
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple, Dict, Any
from app import db
from app.models.project import Project
from app.models.communication_plan import CommunicationPlan
from app.models.financial_budget import FinancialBudget
from app.models.financial_earned_value import FinancialEarnedValue
from app.models.financial_report import FinancialReport
from app.models.financial_scenario import FinancialScenario
from app.models.financial_transaction import FinancialTransaction
from app.models.import_log import ImportLog
from app.models.project_charter import ProjectCharter
from app.models.project_closure import ProjectClosure
from app.models.project_cost_center import ProjectCostCenter
from app.models.report import Report
from app.models.requirement import Requirement
from app.models.scope_change import ScopeChange
from app.models.stakeholder import Stakeholder
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.models.wbs_item import WBSItem


class ProjectService:
    """Service class for project operations."""

    @staticmethod
    def get_user_projects(user_id: int, include_all: bool = False) -> List[Project]:
        """Return projects owned by a user, or all projects if include_all is True."""
        if include_all:
            return Project.query.all()
        return Project.query.filter_by(owner_id=user_id).all()

    @staticmethod
    def get_project(project_id: int) -> Optional[Project]:
        """Return a project by ID."""
        return db.session.get(Project, project_id)

    @staticmethod
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

    @staticmethod
    def create_project(
        name: str,
        description: str,
        owner_id: int,
        status: str = 'planning',
        start_date=None,
        end_date=None,
        budget=None,
        actual_cost=None,
        category: str = None,
        priority: str = None,
        location: str = None,
        client_name: str = None,
        notes: str = None,
    ) -> Tuple[Optional[Project], Optional[str]]:
        """Create a new project.

        Args:
            name: Project name.
            description: Project description.
            owner_id: ID of the owning user.
            status: Project status.
            start_date: Project start date.
            end_date: Project end date.
            budget: Project budget.
            actual_cost: Actual cost spent.
            category: Project category.
            priority: Project priority.
            location: Project location.
            client_name: Client name.
            notes: Additional notes.

        Returns:
            A tuple of (Project, None) on success or (None, error_message) on failure.
        """
        if not name:
            return None, 'Project name is required.'

        if start_date and end_date and end_date < start_date:
            return None, 'End date cannot be before start date.'

        budget_val, err = ProjectService._parse_decimal(budget)
        if err:
            return None, f'Budget: {err}'
        actual_cost_val, err = ProjectService._parse_decimal(actual_cost)
        if err:
            return None, f'Actual cost: {err}'

        project = Project(
            name=name,
            description=description,
            owner_id=owner_id,
            status=status or 'planning',
            start_date=start_date,
            end_date=end_date,
            budget=budget_val,
            actual_cost=actual_cost_val,
            category=category or None,
            priority=priority or None,
            location=location or None,
            client_name=client_name or None,
            notes=notes or None,
        )
        db.session.add(project)
        db.session.commit()
        return project, None

    @staticmethod
    def update_project(project_id: int, data: Dict[str, Any]) -> Tuple[Optional[Project], Optional[str]]:
        """Update an existing project.

        Args:
            project_id: ID of the project to update.
            data: Dictionary of fields to update.

        Returns:
            A tuple of (Project, None) on success or (None, error_message) on failure.
        """
        project = db.session.get(Project, project_id)
        if not project:
            return None, 'Project not found.'

        start_date = data.get('start_date') or project.start_date
        end_date = data.get('end_date') or project.end_date
        if start_date and end_date and end_date < start_date:
            return None, 'End date cannot be before start date.'

        for key in ('budget', 'actual_cost'):
            if key in data:
                val, err = ProjectService._parse_decimal(data[key])
                if err:
                    return None, f'{key.replace("_", " ").title()}: {err}'
                data[key] = val

        allowed_fields = {
            'name', 'description', 'status', 'start_date', 'end_date',
            'budget', 'actual_cost', 'category', 'priority', 'location',
            'client_name', 'notes',
        }
        for key, value in data.items():
            if key in allowed_fields:
                setattr(project, key, value if value != '' else None)
        # name must not be empty
        if not project.name:
            db.session.rollback()
            return None, 'Project name is required.'
        db.session.commit()
        return project, None

    @staticmethod
    def delete_project(project_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a project by ID.

        Explicitly removes all related records before deleting the project to
        avoid SQLAlchemy attempting to set project_id=NULL on NOT NULL columns.

        NOTE: If new models with a project_id foreign key are added, they must
        also be imported and included in the deletion logic below.

        Returns:
            A tuple of (True, None) on success or (False, error_message) on failure.
        """
        project = db.session.get(Project, project_id)
        if not project:
            return False, 'Project not found.'

        try:
            # Delete simple related records (only reference projects.id).
            simple_models = [
                CommunicationPlan,
                FinancialBudget,
                FinancialEarnedValue,
                FinancialReport,
                FinancialScenario,
                FinancialTransaction,
                ImportLog,
                ProjectCharter,
                ProjectClosure,
                ProjectCostCenter,
                Report,
                Requirement,
                ScopeChange,
                Stakeholder,
                TimeEntry,
            ]
            for model in simple_models:
                model.query.filter_by(project_id=project_id).delete(synchronize_session=False)

            # Delete tasks before WBSItems, since Task.wbs_item_id references wbs_items.
            Task.query.filter_by(project_id=project_id).delete(synchronize_session=False)

            # WBSItem has a self-referential parent_id FK. Clear it first so the
            # subsequent bulk delete does not violate the foreign key constraint.
            db.session.query(WBSItem).filter_by(project_id=project_id).update(
                {'parent_id': None}, synchronize_session=False
            )
            WBSItem.query.filter_by(project_id=project_id).delete(synchronize_session=False)

            db.session.delete(project)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return True, None
