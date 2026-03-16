"""Application constants and dropdown options."""

# ---------------------------------------------------------------------------
# Business / Personnel Constants
# ---------------------------------------------------------------------------

SUPERVISION_TYPES = [
    'Engenharia',
    'Implantação',
    'Operação',
    'Manutenção',
    'Qualidade',
    'Segurança',
    'TI',
    'Administrativo',
    'Planejamento',
]

COMPANIES = [
    'Vale',
    'Concremat',
    'TSX',
    'Engevix',
    'Arcadis',
    'Worley',
    'Hatch',
    'SNC-Lavalin',
    'CMRDA',
]

STATES = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
    'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
    'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
]

MEASUREMENT_CRITERIA = [
    'Critério-01',
    'Critério-02',
    'Critério-03',
    'Critério-04',
    'Critério-05',
]

USER_STATUS = [
    'Ativo',
    'Desligado',
    'Férias',
]

USER_ROLES = [
    'Administrador',
    'Usuário',
]

# ---------------------------------------------------------------------------
# Access Control Constants
# ---------------------------------------------------------------------------

# Module names for the access control system
VALID_MODULES = ['projects', 'tasks', 'reports', 'apontamentos', 'pmbok', 'admin']

# Functions available per module
MODULE_FUNCTIONS = {
    'projects': ['view', 'create', 'edit', 'delete'],
    'tasks': ['view', 'create', 'edit', 'delete'],
    'reports': ['view', 'create', 'edit', 'delete', 'export'],
    'apontamentos': ['view', 'create', 'edit', 'delete', 'manage_cycles'],
    'pmbok': ['view', 'create', 'edit', 'delete'],
    'admin': ['manage_users', 'manage_permissions', 'manage_config'],
}

# Human-readable labels for module names
MODULE_DISPLAY_NAMES = {
    'projects': 'Projetos',
    'tasks': 'Tarefas',
    'reports': 'Relatórios',
    'apontamentos': 'Apontamentos',
    'pmbok': 'PMBOK',
    'admin': 'Administração',
}

# Metadata for each module (used in dashboard module grid)
MODULES_METADATA = {
    'projects': {
        'label': 'Projetos',
        'description': 'Gerencie seus projetos',
        'color': 'blue',
        'route_name': 'projects.index',
        'icon': 'folder',
    },
    'tasks': {
        'label': 'Tarefas',
        'description': 'Gerencie suas tarefas',
        'color': 'amber',
        'route_name': 'projects.index',
        'icon': 'clipboard',
    },
    'reports': {
        'label': 'Relatórios',
        'description': 'Relatórios e análises',
        'color': 'emerald',
        'route_name': 'projects.index',
        'icon': 'chart',
    },
    'apontamentos': {
        'label': 'Apontamentos',
        'description': 'Registro de apontamentos',
        'color': 'purple',
        'route_name': 'timeentry.index',
        'icon': 'clock',
    },
    'pmbok': {
        'label': 'PMBOK',
        'description': 'Guia PMBOK',
        'color': 'rose',
        'route_name': 'projects.index',
        'icon': 'book',
    },
    'admin': {
        'label': 'Administração',
        'description': 'Painel administrativo',
        'color': 'gray',
        'route_name': 'admin.dashboard',
        'icon': 'cog',
    },
}

# Human-readable labels for function names
FUNCTION_DISPLAY_NAMES = {
    'view': 'Visualizar',
    'create': 'Criar',
    'edit': 'Editar',
    'delete': 'Excluir',
    'export': 'Exportar',
    'manage_cycles': 'Gerenciar Ciclos',
    'manage_users': 'Gerenciar Usuários',
    'manage_permissions': 'Gerenciar Permissões',
    'manage_config': 'Gerenciar Configurações',
}

# ---------------------------------------------------------------------------
# Project Management Constants
# ---------------------------------------------------------------------------

PROJECT_STATUS = ['planning', 'in_progress', 'on_hold', 'completed', 'cancelled']

PROJECT_PRIORITY = ['low', 'medium', 'high', 'critical']

PROJECT_CATEGORIES = ['Infrastructure', 'Software', 'Hardware', 'Consulting', 'Other']

# ---------------------------------------------------------------------------
# Time Entry / Apontamentos
# ---------------------------------------------------------------------------

# Maximum hours allowed per user per day
MAX_HOURS_PER_DAY = 10

# Default hour types used in time entries
HOUR_TYPES = [
    'Normal',
    'Extra',
]
