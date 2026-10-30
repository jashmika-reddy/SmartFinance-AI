from flask import Blueprint, jsonify, request, g
from datetime import datetime, timedelta, date
from routes.auth_routes import login_required
from models import Transaction
from ml_models.risk_scorer import calculate_risk_assessment
from ml_models.monte_carlo import MonteCarloStressTester

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/summary')
@login_required
def summary():
    user = g.user
    assessment = calculate_risk_assessment(user)
    return jsonify({
        'user': user.to_dict(),
        'assessment': assessment
    })

@api_bp.route('/chart/cashflow')
@login_required
def cashflow_chart():
    user = g.user
    
    # Aggregate transactions by month for the last 6 months
    today = date.today()
    months_labels = []
    income_series = []
    expense_series = []
    
    for i in range(5, -1, -1):
        # Calculate year and month
        month_num = today.month - i
        year_num = today.year
        while month_num <= 0:
            month_num += 12
            year_num -= 1
            
        m_start = date(year_num, month_num, 1)
        if month_num == 12:
            m_end = date(year_num + 1, 1, 1)
        else:
            m_end = date(year_num, month_num + 1, 1)
            
        m_name = m_start.strftime('%b %Y')
        months_labels.append(m_name)
        
        # Monthly totals
        m_txs = [
            tx for tx in user.transactions 
            if tx.transaction_date >= m_start and tx.transaction_date < m_end
        ]
        inc = sum(tx.amount for tx in m_txs if tx.type == 'income')
        exp = sum(tx.amount for tx in m_txs if tx.type == 'expense')
        
        income_series.append(round(inc, 2))
        expense_series.append(round(exp, 2))
        
    return jsonify({
        'labels': months_labels,
        'income': income_series,
        'expense': expense_series
    })

@api_bp.route('/chart/categories')
@login_required
def categories_chart():
    user = g.user
    # Last 60 days expense category breakdown
    cutoff = date.today() - timedelta(days=60)
    txs = [tx for tx in user.transactions if tx.type == 'expense' and tx.transaction_date >= cutoff]
    if not txs:
        txs = [tx for tx in user.transactions if tx.type == 'expense']
        
    category_totals = {}
    for tx in txs:
        cat = tx.category
        category_totals[cat] = category_totals.get(cat, 0.0) + tx.amount
        
    # Sort descending
    sorted_items = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    labels = [item[0] for item in sorted_items]
    values = [round(item[1], 2) for item in sorted_items]
    
    return jsonify({
        'labels': labels,
        'values': values
    })

@api_bp.route('/chart/monte-carlo')
@login_required
def monte_carlo_chart():
    user = g.user
    scenario = request.args.get('scenario', 'baseline')
    
    assessment = calculate_risk_assessment(user)
    features = assessment['features']
    
    initial_wealth = user.liquid_savings or 5000.0
    monthly_income = features['monthly_income']
    monthly_expenses = features['monthly_expenses']
    
    simulations = MonteCarloStressTester.run_simulations(
        initial_wealth=initial_wealth,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        horizon_months=12,
        n_simulations=1000
    )
    
    sc_data = simulations.get(scenario, simulations['baseline'])
    return jsonify(sc_data)

