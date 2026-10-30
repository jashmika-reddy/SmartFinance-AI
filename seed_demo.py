import sys
import os

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import date, timedelta
from app import create_app
from models import db, User, Transaction, Budget, Debt, RiskAssessment
from ml_models.risk_scorer import calculate_risk_assessment

def seed_database():
    app = create_app()
    with app.app_context():
        print("Resetting and initializing database...")
        db.drop_all()
        db.create_all()

        today = date.today()

        # ==========================================
        # 1. Sarah Resilient (Low Risk / Model Profile)
        # ==========================================
        print("Creating User: sarah_resilient...")
        sarah = User(
            username='sarah_resilient',
            email='sarah@example.com',
            full_name='Sarah Resilient',
            monthly_income=7500.0,
            liquid_savings=28500.0,
            risk_tolerance='moderate',
            currency='$'
        )
        sarah.set_password('password123')
        db.session.add(sarah)
        db.session.commit()

        # Debts: Low interest auto loan
        db.session.add(Debt(
            user_id=sarah.id,
            debt_name='Toyota Auto Loan',
            debt_type='Auto Loan',
            principal_balance=5800.0,
            interest_rate_apr=4.25,
            minimum_payment=220.0
        ))

        # Budgets
        sarah_budgets = [
            ('Housing', 1800.0),
            ('Groceries', 650.0),
            ('Food & Dining', 400.0),
            ('Utilities', 250.0),
            ('Transportation', 350.0),
            ('Entertainment', 300.0)
        ]
        for cat, limit in sarah_budgets:
            db.session.add(Budget(user_id=sarah.id, category=cat, monthly_limit=limit))

        # Transactions (last 60 days)
        # Incomes
        for m_offset in range(3):
            tx_d = today - timedelta(days=m_offset * 30 + 1)
            db.session.add(Transaction(
                user_id=sarah.id, title='Principal Tech Salary', amount=7500.0,
                type='income', category='Salary', transaction_date=tx_d
            ))
        # Expenses
        sarah_expenses = [
            ('Mortgage / Housing', 1750.0, 'Housing', 5),
            ('Organic Groceries', 165.0, 'Groceries', 8),
            ('Electric & Water Utility', 185.0, 'Utilities', 12),
            ('Auto Insurance & Gas', 140.0, 'Transportation', 15),
            ('Dinner at Bistro', 95.0, 'Food & Dining', 18),
            ('Target Household', 110.0, 'Groceries', 22),
            ('Toyota Auto Payment', 220.0, 'Debt Payment', 25),
            ('Streaming Subscriptions', 45.0, 'Entertainment', 28)
        ]
        for title, amt, cat, days_ago in sarah_expenses:
            db.session.add(Transaction(
                user_id=sarah.id, title=title, amount=amt,
                type='expense', category=cat, transaction_date=today - timedelta(days=days_ago)
            ))
        db.session.commit()

        # Evaluate Sarah's Risk
        sarah_eval = calculate_risk_assessment(sarah)
        r1 = RiskAssessment(
            user_id=sarah.id,
            health_score=sarah_eval['health_score'],
            risk_tier=sarah_eval['risk_tier'],
            dti_ratio=sarah_eval['features']['dti_ratio'],
            savings_rate=sarah_eval['features']['savings_rate'],
            emergency_runway_months=sarah_eval['features']['emergency_runway_months'],
            discretionary_ratio=sarah_eval['features']['discretionary_ratio'],
            expense_volatility=sarah_eval['features']['expense_volatility'],
            solvency_probability_12m=sarah_eval['solvency_probability_12m']
        )
        r1.set_drivers(sarah_eval['drivers'])
        db.session.add(r1)

        # ==========================================
        # 2. Alex Stressed (Critical Risk / High Debt)
        # ==========================================
        print("Creating User: alex_stressed...")
        alex = User(
            username='alex_stressed',
            email='alex@example.com',
            full_name='Alex Stressed',
            monthly_income=3200.0,
            liquid_savings=350.0,
            risk_tolerance='conservative',
            currency='$'
        )
        alex.set_password('password123')
        db.session.add(alex)
        db.session.commit()

        # Severe toxic high-interest debt burden (DTI > 55%)
        db.session.add(Debt(
            user_id=alex.id,
            debt_name='Chase Sapphire Reserve',
            debt_type='Credit Card',
            principal_balance=16500.0,
            interest_rate_apr=28.99,
            minimum_payment=560.0
        ))
        db.session.add(Debt(
            user_id=alex.id,
            debt_name='Capital One QuickSilver',
            debt_type='Credit Card',
            principal_balance=9400.0,
            interest_rate_apr=27.49,
            minimum_payment=340.0
        ))
        db.session.add(Debt(
            user_id=alex.id,
            debt_name='Consolidation Personal Loan',
            debt_type='Personal Loan',
            principal_balance=14200.0,
            interest_rate_apr=21.80,
            minimum_payment=510.0
        ))
        db.session.add(Debt(
            user_id=alex.id,
            debt_name='Subprime Auto Loan',
            debt_type='Auto Loan',
            principal_balance=11800.0,
            interest_rate_apr=14.50,
            minimum_payment=380.0
        ))

        # Budgets
        alex_budgets = [
            ('Housing', 1300.0),
            ('Food & Dining', 300.0),
            ('Groceries', 350.0),
            ('Shopping', 150.0),
            ('Entertainment', 100.0)
        ]
        for cat, limit in alex_budgets:
            db.session.add(Budget(user_id=alex.id, category=cat, monthly_limit=limit))

        # Incomes
        for m_offset in range(3):
            db.session.add(Transaction(
                user_id=alex.id, title='Monthly Net Salary', amount=3200.0,
                type='income', category='Salary', transaction_date=today - timedelta(days=m_offset * 30 + 1)
            ))

        # Expenses (including an anomaly!)
        alex_expenses = [
            ('Apartment Rent', 1350.0, 'Housing', 4, False, 0.0),
            ('Fast Food & Dining Out', 420.0, 'Food & Dining', 7, False, 0.0),
            ('Chase Minimum Payment', 560.0, 'Debt Payment', 10, False, 0.0),
            ('Capital One Minimum Payment', 340.0, 'Debt Payment', 12, False, 0.0),
            ('Personal Loan Payment', 510.0, 'Debt Payment', 14, False, 0.0),
            ('Auto Loan Payment', 380.0, 'Debt Payment', 16, False, 0.0),
            ('Best Buy Electronics Shopping', 890.0, 'Shopping', 19, True, 0.92),  # ML Anomaly!
            ('Emergency Car Towing', 310.0, 'Transportation', 21, False, 0.0),
            ('Supermarket Groceries', 280.0, 'Groceries', 25, False, 0.0)
        ]
        for title, amt, cat, days_ago, is_anom, anom_score in alex_expenses:
            db.session.add(Transaction(
                user_id=alex.id, title=title, amount=amt,
                type='expense', category=cat, transaction_date=today - timedelta(days=days_ago),
                is_anomaly=is_anom, anomaly_score=anom_score
            ))
        db.session.commit()

        alex_eval = calculate_risk_assessment(alex)
        r2 = RiskAssessment(
            user_id=alex.id,
            health_score=alex_eval['health_score'],
            risk_tier=alex_eval['risk_tier'],
            dti_ratio=alex_eval['features']['dti_ratio'],
            savings_rate=alex_eval['features']['savings_rate'],
            emergency_runway_months=alex_eval['features']['emergency_runway_months'],
            discretionary_ratio=alex_eval['features']['discretionary_ratio'],
            expense_volatility=alex_eval['features']['expense_volatility'],
            solvency_probability_12m=alex_eval['solvency_probability_12m']
        )
        r2.set_drivers(alex_eval['drivers'])
        db.session.add(r2)

        # ==========================================
        # 3. David Moderate (Moderate Risk / Typical)
        # ==========================================
        print("Creating User: david_moderate...")
        david = User(
            username='david_moderate',
            email='david@example.com',
            full_name='David Moderate',
            monthly_income=5400.0,
            liquid_savings=11500.0,
            risk_tolerance='moderate',
            currency='$'
        )
        david.set_password('password123')
        db.session.add(david)
        db.session.commit()

        # Debt: Student Loan
        db.session.add(Debt(
            user_id=david.id,
            debt_name='Federal Direct Student Loan',
            debt_type='Student Loan',
            principal_balance=13400.0,
            interest_rate_apr=5.50,
            minimum_payment=165.0
        ))
        db.session.add(Debt(
            user_id=david.id,
            debt_name='Store Credit Card',
            debt_type='Credit Card',
            principal_balance=1850.0,
            interest_rate_apr=19.99,
            minimum_payment=65.0
        ))

        # Budgets
        david_budgets = [
            ('Housing', 1600.0),
            ('Groceries', 550.0),
            ('Food & Dining', 400.0),
            ('Transportation', 300.0),
            ('Utilities', 220.0)
        ]
        for cat, limit in david_budgets:
            db.session.add(Budget(user_id=david.id, category=cat, monthly_limit=limit))

        # Incomes
        for m_offset in range(3):
            db.session.add(Transaction(
                user_id=david.id, title='Software Engineer Salary', amount=5400.0,
                type='income', category='Salary', transaction_date=today - timedelta(days=m_offset * 30 + 1)
            ))

        # Expenses
        david_expenses = [
            ('Apartment Rent', 1550.0, 'Housing', 3),
            ('Trader Joe\'s Grocery', 210.0, 'Groceries', 7),
            ('Gas & Subway Commute', 120.0, 'Transportation', 11),
            ('Electric & Internet', 195.0, 'Utilities', 15),
            ('Restaurant with Friends', 125.0, 'Food & Dining', 19),
            ('Student Loan Monthly Payment', 165.0, 'Debt Payment', 22),
            ('Credit Card Payment', 150.0, 'Debt Payment', 26)
        ]
        for title, amt, cat, days_ago in david_expenses:
            db.session.add(Transaction(
                user_id=david.id, title=title, amount=amt,
                type='expense', category=cat, transaction_date=today - timedelta(days=days_ago)
            ))
        db.session.commit()

        david_eval = calculate_risk_assessment(david)
        r3 = RiskAssessment(
            user_id=david.id,
            health_score=david_eval['health_score'],
            risk_tier=david_eval['risk_tier'],
            dti_ratio=david_eval['features']['dti_ratio'],
            savings_rate=david_eval['features']['savings_rate'],
            emergency_runway_months=david_eval['features']['emergency_runway_months'],
            discretionary_ratio=david_eval['features']['discretionary_ratio'],
            expense_volatility=david_eval['features']['expense_volatility'],
            solvency_probability_12m=david_eval['solvency_probability_12m']
        )
        r3.set_drivers(david_eval['drivers'])
        db.session.add(r3)
        db.session.commit()

        print("=" * 60)
        print("Database seeded successfully with 3 demonstration profiles:")
        print(f"1. Sarah Resilient (Score: {sarah_eval['health_score']}, Tier: {sarah_eval['risk_tier']})")
        print(f"2. Alex Stressed   (Score: {alex_eval['health_score']}, Tier: {alex_eval['risk_tier']})")
        print(f"3. David Moderate  (Score: {david_eval['health_score']}, Tier: {david_eval['risk_tier']})")
        print("Default password for all demo accounts: 'password123'")
        print("=" * 60)

if __name__ == '__main__':
    seed_database()
