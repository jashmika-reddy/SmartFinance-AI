from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from routes.auth_routes import login_required
from models import db, Debt
from ml_models.debt_optimizer import DebtOptimizationEngine

debt_bp = Blueprint('debts', __name__)

DEBT_TYPES = ['Credit Card', 'Personal Loan', 'Student Loan', 'Auto Loan', 'Mortgage', 'Medical Debt', 'Other']

@debt_bp.route('/debts')
@login_required
def index():
    user = g.user
    debts = user.debts.order_by(Debt.interest_rate_apr.desc()).all()
    
    total_debt = sum(d.principal_balance for d in debts)
    total_min_payments = sum(d.minimum_payment for d in debts)
    
    # Calculate weighted average APR
    if total_debt > 0:
        weighted_apr = sum(d.principal_balance * (d.interest_rate_apr / 100.0) for d in debts) / total_debt * 100.0
    else:
        weighted_apr = 0.0
        
    extra_payment = float(request.args.get('extra', 200.0))
    
    # Run optimization simulation
    debts_payload = [
        {
            'id': d.id,
            'name': d.debt_name,
            'balance': d.principal_balance,
            'apr': d.interest_rate_apr,
            'min_payment': d.minimum_payment
        }
        for d in debts
    ]
    
    comparison = DebtOptimizationEngine.compare_strategies(debts_payload, extra_monthly_payment=extra_payment)
    
    return render_template(
        'debts.html',
        debts=debts,
        total_debt=round(total_debt, 2),
        total_min_payments=round(total_min_payments, 2),
        weighted_apr=round(weighted_apr, 2),
        extra_payment=extra_payment,
        comparison=comparison,
        debt_types=DEBT_TYPES
    )

@debt_bp.route('/debts/add', methods=['POST'])
@login_required
def add():
    user = g.user
    name = request.form.get('debt_name', '').strip()
    debt_type = request.form.get('debt_type', 'Credit Card')
    balance_str = request.form.get('principal_balance', '0')
    apr_str = request.form.get('interest_rate_apr', '0')
    min_payment_str = request.form.get('minimum_payment', '0')
    
    if not name:
        flash('Please enter a debt name (e.g. Chase Sapphire, Auto Loan).', 'danger')
        return redirect(url_for('debts.index'))
        
    try:
        balance = float(balance_str)
        apr = float(apr_str)
        min_payment = float(min_payment_str)
        if balance < 0 or apr < 0 or min_payment < 0:
            raise ValueError()
    except ValueError:
        flash('Please enter valid non-negative numbers for balance, APR, and payment.', 'danger')
        return redirect(url_for('debts.index'))
        
    new_debt = Debt(
        user_id=user.id,
        debt_name=name,
        debt_type=debt_type,
        principal_balance=balance,
        interest_rate_apr=apr,
        minimum_payment=min_payment
    )
    db.session.add(new_debt)
    db.session.commit()
    flash(f'Debt liability "{name}" recorded successfully.', 'success')
    return redirect(url_for('debts.index'))

@debt_bp.route('/debts/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    user = g.user
    debt = Debt.query.filter_by(id=id, user_id=user.id).first_or_404()
    
    debt.debt_name = request.form.get('debt_name', debt.debt_name).strip()
    debt.debt_type = request.form.get('debt_type', debt.debt_type)
    
    try:
        debt.principal_balance = float(request.form.get('principal_balance', debt.principal_balance))
        debt.interest_rate_apr = float(request.form.get('interest_rate_apr', debt.interest_rate_apr))
        debt.minimum_payment = float(request.form.get('minimum_payment', debt.minimum_payment))
    except ValueError:
        flash('Invalid numbers provided.', 'danger')
        return redirect(url_for('debts.index'))
        
    db.session.commit()
    flash(f'Debt "{debt.debt_name}" updated.', 'success')
    return redirect(url_for('debts.index'))

@debt_bp.route('/debts/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    user = g.user
    debt = Debt.query.filter_by(id=id, user_id=user.id).first_or_404()
    name = debt.debt_name
    db.session.delete(debt)
    db.session.commit()
    flash(f'Debt "{name}" deleted.', 'info')
    return redirect(url_for('debts.index'))

@debt_bp.route('/debts/api/simulate', methods=['POST'])
@login_required
def simulate_api():
    user = g.user
    data = request.get_json() or {}
    extra_payment = float(data.get('extra_payment', 150.0))
    
    debts = user.debts.all()
    debts_payload = [
        {
            'id': d.id,
            'name': d.debt_name,
            'balance': d.principal_balance,
            'apr': d.interest_rate_apr,
            'min_payment': d.minimum_payment
        }
        for d in debts
    ]
    
    comparison = DebtOptimizationEngine.compare_strategies(debts_payload, extra_monthly_payment=extra_payment)
    return jsonify(comparison)

