"""Time entry service."""
from datetime import datetime, timedelta, date as date_type
from typing import List, Optional, Tuple, Any, Dict, Set
from app import db
from app.models.time_entry import MeasurementCycle, TimeEntry
from app.constants import MAX_HOURS_PER_DAY

class TimeEntryService:
    """Service class for time entry and measurement cycle operations."""

    # ── Internal Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _parse_hours(hours_str: str) -> timedelta:
        """Convert HH:MM:SS string to timedelta."""
        h, m, s = map(int, hours_str.split(":"))
        return timedelta(hours=h, minutes=m, seconds=s)

    @staticmethod
    def _sum_hours(entries: List[TimeEntry]) -> timedelta:
        """Sum hours from a list of entries."""
        total = timedelta()
        for e in entries:
            total += TimeEntryService._parse_hours(e.hours_worked)
        return total

    @staticmethod
    def _validate_daily_limit(
        user_id: int,
        work_date,
        new_hours: str,
        exclude_entry_id: Optional[int] = None
    ) -> Optional[str]:
        """Validate daily hour limit (10h/day)."""

        query = TimeEntry.query.filter_by(
            user_id=user_id,
            work_date=work_date
        )

        if exclude_entry_id:
            query = query.filter(TimeEntry.id != exclude_entry_id)

        entries = query.all()

        total_hours = TimeEntryService._sum_hours(entries)
        new_hours_td = TimeEntryService._parse_hours(new_hours)

        max_hours = timedelta(hours=MAX_HOURS_PER_DAY)

        if total_hours + new_hours_td > max_hours:

            remaining = max_hours - total_hours

            return (
                f'Limite diário de {MAX_HOURS_PER_DAY}h excedido. '
                f'Você já apontou {total_hours}. '
                f'Restante permitido: {remaining}.'
            )

        return None

    # ── Measurement Cycles ─────────────────────────────────────────────────

    @staticmethod
    def get_active_cycle() -> Optional[MeasurementCycle]:
        return MeasurementCycle.query.filter_by(is_active=True).first()

    @staticmethod
    def get_all_cycles() -> List[MeasurementCycle]:
        return MeasurementCycle.query.order_by(MeasurementCycle.start_date.desc()).all()

    @staticmethod
    def get_cycle(cycle_id: int) -> Optional[MeasurementCycle]:
        return db.session.get(MeasurementCycle, cycle_id)

    @staticmethod
    def create_cycle(
        start_day: int,
        start_date,
        end_date,
        is_active: bool,
        created_by: int,
    ) -> Tuple[Optional[MeasurementCycle], Optional[str]]:

        if not (1 <= start_day <= 28):
            return None, 'O dia de início deve estar entre 1 e 28.'

        if not start_date or not end_date:
            return None, 'As datas de início e fim são obrigatórias.'

        if end_date <= start_date:
            return None, 'A data de fim deve ser posterior à data de início.'

        if is_active:
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
                MeasurementCycle.is_active == True
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

        from sqlalchemy.orm import joinedload

        query = TimeEntry.query.options(
            joinedload(TimeEntry.project),
            joinedload(TimeEntry.user)
        )

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

            query = query.outerjoin(Project).filter(
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

        # Validate daily hour limit
        error = TimeEntryService._validate_daily_limit(
            user_id,
            work_date,
            hours_worked
        )

        if error:
            return None, error

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

        entry = db.session.get(TimeEntry, entry_id)

        if not entry:
            return None, 'Apontamento não encontrado.'

        work_date = data.get('work_date', entry.work_date)
        hours_worked = data.get('hours_worked', entry.hours_worked)

        error = TimeEntryService._validate_daily_limit(
            entry.user_id,
            work_date,
            hours_worked,
            exclude_entry_id=entry.id
        )

        if error:
            return None, error

        for field in (
            'project_id',
            'discipline',
            'main_activity',
            'sub_activity',
            'work_date',
            'hours_worked',
            'hour_type',
            'observation'
        ):
            if field in data:
                setattr(entry, field, data[field] if data[field] != '' else None)

        db.session.commit()

        return entry, None

    # ── Bulk / Pending helpers ─────────────────────────────────────────────

    @staticmethod
    def generate_weekday_dates(
        start_date: date_type,
        end_date: date_type,
        skip_weekends: bool = True,
    ) -> List[date_type]:

        dates: List[date_type] = []
        current = start_date

        while current <= end_date:
            if not skip_weekends or current.weekday() < 5:
                dates.append(current)

            current += timedelta(days=1)

        return dates

    @staticmethod
    def get_pending_cycle_dates(
        user_id: int,
        cycle: MeasurementCycle,
    ) -> Tuple[List[date_type], Set[date_type], List[date_type], List[date_type], List[date_type]]:

        all_weekdays = TimeEntryService.generate_weekday_dates(
            cycle.start_date,
            cycle.end_date,
            skip_weekends=True
        )

        entries = TimeEntry.query.filter_by(
            user_id=user_id,
            measurement_cycle_id=cycle.id,
        ).all()

        entered_dates: Set[date_type] = {e.work_date for e in entries}

        today = date_type.today()

        pending = [d for d in all_weekdays if d not in entered_dates and d <= today]
        future = [d for d in all_weekdays if d not in entered_dates and d > today]
        completed = [d for d in all_weekdays if d in entered_dates]

        return all_weekdays, entered_dates, pending, future, completed

    @staticmethod
    def create_bulk_time_entries(
        dates: List[date_type],
        project_id: int,
        user_id: int,
        main_activity: str,
        hours_worked: str,
        hour_type: str,
        discipline: Optional[str] = None,
        sub_activity: Optional[str] = None,
        observation: Optional[str] = None,
    ) -> Tuple[List[TimeEntry], List[str]]:

        results: List[TimeEntry] = []
        errors: List[str] = []

        for work_date in dates:

            entry, error = TimeEntryService.create_time_entry(
                project_id=project_id,
                user_id=user_id,
                main_activity=main_activity,
                work_date=work_date,
                hours_worked=hours_worked,
                hour_type=hour_type,
                discipline=discipline,
                sub_activity=sub_activity,
                observation=observation,
            )

            if entry:
                results.append(entry)
            else:
                errors.append(f"{work_date.strftime('%d/%m/%Y')}: {error}")

        return results, errors

    @staticmethod
    def delete_time_entry(
        entry_id: int,
        is_admin: bool = False,
        current_user_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:

        entry = db.session.get(TimeEntry, entry_id)

        if not entry:
            return False, 'Apontamento não encontrado.'

        db.session.delete(entry)
        db.session.commit()

        return True, None