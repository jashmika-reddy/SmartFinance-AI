import pytest
from datetime import date
from app import create_app
from models import db, User, Transaction, Budget

@pytest.fixture
def auth_client():
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    
    with app.app_context():
        db.create_all()
        user = User(username='ledger_user', email='ledger@example.com', monthly_income=6000.0, liquid_savings=15000.0)
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()
        
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            
        yield client, user
        db.session.remove()
        db.drop_all()

def test_transaction_crud(auth_client):
    client, user = auth_client
    
    # 1. Add Transaction
    res = client.post('/transactions/add', data={
        'title': 'Consulting Fee',
        'amount': '1500.00',
        'type': 'income',
        'category': 'Salary',
        'transaction_date': date.today().isoformat(),
        'description': 'Freelance income'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Consulting Fee' in res.data

    # Verify DB
    tx = Transaction.query.filter_by(title='Consulting Fee').first()
    assert tx is not None
    assert tx.amount == 1500.0
    assert tx.type == 'income'

    # 2. Add Expense
    res2 = client.post('/transactions/add', data={
        'title': 'Grocery Shopping',
        'amount': '120.50',
        'type': 'expense',
        'category': 'Groceries',
        'transaction_date': date.today().isoformat(),
        'description': 'Weekly food'
    }, follow_redirects=True)
    assert res2.status_code == 200
    assert b'Grocery Shopping' in res2.data

    # 3. Export CSV
    csv_res = client.get('/transactions/export')
    assert csv_res.status_code == 200
    assert 'text/csv' in csv_res.content_type
    assert b'Consulting Fee' in csv_res.data

def test_budget_envelopes(auth_client):
    client, user = auth_client
    
    # Create budget
    res = client.post('/budgets/add', data={
        'category': 'Food & Dining',
        'monthly_limit': '450.00',
        'alert_threshold': '80'
    }, follow_redirects=True)
    assert res.status_code == 200
    
    b = Budget.query.filter_by(category='Food & Dining').first()
    assert b is not None
    assert b.monthly_limit == 450.0