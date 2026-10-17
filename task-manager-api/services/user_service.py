"""Regras de negócio e acesso a dados de usuários (PB-05/PB-09). Não conhece HTTP."""
import logging

from database import db, commit
from domain.exceptions import NotFoundError, ConflictError
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)


def list_users_with_task_count():
    """Uma consulta com agregação, no lugar de len(user.tasks) por usuário."""
    statement = (
        db.select(User, db.func.count(Task.id))
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
    )
    return db.session.execute(statement).all()


def get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError('Usuário não encontrado')
    return user


def get_user_by_email(email):
    return db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()


def list_user_tasks(user_id):
    return db.session.execute(db.select(Task).filter_by(user_id=user_id).order_by(Task.id)).scalars().all()


def _ensure_email_available(email, current_user_id=None):
    existing = get_user_by_email(email)
    if existing is not None and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')


def create_user(payload):
    _ensure_email_available(payload['email'])
    user = User(name=payload['name'], email=payload['email'], role=payload['role'])
    user.set_password(payload['password'])
    db.session.add(user)
    commit()
    logger.info('Usuário criado: id=%s', user.id)
    return user


def update_user(user, payload):
    if 'email' in payload:
        _ensure_email_available(payload['email'], current_user_id=user.id)
    for field, value in payload.items():
        if field == 'password':
            user.set_password(value)
        else:
            setattr(user, field, value)
    commit()
    logger.info('Usuário atualizado: id=%s', user.id)
    return user


def delete_user(user):
    """A cascata user -> tasks está declarada no model (PB-15), não mais na rota."""
    user_id = user.id
    db.session.delete(user)
    commit()
    logger.info('Usuário deletado: id=%s', user_id)
