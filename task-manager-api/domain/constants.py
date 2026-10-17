"""Constantes de domínio (PB-13). Valores idênticos aos literais originais das rotas."""
VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
FINAL_STATUSES = ('done', 'cancelled')
STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'

VALID_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 4

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2          # prioridade <= 2 conta como "alta" no relatório
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

DEFAULT_COLOR = '#000000'
DATE_FORMAT = '%Y-%m-%d'
RECENT_ACTIVITY_DAYS = 7
