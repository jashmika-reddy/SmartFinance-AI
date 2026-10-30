from flask import Blueprint, render_template, request, jsonify, g
from routes.auth_routes import login_required
from models import Transaction, Budget, Debt
from ml_models.risk_scorer import calculate_risk_assessment
from ml_models.advisor import FinancialAdvisorEngine

advisor_bp = Blueprint('advisor', __name__)

@advisor_bp.route('/advisor')
@login_required
def index():
    user = g.user
    assessment = calculate_risk_assessment(user)
    debts = user.debts.all()
    budgets = user.budgets.all()
    transactions = user.transactions.all()
    
    recommendations = FinancialAdvisorEngine.generate_recommendations(
        user=user,
        assessment=assessment,
        debts=debts,
        budgets=budgets,
        transactions=transactions
    )
    
    return render_template(
        'advisor.html',
        user=user,
        assessment=assessment,
        recommendations=recommendations
    )

@advisor_bp.route('/advisor/chat', methods=['POST'])
@login_required
def chat():
    user = g.user
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message cannot be empty.'}), 400
        
    assessment = calculate_risk_assessment(user)
    context = {
        'health_score': assessment['health_score'],
        'risk_tier': assessment['risk_tier'],
        'dti': assessment['features']['dti_ratio'],
        'runway': assessment['features']['emergency_runway_months'],
        'savings_rate': assessment['features']['savings_rate'],
        'user_name': user.full_name or user.username
    }
    
    response = FinancialAdvisorEngine.answer_query(message, context)
    return jsonify(response)

