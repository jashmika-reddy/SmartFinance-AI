from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from datetime import datetime, date
from routes.auth_routes import login_required
from models import db, Budget, Transaction
from currency_utils import format_inr

budget_bp = Blueprint('budgets', __name__)

DEFAULT_BUDGET_CATEGORIES = [
    'Housing', 'Food & Dining', 'Groceries', 'Utilities', 'Transportation',
    'Healthcare', 'Debt Payment', 'Entertainment', 'Personal Care', 'Shopping'
]

@budget_bp.route('/budgets')
@login_required
def index():
    user = g.user
    budgets = user.budgets.all()
    
    # Calculate spending in the current calendar month
    today = date.today()
    first_of_month = date(today.year, today.month, 1)
    
    current_month_txs = [
        tx for tx in user.transactions 
        if tx.type == 'expense' and tx.transaction_date >= first_of_month
    ]
    
    budget_items = []
    total_budgeted = 0.0
    total_spent = 0.0
    over_count = 0
    warning_count = 0
    
    for b in budgets:
        cat_spent = sum(
            tx.amount for tx in current_month_txs 
            if tx.category.lower() == b.category.lower()
        )
        total_budgeted += b.monthly_limit
        total_spent += cat_spent
        
        pct = (cat_spent / b.monthly_limit * 100.0) if b.monthly_limit > 0 else 0.0
        
        status = 'safe'
        if cat_spent > b.monthly_limit:
            status = 'danger'
            over_count += 1
        elif pct >= b.alert_threshold:
            status = 'warning'
            warning_count += 1
            
        budget_items.append({
            'id': b.id,
            'category': b.category,
            'monthly_limit': b.monthly_limit,
            'spent': round(cat_spent, 2),
            'remaining': round(max(0.0, b.monthly_limit - cat_spent), 2),
            'over_amount': round(max(0.0, cat_spent - b.monthly_limit), 2),
            'percentage': round(pct, 1),
            'alert_threshold': b.alert_threshold,
            'status': status
        })
        
    overall_pct = (total_spent / total_budgeted * 100.0) if total_budgeted > 0 else 0.0
    
    # Categories without budget
    existing_categories = {b.category.lower() for b in budgets}
    available_categories = [c for c in DEFAULT_BUDGET_CATEGORIES if c.lower() not in existing_categories]

    return render_template(
        'budgets.html',
        budgets=budget_items,
        total_budgeted=round(total_budgeted, 2),
        total_spent=round(total_spent, 2),
        total_remaining=round(max(0.0, total_budgeted - total_spent), 2),
        overall_percentage=round(overall_pct, 1),
        over_count=over_count,
        warning_count=warning_count,
        available_categories=available_categories,
        default_categories=DEFAULT_BUDGET_CATEGORIES
    )

@budget_bp.route('/budgets/add', methods=['POST'])
@login_required
def add():
    user = g.user
    category = request.form.get('category', '').strip()
    limit_str = request.form.get('monthly_limit', '0').strip()
    threshold_str = request.form.get('alert_threshold', '80').strip()
    
    if not category:
        flash('Please select or enter a category name.', 'danger')
        return redirect(url_for('budgets.index'))
        
    try:
        limit_val = float(limit_str)
        if limit_val <= 0:
            raise ValueError()
    except ValueError:
        flash('Monthly limit must be greater than zero.', 'danger')
        return redirect(url_for('budgets.index'))
        
    threshold_val = float(threshold_str or 80.0)
    
    # Check if budget for category already exists -> update it
    existing = Budget.query.filter_by(user_id=user.id, category=category).first()
    if existing:
        existing.monthly_limit = limit_val
        existing.alert_threshold = threshold_val
        flash(f'Budget for {category} updated to {format_inr(limit_val)}.', 'success')
    else:
        new_budget = Budget(
            user_id=user.id,
            category=category,
            monthly_limit=limit_val,
            alert_threshold=threshold_val
        )
        db.session.add(new_budget)
        flash(f'Budget envelope for {category} created!', 'success')
        
    db.session.commit()
    return redirect(url_for('budgets.index'))

@budget_bp.route('/budgets/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    user = g.user
    budget = Budget.query.filter_by(id=id, user_id=user.id).first_or_404()
    cat_name = budget.category
    db.session.delete(budget)
    db.session.commit()
    flash(f'Budget envelope for {cat_name} removed.', 'info')
    return redirect(url_for('budgets.index'))

