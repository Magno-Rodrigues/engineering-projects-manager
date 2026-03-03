"""Primavera P6 XML and Excel importer."""
import io
from datetime import datetime
from typing import Any, Dict, List, Optional

import defusedxml.ElementTree as ET

from app.services.importers.base_importer import BaseImporter


def _parse_date(value: str) -> Optional[str]:
    """Return ISO date string or None."""
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(value[:19], fmt).date().isoformat()
        except (ValueError, TypeError):
            continue
    return None


class PrimaveraImporter(BaseImporter):
    """Parse Primavera P6 XML (XER export) and Excel files."""

    def parse(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """Parse Primavera file and return structured data."""
        self.errors = []
        lower = file_name.lower()
        if lower.endswith('.xml'):
            return self._parse_xml(file_content)
        if lower.endswith('.xls') or lower.endswith('.xlsx'):
            return self._parse_excel(file_content)
        self.errors.append(f'Unsupported file format: {file_name}')
        return {'tasks': [], 'wbs_items': [], 'resources': [], 'budgets': []}

    # ------------------------------------------------------------------
    def _parse_xml(self, content: bytes) -> Dict[str, Any]:
        try:
            root = ET.fromstring(content)
        except ET.ParseError as exc:
            self.errors.append(f'XML parse error: {exc}')
            return {'tasks': [], 'wbs_items': [], 'resources': [], 'budgets': []}

        tasks = self._xml_activities(root)
        wbs_items = self._xml_wbs(root)
        budgets = self._xml_budgets(root, tasks)
        return {'tasks': tasks, 'wbs_items': wbs_items, 'resources': [], 'budgets': budgets}

    def _xml_activities(self, root: Any) -> List[Dict[str, Any]]:
        activities = []
        for act in root.iter('Activity'):
            activities.append({
                'uid': act.get('ObjectId') or act.findtext('ObjectId', ''),
                'name': act.findtext('Name') or act.findtext('ActivityId', ''),
                'wbs': act.findtext('WBSObjectId') or act.get('WBSObjectId', ''),
                'start': _parse_date(act.findtext('StartDate', '')),
                'finish': _parse_date(act.findtext('FinishDate', '')),
                'duration': act.findtext('Duration', ''),
                'estimated_effort': self._parse_duration(act.findtext('Duration', '')),
                'planned_cost': act.findtext('BudgetedTotalCost') or act.findtext('PlannedTotalCost'),
                'summary': False,
                'milestone': act.findtext('Type', '') in ('MilestoneFlag', 'StartMilestone', 'FinishMilestone'),
            })
        return activities

    def _xml_wbs(self, root: Any) -> List[Dict[str, Any]]:
        wbs_items = []
        for wbs in root.iter('WBS'):
            obj_id = wbs.get('ObjectId') or wbs.findtext('ObjectId', '')
            parent_id = wbs.findtext('ParentObjectId') or wbs.get('ParentObjectId')
            wbs_items.append({
                'uid': obj_id,
                'wbs_code': wbs.findtext('Code', obj_id),
                'title': wbs.findtext('Name', ''),
                'level': int(wbs.findtext('Level', '1') or 1),
                'parent_uid': parent_id if parent_id else None,
            })
        return wbs_items

    def _xml_budgets(self, root: Any, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        budgets = []
        for task in tasks:
            cost = task.get('planned_cost')
            if cost:
                try:
                    if float(cost) > 0:
                        budgets.append({
                            'description': task['name'],
                            'planned_amount': cost,
                            'currency': 'BRL',
                            'planned_date_start': task.get('start'),
                            'planned_date_end': task.get('finish'),
                            'category': 'other',
                        })
                except (ValueError, TypeError):
                    pass
        return budgets

    def _parse_excel(self, content: bytes) -> Dict[str, Any]:
        try:
            import openpyxl
        except ImportError:
            self.errors.append('openpyxl is required to import Excel files.')
            return {'tasks': [], 'wbs_items': [], 'resources': [], 'budgets': []}

        try:
            wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        except Exception as exc:
            self.errors.append(f'Excel parse error: {exc}')
            return {'tasks': [], 'wbs_items': [], 'resources': [], 'budgets': []}

        tasks = []
        wbs_items = []
        budgets = []

        ws = wb.worksheets[0]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return {'tasks': [], 'wbs_items': [], 'resources': [], 'budgets': []}

        header = [str(c).strip().lower() if c else '' for c in rows[0]]
        col = {name: idx for idx, name in enumerate(header)}

        def get(row: tuple, key: str, default: str = '') -> str:
            idx = col.get(key)
            if idx is None:
                return default
            val = row[idx]
            return str(val).strip() if val is not None else default

        for i, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue
            uid = get(row, 'activity id') or get(row, 'id') or str(i)
            name = get(row, 'activity name') or get(row, 'name') or get(row, 'task name')
            if not name:
                continue
            start = _parse_date(get(row, 'start date') or get(row, 'start'))
            finish = _parse_date(get(row, 'finish date') or get(row, 'finish'))
            duration = get(row, 'duration') or get(row, 'original duration')
            effort = self._parse_duration(duration)
            wbs_code = get(row, 'wbs') or get(row, 'wbs code')
            cost_str = get(row, 'budgeted total cost') or get(row, 'planned cost') or get(row, 'cost')

            tasks.append({
                'uid': uid,
                'name': name,
                'wbs': wbs_code,
                'start': start,
                'finish': finish,
                'duration': duration,
                'estimated_effort': effort,
                'planned_cost': cost_str,
                'summary': False,
                'milestone': False,
            })

            if wbs_code and not any(w['wbs_code'] == wbs_code for w in wbs_items):
                parts = wbs_code.split('.')
                parent_code = '.'.join(parts[:-1]) if len(parts) > 1 else None
                wbs_items.append({
                    'uid': wbs_code,
                    'wbs_code': wbs_code,
                    'title': wbs_code,
                    'level': len(parts),
                    'parent_uid': parent_code,
                })

            try:
                if cost_str and float(cost_str) > 0:
                    budgets.append({
                        'description': name,
                        'planned_amount': cost_str,
                        'currency': 'BRL',
                        'planned_date_start': start,
                        'planned_date_end': finish,
                        'category': 'other',
                    })
            except (ValueError, TypeError):
                pass

        return {'tasks': tasks, 'wbs_items': wbs_items, 'resources': [], 'budgets': budgets}

    @staticmethod
    def _parse_duration(value: str) -> Optional[float]:
        """Parse duration string to hours float."""
        if not value:
            return None
        try:
            # Plain number → hours
            return float(value)
        except (ValueError, TypeError):
            pass
        # Handle "Xd", "Xh" patterns
        value = value.strip()
        if value.endswith('d'):
            try:
                return float(value[:-1]) * 8
            except ValueError:
                pass
        if value.endswith('h'):
            try:
                return float(value[:-1])
            except ValueError:
                pass
        return None
