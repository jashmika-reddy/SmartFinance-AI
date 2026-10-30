import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smartfinance-ai-super-secret-key-2026-btech')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f'sqlite:///{os.path.join(BASE_DIR, "smartfinance.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Financial Risk Threshold Benchmarks
    RISK_THRESHOLDS = {
        'dti_optimal': 20.0,
        'dti_warning': 36.0,
        'dti_critical': 50.0,
        'emergency_fund_months_min': 3.0,
        'emergency_fund_months_ideal': 6.0,
        'savings_rate_healthy': 20.0
    }

