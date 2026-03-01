from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """User model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    expenses = db.relationship('Expense', backref='user', lazy=True)
    budgets = db.relationship('Budget', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.name}>'

class Expense(db.Model):
    """Expense model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    merchant = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.Text)
    receipt_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'merchant': self.merchant,
            'amount': self.amount,
            'category': self.category,
            'date': self.date.isoformat(),
            'description': self.description
        }
    
    def __repr__(self):
        return f'<Expense {self.merchant} - ${self.amount}>'

class Budget(db.Model):
    """Budget model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_spent(self, user_id):
        """Calculate total spent in this category"""
        from models import Expense
        expenses = Expense.query.filter_by(
            user_id=user_id, 
            category=self.category
        ).all()
        return sum(exp.amount for exp in expenses)
    
    def get_remaining(self, user_id):
        """Calculate remaining budget"""
        return self.amount - self.get_spent(user_id)
    
    def __repr__(self):
        return f'<Budget {self.category} - ${self.amount}>'
