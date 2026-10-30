from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), default='SmartFinance User')
    monthly_income = db.Column(db.Float, default=50000.0)
    liquid_savings = db.Column(db.Float, default=150000.0)
    risk_tolerance = db.Column(db.String(30), default='moderate')  # conservative, moderate, aggressive
    currency = db.Column(db.String(5), default='₹')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='user', cascade='all, delete-orphan', lazy='dynamic')
    budgets = db.relationship('Budget', backref='user', cascade='all, delete-orphan', lazy='dynamic')
    debts = db.relationship('Debt', backref='user', cascade='all, delete-orphan', lazy='dynamic')
    risk_assessments = db.relationship('RiskAssessment', backref='user', cascade='all, delete-orphan', lazy='dynamic')
    goals = db.relationship('FinancialGoal', backref='user', cascade='all, delete-orphan', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'monthly_income': self.monthly_income,
            'liquid_savings': self.liquid_savings,
            'risk_tolerance': self.risk_tolerance,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    category = db.Column(db.String(60), nullable=False, index=True)
    transaction_date = db.Column(db.Date, default=date.today, nullable=False)
    description = db.Column(db.String(255), default='')
    is_anomaly = db.Column(db.Boolean, default=False)
    anomaly_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'amount': self.amount,
            'type': self.type,
            'category': self.category,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'description': self.description,
            'is_anomaly': self.is_anomaly,
            'anomaly_score': round(self.anomaly_score, 2),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category = db.Column(db.String(60), nullable=False)
    monthly_limit = db.Column(db.Float, nullable=False)
    alert_threshold = db.Column(db.Float, default=80.0)  # Trigger warning when reached
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'monthly_limit': self.monthly_limit,
            'alert_threshold': self.alert_threshold
        }


class Debt(db.Model):
    __tablename__ = 'debts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    debt_name = db.Column(db.String(120), nullable=False)
    debt_type = db.Column(db.String(40), default='Credit Card')  # Credit Card, Student Loan, Mortgage, Auto Loan, Personal Loan
    principal_balance = db.Column(db.Float, nullable=False)
    interest_rate_apr = db.Column(db.Float, nullable=False)  # in percentage e.g. 19.99
    minimum_payment = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'debt_name': self.debt_name,
            'debt_type': self.debt_type,
            'principal_balance': self.principal_balance,
            'interest_rate_apr': self.interest_rate_apr,
            'minimum_payment': self.minimum_payment
        }


class RiskAssessment(db.Model):
    __tablename__ = 'risk_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    health_score = db.Column(db.Float, nullable=False)  # 0 to 100
    risk_tier = db.Column(db.String(40), nullable=False)  # Low Risk, Moderate Risk, Elevated Risk, Critical Risk
    dti_ratio = db.Column(db.Float, nullable=False)
    savings_rate = db.Column(db.Float, nullable=False)
    emergency_runway_months = db.Column(db.Float, nullable=False)
    discretionary_ratio = db.Column(db.Float, default=0.0)
    expense_volatility = db.Column(db.Float, default=0.0)
    solvency_probability_12m = db.Column(db.Float, default=95.0)
    key_drivers = db.Column(db.Text, default='[]')  # JSON array of drivers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_drivers(self):
        try:
            return json.loads(self.key_drivers)
        except Exception:
            return []

    def set_drivers(self, drivers_list):
        self.key_drivers = json.dumps(drivers_list)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'health_score': round(self.health_score, 1),
            'risk_tier': self.risk_tier,
            'dti_ratio': round(self.dti_ratio, 1),
            'savings_rate': round(self.savings_rate, 1),
            'emergency_runway_months': round(self.emergency_runway_months, 1),
            'discretionary_ratio': round(self.discretionary_ratio, 1),
            'expense_volatility': round(self.expense_volatility, 2),
            'solvency_probability_12m': round(self.solvency_probability_12m, 1),
            'key_drivers': self.get_drivers(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }


class FinancialGoal(db.Model):
    __tablename__ = 'financial_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    target_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(60), default='Emergency Fund')
    status = db.Column(db.String(30), default='active')  # active, completed, paused
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def progress_percentage(self):
        if self.target_amount <= 0:
            return 100.0
        return min(100.0, round((self.current_amount / self.target_amount) * 100.0, 1))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'category': self.category,
            'status': self.status,
            'progress': self.progress_percentage()
        }

