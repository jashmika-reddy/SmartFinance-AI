import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

MODEL_BUNDLE_PATH = os.path.join(os.path.dirname(__file__), 'risk_model_bundle.joblib')

_cached_bundle = None

def get_model_bundle():
    global _cached_bundle
    if _cached_bundle is None:
        if os.path.exists(MODEL_BUNDLE_PATH):
            try:
                _cached_bundle = joblib.load(MODEL_BUNDLE_PATH)
            except Exception as e:
                print(f"Warning: Failed to load model bundle: {e}")
                _cached_bundle = None
    return _cached_bundle


def extract_user_financial_features(user):
    """
    Extract and compute multi-factor financial risk indicators from user records.
    """
    # 1. Monthly Income (base from profile or last 30d income)
    monthly_income = float(user.monthly_income) if user.monthly_income and user.monthly_income > 0 else 50000.0
    
    # 2. Extract recent transactions
    # Look back 90 days or all available
    cutoff_date = (datetime.utcnow() - timedelta(days=90)).date()
    tx_list = [tx for tx in user.transactions if tx.transaction_date >= cutoff_date]
    if not tx_list:
        tx_list = list(user.transactions)
        
    income_txs = [tx.amount for tx in tx_list if tx.type == 'income']
    expense_txs = [tx.amount for tx in tx_list if tx.type == 'expense']
    
    # If transaction history has income, compute monthly average
    if income_txs:
        # compute monthly normalized
        monthly_income_est = sum(income_txs) / max(1.0, len(income_txs) / 2.0)
        if monthly_income_est > 5000:
            monthly_income = (monthly_income + monthly_income_est) / 2.0
            
    # Monthly Expenses
    if expense_txs:
        # Estimate monthly expenses from transaction sum or average
        total_expense_sum = sum(expense_txs)
        # Average over at least 1 month
        monthly_expenses = total_expense_sum if total_expense_sum > 0 else (monthly_income * 0.70)
    else:
        monthly_expenses = monthly_income * 0.72  # standard default baseline
        
    monthly_expenses = max(1000.0, monthly_expenses)
    
    # 3. Debt-to-Income (DTI)
    debts = list(user.debts)
    total_min_debt_payment = sum(float(d.minimum_payment) for d in debts)
    dti_ratio = (total_min_debt_payment / monthly_income) * 100.0 if monthly_income > 0 else 0.0
    dti_ratio = min(99.0, max(0.0, dti_ratio))
    
    # 4. Savings Rate
    savings_rate = ((monthly_income - monthly_expenses) / monthly_income) * 100.0 if monthly_income > 0 else 0.0
    savings_rate = max(-100.0, min(80.0, savings_rate))
    
    # 5. Essential Expenses & Discretionary Ratio
    essential_categories = {'Housing', 'Rent', 'Utilities', 'Healthcare', 'Groceries', 'Debt Payment', 'Transportation'}
    essential_expense_sum = sum(
        tx.amount for tx in tx_list 
        if tx.type == 'expense' and any(c.lower() in tx.category.lower() for c in essential_categories)
    )
    if not essential_expense_sum and expense_txs:
        essential_expense_sum = monthly_expenses * 0.65
        
    essential_monthly_burn = max(essential_expense_sum, monthly_expenses * 0.50, 8000.0)
    
    discretionary_sum = max(0.0, monthly_expenses - essential_monthly_burn)
    discretionary_ratio = (discretionary_sum / monthly_expenses) * 100.0 if monthly_expenses > 0 else 30.0
    discretionary_ratio = min(90.0, max(5.0, discretionary_ratio))
    
    # 6. Emergency Runway
    liquid_savings = float(user.liquid_savings) if user.liquid_savings is not None else 150000.0
    emergency_runway_months = liquid_savings / essential_monthly_burn if essential_monthly_burn > 0 else 3.0
    emergency_runway_months = min(36.0, max(0.0, emergency_runway_months))
    
    # 7. Expense Volatility
    if len(expense_txs) >= 4:
        exp_std = float(np.std(expense_txs))
        exp_mean = float(np.mean(expense_txs))
        expense_volatility = (exp_std / exp_mean) if exp_mean > 0 else 0.20
    else:
        expense_volatility = 0.18
    expense_volatility = min(1.0, max(0.02, expense_volatility))
    
    # 8. Active Debts Count
    active_debts_count = len(debts)
    
    # 9. Budget Utilization
    budgets = list(user.budgets)
    total_budget_limit = sum(b.monthly_limit for b in budgets)
    if total_budget_limit > 0:
        budget_utilization = monthly_expenses / total_budget_limit
    else:
        budget_utilization = 0.90
    budget_utilization = min(2.5, max(0.3, budget_utilization))
    
    features = {
        'monthly_income': round(monthly_income, 2),
        'monthly_expenses': round(monthly_expenses, 2),
        'dti_ratio': round(dti_ratio, 2),
        'savings_rate': round(savings_rate, 2),
        'emergency_runway_months': round(emergency_runway_months, 2),
        'liquid_savings': round(liquid_savings, 2),
        'discretionary_ratio': round(discretionary_ratio, 2),
        'expense_volatility': round(expense_volatility, 3),
        'active_debts_count': active_debts_count,
        'budget_utilization': round(budget_utilization, 3)
    }
    
    return features


def calculate_risk_assessment(user):
    """
    Evaluates personal financial risk using the trained Random Forest model bundle,
    falling back to mathematical analytical index if bundle is uncompiled.
    """
    features = extract_user_financial_features(user)
    bundle = get_model_bundle()
    
    health_score = None
    risk_tier = None
    
    if bundle is not None:
        try:
            feat_cols = bundle['feature_columns']
            X_df = pd.DataFrame([{col: features.get(col, 0.0) for col in feat_cols}])
            X_scaled = bundle['scaler'].transform(X_df)
            
            # Predict Regressor Score
            raw_score = float(bundle['regressor'].predict(X_scaled)[0])
            health_score = round(max(5.0, min(99.0, raw_score)), 1)
            
            # Predict Classifier Tier
            predicted_tier = bundle['classifier'].predict(X_scaled)[0]
            risk_tier = str(predicted_tier)
        except Exception as e:
            print(f"Inference error with model bundle: {e}. Using deterministic fallback.")
            health_score = None
            
    # Deterministic Academic Fallback
    if health_score is None:
        dti = features['dti_ratio']
        sr = features['savings_rate']
        runway = features['emergency_runway_months']
        disc = features['discretionary_ratio']
        vol = features['expense_volatility']
        b_util = features['budget_utilization']
        debts = features['active_debts_count']
        
        calculated_score = (
            85.0
            - (0.42 * dti)
            + (0.32 * sr)
            + (3.80 * min(runway, 6.0))
            - (0.18 * disc)
            - (18.0 * vol)
            - (15.0 * max(0.0, b_util - 1.0))
            - (2.0 * max(0, debts - 2))
        )
        health_score = round(max(5.0, min(98.5, calculated_score)), 1)
        
        if health_score >= 78.0:
            risk_tier = 'Low Risk'
        elif health_score >= 58.0:
            risk_tier = 'Moderate Risk'
        elif health_score >= 38.0:
            risk_tier = 'Elevated Risk'
        else:
            risk_tier = 'Critical Risk'

    # Compute Factor Drivers / Explainability Breakdown
    drivers = []
    
    # 1. DTI Driver
    dti_val = features['dti_ratio']
    if dti_val > 45.0:
        drivers.append({
            'factor': 'Debt-to-Income Ratio (DTI)',
            'impact': 'negative',
            'severity': 'high',
            'detail': f'DTI of {dti_val:.1f}% is critically high (>45%). Debt debt-service drains cashflow.'
        })
    elif dti_val > 35.0:
        drivers.append({
            'factor': 'Debt-to-Income Ratio (DTI)',
            'impact': 'negative',
            'severity': 'medium',
            'detail': f'DTI of {dti_val:.1f}% exceeds optimal safety thresholds (max recommended: 35%).'
        })
    else:
        drivers.append({
            'factor': 'Debt-to-Income Ratio (DTI)',
            'impact': 'positive',
            'severity': 'low',
            'detail': f'Healthy DTI of {dti_val:.1f}% leaves ample headroom for living and savings.'
        })

    # 2. Emergency Runway Driver
    runway_val = features['emergency_runway_months']
    if runway_val < 2.0:
        drivers.append({
            'factor': 'Emergency Reserve Runway',
            'impact': 'negative',
            'severity': 'high',
            'detail': f'Runway of only {runway_val:.1f} months provides virtually zero cushion for unforeseen shocks.'
        })
    elif runway_val < 4.0:
        drivers.append({
            'factor': 'Emergency Reserve Runway',
            'impact': 'warning',
            'severity': 'medium',
            'detail': f'Runway is {runway_val:.1f} months. The standard benchmark is 6 full months of essential costs.'
        })
    else:
        drivers.append({
            'factor': 'Emergency Reserve Runway',
            'impact': 'positive',
            'severity': 'low',
            'detail': f'Solid emergency runway of {runway_val:.1f} months provides great resilience.'
        })

    # 3. Savings Rate Driver
    sr_val = features['savings_rate']
    if sr_val < 0.0:
        drivers.append({
            'factor': 'Net Savings Rate',
            'impact': 'negative',
            'severity': 'high',
            'detail': f'Negative savings rate ({sr_val:.1f}%). Monthly expenses exceed net income.'
        })
    elif sr_val < 15.0:
        drivers.append({
            'factor': 'Net Savings Rate',
            'impact': 'warning',
            'severity': 'medium',
            'detail': f'Savings rate of {sr_val:.1f}% is below the 20% standard wealth accumulation rule.'
        })
    else:
        drivers.append({
            'factor': 'Net Savings Rate',
            'impact': 'positive',
            'severity': 'low',
            'detail': f'Strong net savings rate of {sr_val:.1f}% accelerating net worth growth.'
        })

    # 4. Budget Utilization Driver
    b_util = features['budget_utilization']
    if b_util > 1.15:
        drivers.append({
            'factor': 'Budget Envelope Adherence',
            'impact': 'negative',
            'severity': 'high',
            'detail': f'Currently overspending allocated budget by {(b_util - 1.0)*100:.1f}%.'
        })
    elif b_util <= 0.90:
        drivers.append({
            'factor': 'Budget Envelope Adherence',
            'impact': 'positive',
            'severity': 'low',
            'detail': f'Spending is well within budget limits ({b_util*100:.1f}% utilized).'
        })

    # Solvency Probability estimate over 12 months (logistic decay function based on runway & DTI)
    solvency_prob = 100.0 / (1.0 + np.exp(-0.08 * (health_score - 45.0)))
    solvency_prob = round(float(np.clip(solvency_prob, 10.0, 99.8)), 1)
    
    return {
        'health_score': health_score,
        'risk_tier': risk_tier,
        'features': features,
        'drivers': drivers,
        'solvency_probability_12m': solvency_prob
    }

