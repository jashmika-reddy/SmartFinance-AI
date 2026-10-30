import pytest
from app import create_app
from models import db, User

@pytest.fixture
def client():
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def test_user_password_hashing():
    user = User(username='testuser', email='test@test.com')
    user.set_password('SecretPass123')
    assert user.password_hash != 'SecretPass123'
    assert user.check_password('SecretPass123') is True
    assert user.check_password('WrongPass') is False

def test_registration_and_login_flow(client):
    # Register new account
    reg_res = client.post('/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'full_name': 'New Tester',
        'monthly_income': '5000',
        'liquid_savings': '10000',
        'risk_tolerance': 'moderate'
    }, follow_redirects=True)
    assert reg_res.status_code == 200
    assert b'Account created successfully' in reg_res.data or b'Executive Financial Dashboard' in reg_res.data

    # Logout
    logout_res = client.get('/logout', follow_redirects=True)
    assert b'logged out safely' in logout_res.data

    # Login
    login_res = client.post('/login', data={
        'username_or_email': 'newuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b'Executive Financial Dashboard' in login_res.data
