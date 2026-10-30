from flask import Blueprint, render_template, request, redirect, url_for, flash, g, Response
from datetime import datetime, date
import csv
import io
from routes.auth_routes import login_required
from models import db, Transaction
from ml_models.anomaly_detector import TransactionAnomalyDetector

transaction_bp = Blueprint('transactions', __name__)

CATEGORIES = [
    'Housing', 'Food & Dining', 'Groceries', 'Utilities', 'Transportation',
    'Healthcare', 'Debt Payment', 'Entertainment', 'Personal Care',
    'Shopping', 'Education', 'Salary', 'Freelance', 'Investments', 'Other'
]

@transaction_bp.route('/transactions')
@login_required
def index():
    user = g.user
    query = user.transactions
    
    # Filtering parameters
    search = request.args.get('search', '').strip()
    cat_filter = request.args.get('category', '').strip()
    type_filter = request.args.get('type', '').strip()
    only_anomalies = request.args.get('anomalies', '') == '1'
    
    if search:
        query = query.filter((Transaction.title.ilike(f'%{search}%')) | (Transaction.description.ilike(f'%{search}%')))
    if cat_filter:
        query = query.filter(Transaction.category == cat_filter)
    if type_filter:
        query = query.filter(Transaction.type == type_filter)
    if only_anomalies:
        query = query.filter(Transaction.is_anomaly == True)
        
    transactions = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).all()
    
    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    net_total = total_income - total_expense
    
    return render_template(
        'transactions.html',
        transactions=transactions,
        categories=CATEGORIES,
        total_income=round(total_income, 2),
        total_expense=round(total_expense, 2),
        net_total=round(net_total, 2),
        current_search=search,
        current_category=cat_filter,
        current_type=type_filter,
        only_anomalies=only_anomalies
    )

@transaction_bp.route('/transactions/add', methods=['POST'])
@login_required
def add():
    user = g.user
    title = request.form.get('title', '').strip()
    amount_str = request.form.get('amount', '0').strip()
    tx_type = request.form.get('type', 'expense')
    category = request.form.get('category', 'Other')
    date_str = request.form.get('transaction_date', '')
    description = request.form.get('description', '').strip()
    
    if not title:
        flash('Please enter a transaction title.', 'danger')
        return redirect(url_for('transactions.index'))
        
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError()
    except ValueError:
        flash('Amount must be a positive number.', 'danger')
        return redirect(url_for('transactions.index'))
        
    try:
        tx_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    except ValueError:
        tx_date = date.today()

    # Evaluate Anomaly if expense
    is_anomaly = False
    anomaly_score = 0.0
    if tx_type == 'expense':
        past_txs = user.transactions.all()
        is_anomaly, anomaly_score, reason = TransactionAnomalyDetector.evaluate_transaction(
            amount, category, past_txs
        )
        if is_anomaly:
            flash(f'⚠️ Anomaly Alert: {reason}', 'warning')

    new_tx = Transaction(
        user_id=user.id,
        title=title,
        amount=amount,
        type=tx_type,
        category=category,
        transaction_date=tx_date,
        description=description,
        is_anomaly=is_anomaly,
        anomaly_score=anomaly_score
    )
    
    # Update user's liquid savings balance accordingly
    if tx_type == 'income':
        user.liquid_savings = (user.liquid_savings or 0.0) + amount
    elif tx_type == 'expense':
        user.liquid_savings = max(0.0, (user.liquid_savings or 0.0) - amount)
        
    db.session.add(new_tx)
    db.session.commit()
    
    flash(f'Transaction "{title}" added successfully!', 'success')
    return redirect(url_for('transactions.index'))

@transaction_bp.route('/transactions/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    user = g.user
    tx = Transaction.query.filter_by(id=id, user_id=user.id).first_or_404()
    
    old_type = tx.type
    old_amount = tx.amount
    
    tx.title = request.form.get('title', tx.title).strip()
    try:
        new_amount = float(request.form.get('amount', tx.amount))
        if new_amount <= 0:
            raise ValueError()
        tx.amount = new_amount
    except ValueError:
        flash('Invalid amount entered.', 'danger')
        return redirect(url_for('transactions.index'))
        
    tx.type = request.form.get('type', tx.type)
    tx.category = request.form.get('category', tx.category)
    date_str = request.form.get('transaction_date', '')
    if date_str:
        try:
            tx.transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    tx.description = request.form.get('description', tx.description).strip()
    
    # Rebalance liquid savings difference
    if old_type == 'income':
        user.liquid_savings = max(0.0, (user.liquid_savings or 0.0) - old_amount)
    else:
        user.liquid_savings = (user.liquid_savings or 0.0) + old_amount
        
    if tx.type == 'income':
        user.liquid_savings = (user.liquid_savings or 0.0) + tx.amount
    else:
        user.liquid_savings = max(0.0, (user.liquid_savings or 0.0) - tx.amount)
        
    db.session.commit()
    flash('Transaction updated successfully.', 'success')
    return redirect(url_for('transactions.index'))

@transaction_bp.route('/transactions/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    user = g.user
    tx = Transaction.query.filter_by(id=id, user_id=user.id).first_or_404()
    
    # Revert liquid balance
    if tx.type == 'income':
        user.liquid_savings = max(0.0, (user.liquid_savings or 0.0) - tx.amount)
    elif tx.type == 'expense':
        user.liquid_savings = (user.liquid_savings or 0.0) + tx.amount
        
    db.session.delete(tx)
    db.session.commit()
    flash('Transaction deleted successfully.', 'info')
    return redirect(url_for('transactions.index'))

@transaction_bp.route('/transactions/export')
@login_required
def export_csv():
    user = g.user
    transactions = user.transactions.order_by(Transaction.transaction_date.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Date', 'Title', 'Type', 'Category', 'Amount', 'Is Anomaly', 'Anomaly Score', 'Description'])
    
    for tx in transactions:
        writer.writerow([
            tx.id,
            tx.transaction_date.isoformat(),
            tx.title,
            tx.type,
            tx.category,
            f"{tx.amount:.2f}",
            'YES' if tx.is_anomaly else 'NO',
            f"{tx.anomaly_score:.2f}",
            tx.description
        ])
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename=smartfinance_transactions_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
    )

