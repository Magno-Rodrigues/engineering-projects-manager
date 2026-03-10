"""Time entry service."""
from datetime import datetime
from typing import List, Optional, Tuple, Any, Dict
from app import db
from app.models.time_entry import MeasurementCycle, TimeEntry


class TimeEntryService:
    """Service class for time entry and measurement cycle operations."""

    # ── Measurement Cycles ─────────────────────────────────────────────────

    @staticmethod
    def get_active_cycle() -> Optional[MeasurementCycle]:
        """Return the currently active measurement cycle."""
        return MeasurementCycle.query.filter_by(is_active=True).first()

    @staticmethod
    def get_all_cycles() -> List[MeasurementCycle]:
        """Return all measurement cycles ordered by start_date descending."""
        return MeasurementCycle.query.order_by(MeasurementCycle.start_date.desc()).all()

    @staticmethod
    def get_cycle(cycle_id: int) -> Optional[MeasurementCycle]:
        """Return a measurement cycle by ID."""
        return db.session.get(MeasurementCycle, cycle_id)

    @staticmethod
    def create_cycle(
        start_day: int,
        start_date,
        end_date,
        is_active: bool,
        created_by: int,
    ) -> Tuple[Optional[MeasurementCycle], Optional[str]]:
        """Create a new measurement cycle.

        Args:
            start_day: Day of the month (1-28) when the cycle starts.
            start_date: Start date of the cycle.
            end_date: End date of the cycle.
            is_active: Whether this cycle is the active one.
            created_by: ID of the admin creating the cycle.

        Returns:
            A tuple of (MeasurementCycle, None) on success or (None, error) on failure.
        """
        if not (1 <= start_day <= 28):
            return None, 'O dia de início deve estar entre 1 e 28.'
        if not start_date or not end_date:
            return None, 'As datas de início e fim são obrigatórias.'
        if end_date <= start_date:
            return None, 'A data de fim deve ser posterior à data de início.'

        if is_active:
            # Deactivate all other cycles
            MeasurementCycle.query.filter_by(is_active=True).update({'is_active': False})

        cycle = MeasurementCycle(
            start_day=start_day,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
            created_by=created_by,
        )
        db.session.add(cycle)
        db.session.commit()
        return cycle, None

    @staticmethod
    def update_cycle(
        cycle_id: int,
        data: Dict[str, Any],
    ) -> Tuple[Optional[MeasurementCycle], Optional[str]]:
        """Update an existing measurement cycle.

        Returns:
            A tuple of (MeasurementCycle, None) on success or (None, error) on failure.
        """
        cycle = db.session.get(MeasurementCycle, cycle_id)
        if not cycle:
            return None, 'Ciclo de medição não encontrado.'

        start_day = data.get('start_day', cycle.start_day)
        start_date = data.get('start_date', cycle.start_date)
        end_date = data.get('end_date', cycle.end_date)
        is_active = data.get('is_active', cycle.is_active)

        if not (1 <= int(start_day) <= 28):
            return None, 'O dia de início deve estar entre 1 e 28.'
        if end_date <= start_date:
            return None, 'A data de fim deve ser posterior à data de início.'

        if is_active and not cycle.is_active:
            MeasurementCycle.query.filter(
                MeasurementCycle.id != cycle_id,
                MeasurementCycle.is_active == True,  # noqa: E712
            ).update({'is_active': False})

        cycle.start_day = int(start_day)
        cycle.start_date = start_date
        cycle.end_date = end_date
        cycle.is_active = is_active
        db.session.commit()
        return cycle, None

    # ── Time Entries ───────────────────────────────────────────────────────

    @staticmethod
    def get_time_entries(
        user_id: int,
        is_admin: bool = False,
        project_id: Optional[int] = None,
        cycle_id: Optional[int] = None,
        work_date=None,
        search: Optional[str] = None,
        filter_user_id: Optional[int] = None,
    ) -> List[TimeEntry]:
        """Return time entries with optional filters.

        Admins see all entries; regular users see only their own.
        """
        from sqlalchemy.orm import joinedload
        query = TimeEntry.query.options(joinedload(TimeEntry.project), joinedload(TimeEntry.user))
        if not is_admin:
            query = query.filter_by(user_id=user_id)
        elif filter_user_id:
            query = query.filter_by(user_id=filter_user_id)
        if project_id:
            query = query.filter_by(project_id=project_id)
        if cycle_id:
            query = query.filter_by(measurement_cycle_id=cycle_id)
        if work_date:
            query = query.filter_by(work_date=work_date)
        if search:
            from app.models.project import Project
            search_term = f'%{search}%'
            query = query.outerjoin(Project, TimeEntry.project_id == Project.id).filter(
                db.or_(
                    TimeEntry.main_activity.ilike(search_term),
                    TimeEntry.sub_activity.ilike(search_term),
                    TimeEntry.discipline.ilike(search_term),
                    Project.name.ilike(search_term),
                )
            )
        return query.order_by(TimeEntry.work_date.desc()).all()

    @staticmethod
    def get_time_entry(entry_id: int) -> Optional[TimeEntry]:
        """Return a time entry by ID."""
        return db.session.get(TimeEntry, entry_id)

    @staticmethod
    def create_time_entry(
        project_id: int,
        user_id: int,
        main_activity: str,
        work_date,
        hours_worked: str,
        hour_type: str,
        discipline: Optional[str] = None,
        sub_activity: Optional[str] = None,
        observation: Optional[str] = None,
    ) -> Tuple[Optional[TimeEntry], Optional[str]]:
        """Create a new time entry.

        The work_date must fall within the currently active measurement cycle.

        Returns:
            A tuple of (TimeEntry, None) on success or (None, error) on failure.
        """
        if not main_activity:
            return None, 'A atividade principal é obrigatória.'
        if not work_date:
            return None, 'A data de trabalho é obrigatória.'
        if not TimeEntry.is_valid_hours(hours_worked):
            return None, 'O formato de horas deve ser HH:MM:SS.'
        if hour_type not in ('Normal', 'Extra'):
            return None, 'O tipo de hora deve ser Normal ou Extra.'

        active_cycle = TimeEntryService.get_active_cycle()
        if not active_cycle:
            return None, 'Não há ciclo de medição ativo. Contate o administrador.'
        if not (active_cycle.start_date <= work_date <= active_cycle.end_date):
            return None, (
                f'A data de trabalho deve estar dentro do ciclo ativo '
                f'({active_cycle.start_date} a {active_cycle.end_date}).'
            )

        # Validate project and cost center blocking status
        from app.models.project import Project
        from app.models.cost_center import CostCenter
        from app.models.project_cost_center import ProjectCostCenter
        project = db.session.get(Project, project_id)
        if project and project.status == 'blocked':
            return None, 'Este projeto está bloqueado e não aceita novos apontamentos.'
        blocked_cc = (
            CostCenter.query
            .join(ProjectCostCenter, ProjectCostCenter.cost_center_id == CostCenter.id)
            .filter(ProjectCostCenter.project_id == project_id, CostCenter.status == 'blocked')
            .first()
        )
        if blocked_cc:
            return None, (
                f'O centro de custo "{blocked_cc.name}" associado a este projeto está bloqueado. '
                'Nenhum apontamento pode ser registrado.'
            )

        entry = TimeEntry(
            project_id=project_id,
            user_id=user_id,
            discipline=discipline or None,
            main_activity=main_activity,
            sub_activity=sub_activity or None,
            work_date=work_date,
            hours_worked=hours_worked,
            hour_type=hour_type,
            observation=observation or None,
            measurement_cycle_id=active_cycle.id,
        )
        db.session.add(entry)
        db.session.commit()
        return entry, None

    @staticmethod
    def update_time_entry(
        entry_id: int,
        data: Dict[str, Any],
        is_admin: bool = False,
        current_user_id: Optional[int] = None,
    ) -> Tuple[Optional[TimeEntry], Optional[str]]:
        """Update a time entry.

        Regular users can only edit entries from the active cycle.
        Admins can edit any entry.

        Returns:
            A tuple of (TimeEntry, None) on success or (None, error) on failure.
        """
        entry = db.session.get(TimeEntry, entry_id)
        if not entry:
            return None, 'Apontamento não encontrado.'

        if not is_admin:
            if entry.user_id != current_user_id:
                return None, 'Você não tem permissão para editar este apontamento.'
            active_cycle = TimeEntryService.get_active_cycle()
            if not active_cycle or not (active_cycle.start_date <= entry.work_date <= active_cycle.end_date):
                return None, 'Apenas o administrador pode editar apontamentos de ciclos anteriores.'

        work_date = data.get('work_date', entry.work_date)
        hours_worked = data.get('hours_worked', entry.hours_worked)
        hour_type = data.get('hour_type', entry.hour_type)
        main_activity = data.get('main_activity', entry.main_activity)

        if not main_activity:
            return None, 'A atividade principal é obrigatória.'
        if not TimeEntry.is_valid_hours(hours_worked):
            return None, 'O formato de horas deve ser HH:MM:SS.'
        if hour_type not in ('Normal', 'Extra'):
            return None, 'O tipo de hora deve ser Normal ou Extra.'

        if not is_admin:
            active_cycle = TimeEntryService.get_active_cycle()
            if active_cycle and not (active_cycle.start_date <= work_date <= active_cycle.end_date):
                return None, (
                    f'A data de trabalho deve estar dentro do ciclo ativo '
                    f'({active_cycle.start_date} a {active_cycle.end_date}).'
                )

        for field in ('project_id', 'discipline', 'main_activity', 'sub_activity',
                      'work_date', 'hours_worked', 'hour_type', 'observation'):
            if field in data:
                setattr(entry, field, data[field] if data[field] != '' else None)

        db.session.commit()
        return entry, None

    @staticmethod
    def delete_time_entry(
        entry_id: int,
        is_admin: bool = False,
        current_user_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Delete a time entry.

        Regular users can only delete entries from the active cycle.
        Admins can delete any entry.

        Returns:
            A tuple of (True, None) on success or (False, error) on failure.
        """
        entry = db.session.get(TimeEntry, entry_id)
        if not entry:
            return False, 'Apontamento não encontrado.'

        if not is_admin:
            if entry.user_id != current_user_id:
                return False, 'Você não tem permissão para deletar este apontamento.'
            active_cycle = TimeEntryService.get_active_cycle()
            if not active_cycle or not (active_cycle.start_date <= entry.work_date <= active_cycle.end_date):
                return False, 'Apenas o administrador pode deletar apontamentos de ciclos anteriores.'

        db.session.delete(entry)
        db.session.commit()
        return True, None
