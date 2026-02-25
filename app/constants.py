"""Application constants."""

# Project Status
PROJECT_STATUS = [
    ('planning', 'Planejamento'),
    ('in_progress', 'Em Progresso'),
    ('on_hold', 'Pausado'),
    ('completed', 'Concluído'),
    ('cancelled', 'Cancelado'),
]

# Project Priority
PROJECT_PRIORITY = [
    ('low', 'Baixa'),
    ('medium', 'Média'),
    ('high', 'Alta'),
    ('critical', 'Crítica'),
]

# Project Categories
PROJECT_CATEGORIES = [
    ('development', 'Desenvolvimento'),
    ('design', 'Design'),
    ('infrastructure', 'Infraestrutura'),
    ('research', 'Pesquisa'),
    ('maintenance', 'Manutenção'),
]


"""Application constants and dropdown options."""

SUPERVISION_TYPES = [
    'Engenharia',
    'Implantação',
    'Operação',
    'Manutenção',
    'Qualidade',
    'Segurança',
    'TI',
    'Administrativo',
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

PROJECT_STATUS = ['planning', 'in_progress', 'on_hold', 'completed', 'cancelled']

PROJECT_PRIORITY = ['low', 'medium', 'high', 'critical']

PROJECT_CATEGORIES = ['Infrastructure', 'Software', 'Hardware', 'Consulting', 'Other']
