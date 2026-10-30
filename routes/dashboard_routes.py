from flask import Blueprint, render_template, redirect, url_for, g
from datetime import datetime, timedelta
from routes.auth_routes import login_required
from models import db, Transaction, Budget, Debt, RiskAssessment
from ml_models.risk_scorer import calculate_risk_assessment

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def home():
    if g.user:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@dashboard_bp.route('/dashboard')
@login_required
def index():
    user = g.user
    now = datetime.utcnow()
    thirty_days_ago = (now - timedelta(days=30)).date()
    
    # Transactions in last 30 days
    recent_30d_tx = [tx for tx in user.transactions if tx.transaction_date >= thirty_days_ago]
    if not recent_30d_tx:
        recent_30d_tx = list(user.transactions)
        
    income_30d = sum(tx.amount for tx in recent_30d_tx if tx.type == 'income')
    expense_30d = sum(tx.amount for tx in recent_30d_tx if tx.type == 'expense')
    
    # Monthly figures
    monthly_income = income_30d if income_30d > 0 else (user.monthly_income or 4000.0)
    monthly_expenses = expense_30d if expense_30d > 0 else (monthly_income * 0.70)
    net_cashflow = monthly_income - monthly_expenses
    savings_rate = ((monthly_income - monthly_expenses) / monthly_income * 100.0) if monthly_income > 0 else 0.0
    
    # Debts & Liabilities
    debts = list(user.debts)
    total_debt_balance = sum(d.principal_balance for d in debts)
    monthly_debt_obligations = sum(d.minimum_payment for d in debts)
    
    # Net Worth estimate: liquid savings - debt
    liquid_savings = user.liquid_savings or 0.0
    net_worth = liquid_savings - total_debt_balance
    
    # AI Risk Assessment
    assessment = calculate_risk_assessment(user)
    
    # Persist or update the risk assessment record
    latest_record = user.risk_assessments.order_by(RiskAssessment.created_at.desc()).first()
    if not latest_record or (now - latest_record.created_at).total_seconds() > 3600:
        new_assessment = RiskAssessment(
            user_id=user.id,
            health_score=assessment['health_score'],
            risk_tier=assessment['risk_tier'],
            dti_ratio=assessment['features']['dti_ratio'],
            savings_rate=assessment['features']['savings_rate'],
            emergency_runway_months=assessment['features']['emergency_runway_months'],
            discretionary_ratio=assessment['features']['discretionary_ratio'],
            expense_volatility=assessment['features']['expense_volatility'],
            solvency_probability_12m=assessment['solvency_probability_12m']
        )
        new_assessment.set_drivers(assessment['drivers'])
        db.session.add(new_assessment)
        db.session.commit()

    # Budgets Summary
    budgets = list(user.budgets)
    budget_stats = []
    for b in budgets:
        cat_spent = sum(
            tx.amount for tx in recent_30d_tx 
            if tx.type == 'expense' and tx.category.lower() == b.category.lower()
        )
        pct = (cat_spent / b.monthly_limit * 100.0) if b.monthly_limit > 0 else 0.0
        budget_stats.append({
            'category': b.category,
            'limit': b.monthly_limit,
            'spent': cat_spent,
            'remaining': max(0.0, b.monthly_limit - cat_spent),
            'percentage': round(pct, 1),
            'is_over': cat_spent > b.monthly_limit
        })

    # Recent transactions (last 7)
    recent_transactions = user.transactions.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).limit(7).all()
    
    # Anomalous transactions
    anomalies = [tx for tx in recent_30d_tx if tx.is_anomaly]
    
    return render_template(
        'dashboard.html',
        user=user,
        monthly_income=round(monthly_income, 2),
        monthly_expenses=round(monthly_expenses, 2),
        net_cashflow=round(net_cashflow, 2),
        savings_rate=round(savings_rate, 1),
        liquid_savings=round(liquid_savings, 2),
        total_debt_balance=round(total_debt_balance, 2),
        monthly_debt_obligations=round(monthly_debt_obligations, 2),
        net_worth=round(net_worth, 2),
        assessment=assessment,
        budget_stats=budget_stats,
        recent_transactions=recent_transactions,
        anomalies=anomalies
    )

