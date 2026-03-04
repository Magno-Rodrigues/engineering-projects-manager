"""WBS service — thin wrapper around WBSItem database operations."""
from typing import Any, Dict, List, Optional, Tuple

from app import db
from app.models.wbs_item import WBSItem


class WBSService:
    """Service class for WBS item management."""

    @staticmethod
    def get_project_wbs(project_id: int) -> List[WBSItem]:
        """Return all WBS items for a project ordered by level and code."""
        return (
            WBSItem.query.filter_by(project_id=project_id)
            .order_by(WBSItem.level, WBSItem.wbs_code)
            .all()
        )

    @staticmethod
    def create_wbs_item(
        project_id: int,
        created_by: int,
        wbs_code: str,
        title: str,
        level: int = 1,
        parent_id: Optional[int] = None,
        description: Optional[str] = None,
        estimated_effort: Optional[float] = None,
        responsible_user_id: Optional[int] = None,
    ) -> Tuple[Optional[WBSItem], Optional[str]]:
        """Create and persist a WBS item."""
        if not wbs_code or not wbs_code.strip():
            return None, 'wbs_code is required.'
        if not title or not title.strip():
            return None, 'title is required.'
        item = WBSItem(
            project_id=project_id,
            created_by=created_by,
            wbs_code=wbs_code.strip(),
            title=title.strip(),
            level=level,
            parent_id=parent_id,
            description=description,
            estimated_effort=estimated_effort,
            responsible_user_id=responsible_user_id,
        )
        db.session.add(item)
        db.session.commit()
        return item, None

    @staticmethod
    def bulk_create_wbs_items(
        project_id: int,
        created_by: int,
        items: List[Dict[str, Any]],
        source: str = 'manual',
    ) -> List[WBSItem]:
        """Bulk-insert WBS items, resolving parent relationships by uid.

        Each item dict should contain:
          - wbs_code, title, level, uid (temporary), parent_uid (temporary)
        """
        uid_to_id: Dict[str, int] = {}
        created: List[WBSItem] = []
        for item in items:
            parent_uid = item.get('parent_uid')
            parent_id = uid_to_id.get(parent_uid) if parent_uid else None
            wbs_item = WBSItem(
                project_id=project_id,
                created_by=created_by,
                wbs_code=item.get('wbs_code', ''),
                title=item.get('title', ''),
                level=item.get('level', 1),
                parent_id=parent_id,
                description=item.get('description'),
                estimated_effort=item.get('estimated_effort'),
                source=source,
            )
            db.session.add(wbs_item)
            db.session.flush()
            uid = item.get('uid')
            if uid:
                uid_to_id[uid] = wbs_item.id
            created.append(wbs_item)
        db.session.commit()
        return created
