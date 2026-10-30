from flask import Blueprint, render_template, g
from datetime import datetime
from routes.auth_routes import login_required
from models import Transaction, Budget, Debt
from ml_models.risk_scorer import calculate_risk_assessment
from ml_models.advisor import FinancialAdvisorEngine

report_bp = Blueprint('report', __name__)

@report_bp.route('/report')
@login_required
def index():
    user = g.user
    assessment = calculate_risk_assessment(user)
    debts = user.debts.all()
    budgets = user.budgets.all()
    transactions = user.transactions.order_by(Transaction.transaction_date.desc()).all()
    
    anomalies = [tx for tx in transactions if tx.is_anomaly]
    
    recommendations = FinancialAdvisorEngine.generate_recommendations(
        user=user,
        assessment=assessment,
        debts=debts,
        budgets=budgets,
        transactions=transactions
    )
    
    total_debt = sum(d.principal_balance for d in debts)
    net_worth = (user.liquid_savings or 0.0) - total_debt
    
    return render_template(
        'report.html',
        user=user,
        assessment=assessment,
        debts=debts,
        total_debt=round(total_debt, 2),
        net_worth=round(net_worth, 2),
        budgets=budgets,
        anomalies=anomalies,
        recommendations=recommendations,
        generated_at=datetime.utcnow().strftime('%B %d, %Y - %H:%M UTC')
    )

