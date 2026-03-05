"""Abstract base class for project plan importers."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseImporter(ABC):
    """Abstract base for MS Project and Primavera P6 importers."""

    def __init__(self) -> None:
        self.errors: List[str] = []

    @abstractmethod
    def parse(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """Parse the file content and return a structured data dict.

        Returns a dict with keys:
          - 'tasks': list of task dicts
          - 'wbs_items': list of WBS item dicts
          - 'resources': list of resource dicts
          - 'budgets': list of budget dicts
        """

    def validate(self, data: Dict[str, Any]) -> List[str]:
        """Validate parsed data and return a list of error strings."""
        errors = []
        if not isinstance(data.get('tasks'), list):
            errors.append('tasks must be a list')
        if not isinstance(data.get('wbs_items'), list):
            errors.append('wbs_items must be a list')
        return errors
