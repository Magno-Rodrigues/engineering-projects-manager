"""Schedule management service (PMBOK - Prazo)."""
from datetime import date, timedelta
from typing import List, Optional, Tuple, Dict, Any
from app import db
from app.models.schedule import Activity, ActivityDependency, Milestone, ScheduleBaseline


class ScheduleService:
    """Service class for schedule management operations."""

    # -------------------------
    # Activities
    # -------------------------

    @staticmethod
    def get_activities(project_id: int) -> List[Activity]:
        """Return all activities for a project."""
        return Activity.query.filter_by(project_id=project_id).order_by(Activity.start_date).all()

    @staticmethod
    def get_activity(activity_id: int) -> Optional[Activity]:
        """Return an activity by ID."""
        return db.session.get(Activity, activity_id)

    @staticmethod
    def create_activity(
        project_id: int,
        title: str,
        description: str = None,
        start_date=None,
        end_date=None,
        estimated_duration: int = None,
        wbs_item_id: int = None,
        assignee_id: int = None,
        created_by: int = None,
    ) -> Tuple[Optional[Activity], Optional[str]]:
        """Create a new activity."""
        if not title:
            return None, 'Title is required.'
        if estimated_duration is not None and estimated_duration <= 0:
            return None, 'Duration must be positive.'
        if start_date and end_date and end_date < start_date:
            return None, 'End date cannot be before start date.'
        activity = Activity(
            project_id=project_id,
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            estimated_duration=estimated_duration,
            wbs_item_id=wbs_item_id,
            assignee_id=assignee_id,
            created_by=created_by,
        )
        db.session.add(activity)
        db.session.commit()
        return activity, None

    @staticmethod
    def update_activity(
        activity_id: int,
        data: Dict[str, Any],
        updated_by: int = None,
    ) -> Tuple[Optional[Activity], Optional[str]]:
        """Update an existing activity."""
        activity = db.session.get(Activity, activity_id)
        if not activity:
            return None, 'Activity not found.'
        start_date = data.get('start_date') or activity.start_date
        end_date = data.get('end_date') or activity.end_date
        if start_date and end_date and end_date < start_date:
            return None, 'End date cannot be before start date.'
        if 'estimated_duration' in data and data['estimated_duration'] is not None:
            try:
                dur = int(data['estimated_duration'])
                if dur <= 0:
                    return None, 'Duration must be positive.'
            except (ValueError, TypeError):
                return None, 'Invalid duration value.'
        allowed_fields = {
            'title', 'description', 'start_date', 'end_date',
            'estimated_duration', 'actual_duration', 'progress',
            'status', 'wbs_item_id', 'assignee_id',
        }
        for key, value in data.items():
            if key in allowed_fields:
                setattr(activity, key, value if value != '' else None)
        if not activity.title:
            db.session.rollback()
            return None, 'Title is required.'
        activity.updated_by = updated_by
        db.session.commit()
        return activity, None

    @staticmethod
    def delete_activity(activity_id: int) -> Tuple[bool, Optional[str]]:
        """Delete an activity and its dependencies."""
        activity = db.session.get(Activity, activity_id)
        if not activity:
            return False, 'Activity not found.'
        # Remove dependencies
        ActivityDependency.query.filter(
            (ActivityDependency.predecessor_id == activity_id) |
            (ActivityDependency.successor_id == activity_id)
        ).delete()
        db.session.delete(activity)
        db.session.commit()
        return True, None

    # -------------------------
    # Dependencies
    # -------------------------

    @staticmethod
    def add_dependency(
        predecessor_id: int,
        successor_id: int,
        dependency_type: str = 'FS',
        lag: int = 0,
    ) -> Tuple[Optional[ActivityDependency], Optional[str]]:
        """Add a dependency between two activities."""
        if predecessor_id == successor_id:
            return None, 'An activity cannot depend on itself.'
        # Check for circular dependency
        if ScheduleService._would_create_cycle(predecessor_id, successor_id):
            return None, 'This dependency would create a circular reference.'
        # Check for duplicate
        existing = ActivityDependency.query.filter_by(
            predecessor_id=predecessor_id,
            successor_id=successor_id,
        ).first()
        if existing:
            return None, 'This dependency already exists.'
        dep = ActivityDependency(
            predecessor_id=predecessor_id,
            successor_id=successor_id,
            dependency_type=dependency_type or 'FS',
            lag=lag or 0,
        )
        db.session.add(dep)
        db.session.commit()
        return dep, None

    @staticmethod
    def _would_create_cycle(predecessor_id: int, new_successor_id: int) -> bool:
        """Check if adding a dependency would create a cycle using BFS."""
        visited = set()
        queue = [new_successor_id]
        while queue:
            current = queue.pop(0)
            if current == predecessor_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            deps = ActivityDependency.query.filter_by(predecessor_id=current).all()
            for dep in deps:
                queue.append(dep.successor_id)
        return False

    @staticmethod
    def delete_dependency(dependency_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a dependency."""
        dep = db.session.get(ActivityDependency, dependency_id)
        if not dep:
            return False, 'Dependency not found.'
        db.session.delete(dep)
        db.session.commit()
        return True, None

    # -------------------------
    # Critical Path
    # -------------------------

    @staticmethod
    def get_critical_path(project_id: int) -> List[Activity]:
        """Return activities on the critical path for a project."""
        activities = Activity.query.filter_by(project_id=project_id).all()
        if not activities:
            return []
        # Mark critical activities (those with is_critical=True or on the longest path)
        critical = [a for a in activities if a.is_critical]
        return critical

    @staticmethod
    def calculate_schedule_variance(project_id: int) -> Dict[str, Any]:
        """Calculate schedule variance for the project.

        Returns dict with planned, actual and variance statistics.
        """
        activities = Activity.query.filter_by(project_id=project_id).all()
        total_planned = sum(
            (a.estimated_duration or 0) for a in activities
        )
        total_actual = sum(
            (a.actual_duration or 0) for a in activities
        )
        completed = [a for a in activities if a.status == 'completed']
        in_progress = [a for a in activities if a.status == 'in_progress']
        planned = [a for a in activities if a.status == 'planned']
        return {
            'total_activities': len(activities),
            'completed': len(completed),
            'in_progress': len(in_progress),
            'planned': len(planned),
            'total_planned_duration': total_planned,
            'total_actual_duration': total_actual,
            'schedule_variance': total_actual - total_planned if total_actual else None,
        }

    # -------------------------
    # Milestones
    # -------------------------

    @staticmethod
    def get_milestones(project_id: int) -> List[Milestone]:
        """Return all milestones for a project."""
        return Milestone.query.filter_by(project_id=project_id).order_by(Milestone.target_date).all()

    @staticmethod
    def get_milestone(milestone_id: int) -> Optional[Milestone]:
        """Return a milestone by ID."""
        return db.session.get(Milestone, milestone_id)

    @staticmethod
    def create_milestone(
        project_id: int,
        title: str,
        description: str = None,
        target_date=None,
        created_by: int = None,
    ) -> Tuple[Optional[Milestone], Optional[str]]:
        """Create a new milestone."""
        if not title:
            return None, 'Title is required.'
        milestone = Milestone(
            project_id=project_id,
            title=title,
            description=description,
            target_date=target_date,
            created_by=created_by,
        )
        db.session.add(milestone)
        db.session.commit()
        return milestone, None

    @staticmethod
    def update_milestone(
        milestone_id: int,
        data: Dict[str, Any],
        updated_by: int = None,
    ) -> Tuple[Optional[Milestone], Optional[str]]:
        """Update an existing milestone."""
        milestone = db.session.get(Milestone, milestone_id)
        if not milestone:
            return None, 'Milestone not found.'
        allowed_fields = {'title', 'description', 'target_date', 'actual_date', 'status'}
        for key, value in data.items():
            if key in allowed_fields:
                setattr(milestone, key, value if value != '' else None)
        if not milestone.title:
            db.session.rollback()
            return None, 'Title is required.'
        milestone.updated_by = updated_by
        db.session.commit()
        return milestone, None

    @staticmethod
    def delete_milestone(milestone_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a milestone."""
        milestone = db.session.get(Milestone, milestone_id)
        if not milestone:
            return False, 'Milestone not found.'
        db.session.delete(milestone)
        db.session.commit()
        return True, None
