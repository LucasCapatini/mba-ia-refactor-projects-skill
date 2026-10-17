from werkzeug.security import generate_password_hash, check_password_hash

from database import db
from domain.clock import utc_now
from domain.constants import DEFAULT_ROLE


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self, task_count=None):
        """Serialização única da entidade. Nunca inclui a senha/hash (PB-04)."""
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }
        if task_count is not None:
            data['task_count'] = task_count
        return data

    def set_password(self, raw_password):
        # Hash com salt via werkzeug (dependência do Flask), no lugar de MD5 puro.
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def is_admin(self):
        return self.role == 'admin'
