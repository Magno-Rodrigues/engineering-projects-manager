"""Task model."""
from datetime import datetime, timezone
from decimal import Decimal
from app import db
#from app.models.wbs import WBSItem

# PMBOK Knowledge Areas (10 knowledge areas)
PMBOK_KNOWLEDGE_AREAS = [
    ('integration', 'Integração'),
    ('scope', 'Escopo'),
    ('schedule', 'Cronograma'),
    ('costs', 'Custos'),
    ('quality', 'Qualidade'),
    ('resources', 'Recursos'),
    ('communication', 'Comunicação'),
    ('risk', 'Risco'),
    ('procurement', 'Aquisições'),
    ('stakeholders', 'Partes Interessadas'),
]

# PMBOK Process Groups (5 process groups)
PMBOK_PROCESS_GROUPS = [
    ('initiating', 'Iniciação'),
    ('planning', 'Planejamento'),
    ('executing', 'Execução'),
    ('monitoring', 'Monitoramento e Controle'),
    ('closing', 'Encerramento'),
]


class Task(db.Model):
    """Task model for project task management."""

    __tablename__ = 'tasks'

    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(256), nullable=False)
    description: str = db.Column(db.Text)
    status: str = db.Column(db.String(32), default='todo')
    priority: str = db.Column(db.String(16), default='medium')
    due_date: datetime = db.Column(db.Date)
    project_id: int = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    assignee_id: int = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # PMBOK fields
    pmbok_knowledge_area: str = db.Column(db.String(32), nullable=True)
    pmbok_process_group: str = db.Column(db.String(32), nullable=True)
    wbs_item_id: int = db.Column(db.Integer, db.ForeignKey('wbs_items.id'), nullable=True)
    start_date: datetime = db.Column(db.Date, nullable=True)
    estimated_effort: Decimal = db.Column(db.Numeric(10, 2), nullable=True)
    progress: int = db.Column(db.Integer, default=0)
    dependencies: str = db.Column(db.Text, nullable=True)
    source: str = db.Column(db.String(32), nullable=False, default='manual', server_default='manual')

    # Relationships
    #wbs_item = db.relationship('WBSItem', foreign_keys='Task.wbs_item_id', backref=db.backref('tasks', lazy='dynamic'))

    def __init__(self, **kwargs) -> None:
        """Initialize Task with default status and priority."""
        kwargs.setdefault('status', 'todo')
        kwargs.setdefault('priority', 'medium')
        kwargs.setdefault('progress', 0)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f'<Task {self.title}>'
