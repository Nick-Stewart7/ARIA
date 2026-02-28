from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from ARIA.artifacts.code.app import db

class Role(db.Model):
    """Role model for user permissions"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }

class User(UserMixin, db.Model):
    """User model with authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Foreign keys
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False, default=2)
    
    # Relationships
    tasks = db.relationship('Task', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        from flask_bcrypt import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Set password hash"""
        from flask_bcrypt import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def to_dict(self, include_tasks=False):
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'role': self.role.name if self.role else None
        }
        if include_tasks:
            data['tasks'] = [task.to_dict() for task in self.tasks]
        return data

class Task(db.Model):
    """Task model for todo items"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Add indexes for common queries
    __table_args__ = (
        db.Index('idx_user_completed', 'user_id', 'completed'),
        db.Index('idx_user_priority', 'user_id', 'priority'),
    )
    
    def __repr__(self):
        return f'<Task {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user_id': self.user_id,
            'username': self.user.username if self.user else None
        }
    
    @classmethod
    def get_user_tasks(cls, user_id, completed=None, priority=None):
        """Get tasks for a user with optional filters"""
        query = cls.query.filter_by(user_id=user_id)
        
        if completed is not None:
            query = query.filter_by(completed=completed)
        
        if priority:
            query = query.filter_by(priority=priority)
        
        return query.order_by(cls.created_at.desc()).all()
    
    def update_from_dict(self, data):
        """Update task from dictionary data"""
        allowed_fields = ['title', 'description', 'completed', 'priority', 'due_date']
        
        for field in allowed_fields:
            if field in data:
                if field == 'due_date' and data[field]:
                    # Parse ISO format date string
                    if isinstance(data[field], str):
                        try:
                            data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                        except ValueError:
                            continue
                setattr(self, field, data[field])
        
        self.updated_at = datetime.utcnow()