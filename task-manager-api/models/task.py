from database import db
from domain.clock import utc_now
from domain.constants import FINAL_STATUSES, STATUS_PENDING, DEFAULT_PRIORITY


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    # Apagar o usuário apaga suas tasks (antes feito "na mão" na rota); apagar a categoria
    # apenas desassocia (category_id -> NULL), política explícita no service de categorias.
    user = db.relationship('User', backref=db.backref('tasks', cascade='all, delete'))
    category = db.relationship('Category', backref='tasks')

    def is_overdue(self):
        """Única fonte da regra "atrasada": tem prazo, prazo passou e não está finalizada."""
        if not self.due_date:
            return False
        return self.due_date < utc_now() and self.status not in FINAL_STATUSES

    def tag_list(self):
        return self.tags.split(',') if self.tags else []

    def to_dict(self, with_overdue=False, with_relations=False):
        """Serialização única da entidade. Flags preservam o formato de cada endpoint."""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tag_list(),
        }
        if with_overdue:
            data['overdue'] = self.is_overdue()
        if with_relations:
            data['user_name'] = self.user.name if self.user else None
            data['category_name'] = self.category.name if self.category else None
        return data

    def to_summary_dict(self):
        """Formato reduzido usado por GET /users/<id>/tasks (contrato original)."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }
