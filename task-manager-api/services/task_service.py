"""Regras de negócio e acesso a dados de tasks (PB-05/PB-09). Não conhece HTTP."""
import logging

from sqlalchemy.orm import joinedload

from database import db, commit
from domain.clock import utc_now
from domain.constants import VALID_STATUSES, FINAL_STATUSES, STATUS_DONE
from domain.exceptions import NotFoundError
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import calculate_percentage

logger = logging.getLogger(__name__)


def list_tasks():
    """Lista com user e category carregados numa única consulta (sem N+1)."""
    statement = db.select(Task).options(joinedload(Task.user), joinedload(Task.category)).order_by(Task.id)
    return db.session.execute(statement).scalars().all()


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFoundError('Task não encontrada')
    return task


def _ensure_references(payload):
    """user_id/category_id informados precisam existir (404, como no contrato original)."""
    user_id = payload.get('user_id')
    if user_id is not None and db.session.get(User, user_id) is None:
        raise NotFoundError('Usuário não encontrado')
    category_id = payload.get('category_id')
    if category_id is not None and db.session.get(Category, category_id) is None:
        raise NotFoundError('Categoria não encontrada')


def create_task(payload):
    _ensure_references(payload)
    task = Task(**payload)
    db.session.add(task)
    commit()
    logger.info('Task criada: id=%s', task.id)
    return task


def update_task(task, payload):
    _ensure_references(payload)
    for field, value in payload.items():
        setattr(task, field, value)
    task.updated_at = utc_now()
    commit()
    logger.info('Task atualizada: id=%s', task.id)
    return task


def delete_task(task):
    task_id = task.id
    db.session.delete(task)
    commit()
    logger.info('Task deletada: id=%s', task_id)


def search_tasks(filters):
    statement = db.select(Task)
    if filters['query']:
        pattern = f"%{filters['query']}%"
        statement = statement.where(db.or_(Task.title.like(pattern), Task.description.like(pattern)))
    if filters['status']:
        statement = statement.where(Task.status == filters['status'])
    if filters['priority'] is not None:
        statement = statement.where(Task.priority == filters['priority'])
    if filters['user_id'] is not None:
        statement = statement.where(Task.user_id == filters['user_id'])
    return db.session.execute(statement.order_by(Task.id)).scalars().all()


def overdue_condition():
    """Mesma regra de Task.is_overdue(), em SQL, para contagens e listagens."""
    return db.and_(
        Task.due_date.is_not(None),
        Task.due_date < utc_now(),
        db.or_(Task.status.is_(None), Task.status.not_in(FINAL_STATUSES)),
    )


def count_by_status():
    rows = db.session.execute(db.select(Task.status, db.func.count(Task.id)).group_by(Task.status)).all()
    counts = {status: 0 for status in VALID_STATUSES}
    for status, count in rows:
        if status in counts:
            counts[status] = count
    return counts


def count_all():
    return db.session.execute(db.select(db.func.count(Task.id))).scalar_one()


def count_overdue():
    return db.session.execute(db.select(db.func.count(Task.id)).where(overdue_condition())).scalar_one()


def task_stats():
    total = count_all()
    by_status = count_by_status()
    return {
        'total': total,
        'pending': by_status['pending'],
        'in_progress': by_status['in_progress'],
        'done': by_status['done'],
        'cancelled': by_status['cancelled'],
        'overdue': count_overdue(),
        'completion_rate': calculate_percentage(by_status[STATUS_DONE], total),
    }
