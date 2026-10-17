"""Relatórios (PB-05/PB-09): agregações em SQL no lugar de loops com uma consulta por item."""
from datetime import timedelta

from sqlalchemy import case

from database import db
from domain.clock import utc_now
from domain.constants import (PRIORITY_LABELS, STATUS_DONE, STATUS_PENDING, STATUS_IN_PROGRESS,
                              STATUS_CANCELLED, FINAL_STATUSES, HIGH_PRIORITY_THRESHOLD, RECENT_ACTIVITY_DAYS)
from models.task import Task
from models.user import User
from models.category import Category
from services import task_service
from utils.helpers import calculate_percentage


def _count(model):
    return db.session.execute(db.select(db.func.count(model.id))).scalar_one()


def _count_by_priority():
    rows = db.session.execute(db.select(Task.priority, db.func.count(Task.id)).group_by(Task.priority)).all()
    counts = {label: 0 for label in PRIORITY_LABELS.values()}
    for priority, count in rows:
        if priority in PRIORITY_LABELS:
            counts[PRIORITY_LABELS[priority]] = count
    return counts


def _overdue_tasks(now):
    tasks = db.session.execute(
        db.select(Task).where(task_service.overdue_condition()).order_by(Task.id)
    ).scalars().all()
    return [
        {
            'id': task.id,
            'title': task.title,
            'due_date': str(task.due_date),
            'days_overdue': (now - task.due_date).days,
        }
        for task in tasks
    ]


def _user_productivity():
    """Total e concluídas por usuário numa única consulta agregada."""
    completed_expr = db.func.coalesce(db.func.sum(case((Task.status == STATUS_DONE, 1), else_=0)), 0)
    statement = (
        db.select(User.id, User.name, db.func.count(Task.id), completed_expr)
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
    )
    return [
        {
            'user_id': user_id,
            'user_name': user_name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        }
        for user_id, user_name, total, completed in db.session.execute(statement).all()
    ]


def summary_report():
    now = utc_now()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    by_status = task_service.count_by_status()
    overdue_list = _overdue_tasks(now)

    recent_created = db.session.execute(
        db.select(db.func.count(Task.id)).where(Task.created_at >= since)
    ).scalar_one()
    recent_done = db.session.execute(
        db.select(db.func.count(Task.id)).where(Task.status == STATUS_DONE, Task.updated_at >= since)
    ).scalar_one()

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': task_service.count_all(),
            'total_users': _count(User),
            'total_categories': _count(Category),
        },
        'tasks_by_status': {
            'pending': by_status[STATUS_PENDING],
            'in_progress': by_status[STATUS_IN_PROGRESS],
            'done': by_status[STATUS_DONE],
            'cancelled': by_status[STATUS_CANCELLED],
        },
        'tasks_by_priority': _count_by_priority(),
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_created,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': _user_productivity(),
    }


def user_report(user):
    tasks = db.session.execute(db.select(Task).filter_by(user_id=user.id)).scalars().all()
    counts = {STATUS_DONE: 0, STATUS_PENDING: 0, STATUS_IN_PROGRESS: 0, STATUS_CANCELLED: 0}
    overdue = 0
    high_priority = 0
    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1
        if task.priority <= HIGH_PRIORITY_THRESHOLD:
            high_priority += 1
        if task.is_overdue():
            overdue += 1

    total = len(tasks)
    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': counts[STATUS_DONE],
            'pending': counts[STATUS_PENDING],
            'in_progress': counts[STATUS_IN_PROGRESS],
            'cancelled': counts[STATUS_CANCELLED],
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(counts[STATUS_DONE], total),
        },
    }
