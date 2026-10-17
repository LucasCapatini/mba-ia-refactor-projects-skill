"""Regras de negócio e acesso a dados de categorias (PB-05/PB-09/PB-15). Não conhece HTTP."""
import logging

from database import db, commit
from domain.exceptions import NotFoundError
from models.category import Category
from models.task import Task

logger = logging.getLogger(__name__)


def list_categories_with_task_count():
    """Uma consulta com agregação, no lugar de um count() por categoria."""
    statement = (
        db.select(Category, db.func.count(Task.id))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.id)
    )
    return db.session.execute(statement).all()


def get_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        raise NotFoundError('Categoria não encontrada')
    return category


def create_category(payload):
    category = Category(**payload)
    db.session.add(category)
    commit()
    logger.info('Categoria criada: id=%s', category.id)
    return category


def update_category(category, payload):
    for field, value in payload.items():
        setattr(category, field, value)
    commit()
    logger.info('Categoria atualizada: id=%s', category.id)
    return category


def delete_category(category):
    """Política explícita: tasks da categoria ficam sem categoria (category_id = NULL)."""
    category_id = category.id
    db.session.execute(db.update(Task).where(Task.category_id == category_id).values(category_id=None))
    db.session.delete(category)
    commit()
    logger.info('Categoria deletada: id=%s', category_id)
