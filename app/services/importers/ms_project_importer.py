"""MS Project XML importer."""
import io
from datetime import datetime
from typing import Any, Dict, List, Optional

import defusedxml.ElementTree as ET

from app.services.importers.base_importer import BaseImporter

_MS_NS = 'http://schemas.microsoft.com/project'


def _ns(tag: str) -> str:
    return f'{{{_MS_NS}}}{tag}'


def _text(element: Any, tag: str, default: str = '') -> str:
    child = element.find(_ns(tag))
    return child.text.strip() if child is not None and child.text else default


def _parse_date(value: str) -> Optional[str]:
    """Return an ISO date string (YYYY-MM-DD) or None."""
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(value[:19], fmt).date().isoformat()
        except (ValueError, TypeError):
            continue
    return None


class MSProjectImporter(BaseImporter):
    """Parse MS Project 2013+ XML files."""

    def parse(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """Parse MS Project XML and return structured data."""
        self.errors = []
        try:
            root = ET.fromstring(file_content)
        except ET.ParseError as exc:
            self.errors.append(f'XML parse error: {exc}')
            return {'tasks': [], 'wbs_items': [], 'resources': [], 'budgets': []}

        tasks = self._parse_tasks(root)
        wbs_items = self._build_wbs(tasks)
        resources = self._parse_resources(root)
        budgets = self._parse_baseline(root, tasks)

        return {
            'tasks': tasks,
            'wbs_items': wbs_items,
            'resources': resources,
            'budgets': budgets,
        }

    # ------------------------------------------------------------------
    def _parse_tasks(self, root: Any) -> List[Dict[str, Any]]:
        tasks_elem = root.find(_ns('Tasks'))
        if tasks_elem is None:
            return []
        result = []
        for task in tasks_elem.findall(_ns('Task')):
            uid = _text(task, 'UID')
            if uid == '0':
                continue
            outline_level_str = _text(task, 'OutlineLevel', '1')
            try:
                outline_level = int(outline_level_str)
            except ValueError:
                outline_level = 1
            duration_str = _text(task, 'Duration', '')
            effort = self._parse_duration_hours(duration_str)
            result.append({
                'uid': uid,
                'name': _text(task, 'Name'),
                'wbs': _text(task, 'WBS'),
                'outline_number': _text(task, 'OutlineNumber'),
                'outline_level': outline_level,
                'start': _parse_date(_text(task, 'Start')),
                'finish': _parse_date(_text(task, 'Finish')),
                'duration': duration_str,
                'estimated_effort': effort,
                'milestone': _text(task, 'Milestone') == '1',
                'summary': _text(task, 'Summary') == '1',
                'baseline_start': _parse_date(_text(task, 'BaselineStart')),
                'baseline_finish': _parse_date(_text(task, 'BaselineFinish')),
                'baseline_cost': self._parse_cost(_text(task, 'BaselineCost')),
                'percent_complete': _text(task, 'PercentComplete', '0'),
                'predecessors': _text(task, 'PredecessorLink'),
            })
        return result

    def _parse_resources(self, root: Any) -> List[Dict[str, Any]]:
        resources_elem = root.find(_ns('Resources'))
        if resources_elem is None:
            return []
        result = []
        for res in resources_elem.findall(_ns('Resource')):
            uid = _text(res, 'UID')
            if uid == '0':
                continue
            result.append({
                'uid': uid,
                'name': _text(res, 'Name'),
                'type': _text(res, 'Type', '1'),
                'cost': self._parse_cost(_text(res, 'Cost')),
            })
        return result

    def _build_wbs(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build WBS item list from task outline structure."""
        wbs_items = []
        outline_to_uid: Dict[str, str] = {}
        for task in tasks:
            if not task.get('summary') and task.get('outline_level', 1) > 1:
                continue
            outline_num = task.get('outline_number') or task.get('wbs', '')
            uid = task['uid']
            outline_to_uid[outline_num] = uid
            parent_outline = '.'.join(outline_num.split('.')[:-1]) if '.' in outline_num else None
            wbs_items.append({
                'uid': uid,
                'wbs_code': task.get('wbs') or outline_num,
                'title': task['name'],
                'level': task['outline_level'],
                'parent_outline': parent_outline,
            })
        # Resolve parent UIDs
        for item in wbs_items:
            po = item.pop('parent_outline', None)
            item['parent_uid'] = outline_to_uid.get(po) if po else None
        return wbs_items

    def _parse_baseline(self, root: Any, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build a budget list from task baselines."""
        budgets = []
        currency = _text(root, 'CurrencySymbol', 'BRL') or 'BRL'
        for task in tasks:
            cost = task.get('baseline_cost')
            if cost and float(cost) > 0:
                budgets.append({
                    'description': task['name'],
                    'planned_amount': cost,
                    'currency': currency,
                    'planned_date_start': task.get('baseline_start'),
                    'planned_date_end': task.get('baseline_finish'),
                    'category': 'other',
                })
        return budgets

    @staticmethod
    def _parse_duration_hours(duration: str) -> Optional[float]:
        """Convert ISO 8601 duration (PT8H) to hours float."""
        if not duration or not duration.startswith('PT'):
            return None
        try:
            hours = 0.0
            s = duration[2:]
            if 'H' in s:
                parts = s.split('H')
                hours += float(parts[0])
                s = parts[1]
            if 'M' in s:
                parts = s.split('M')
                hours += float(parts[0]) / 60
            return round(hours, 2) if hours else None
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _parse_cost(value: str) -> Optional[str]:
        """Return cost as string or None."""
        try:
            f = float(value)
            return str(f) if f >= 0 else None
        except (ValueError, TypeError):
            return None
