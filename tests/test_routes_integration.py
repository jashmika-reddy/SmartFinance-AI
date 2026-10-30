from app import create_app
from models import db, User

def test_all_routes_accessible():
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # Check login page
        r_login = client.get('/login')
        assert r_login.status_code == 200
        
        # Check register page
        r_reg = client.get('/register')
        assert r_reg.status_code == 200
        
        # Login as sarah_resilient
        login_res = client.post('/login', data={
            'username_or_email': 'sarah_resilient',
            'password': 'password123'
        }, follow_redirects=True)
        assert login_res.status_code == 200
        assert b'Sarah Resilient' in login_res.data
        
        # Test Dashboard
        r_dash = client.get('/dashboard')
        assert r_dash.status_code == 200
        assert b'Executive Financial Dashboard' in r_dash.data
        
        # Test Transactions page
        r_tx = client.get('/transactions')
        assert r_tx.status_code == 200
        assert b'Transactions Ledger' in r_tx.data
        
        # Test Budgets page
        r_bg = client.get('/budgets')
        assert r_bg.status_code == 200
        assert b'Budget Envelopes' in r_bg.data
        
        # Test Debts page
        r_debt = client.get('/debts')
        assert r_debt.status_code == 200
        assert b'Debt Payoff Strategy Optimizer' in r_debt.data
        
        # Test Risk Assessment page
        r_risk = client.get('/risk-assessment')
        assert r_risk.status_code == 200
        assert b'Composite Financial Health Index' in r_risk.data
        
        # Test Stress Testing page
        r_stress = client.get('/stress-test')
        assert r_stress.status_code == 200
        assert b'Monte Carlo' in r_stress.data
        
        # Test Advisor page
        r_adv = client.get('/advisor')
        assert r_adv.status_code == 200
        assert b'Actionable Financial Health Prescriptions' in r_adv.data
        
        # Test Report page
        r_rep = client.get('/report')
        assert r_rep.status_code == 200
        assert b'Financial Risk & Solvency Audit' in r_rep.data
        
        # Test REST APIs
        r_api_cashflow = client.get('/api/v1/chart/cashflow')
        assert r_api_cashflow.status_code == 200
        assert 'income' in r_api_cashflow.json
        
        r_api_cat = client.get('/api/v1/chart/categories')
        assert r_api_cat.status_code == 200
        assert 'labels' in r_api_cat.json
        
        r_api_mc = client.get('/api/v1/chart/monte-carlo?scenario=baseline')
        assert r_api_mc.status_code == 200
        assert 'p50' in r_api_mc.json
        
        # Test Advisor Chat API
        r_chat = client.post('/advisor/chat', json={'message': 'Should I pay off debt or invest?'})
        assert r_chat.status_code == 200
        assert 'answer' in r_chat.json
        
        print("ALL ROUTES AND REST API ENDPOINTS VERIFIED SUCCESSFULLY!")

if __name__ == '__main__':
    test_all_routes_accessible()

