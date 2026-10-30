import numpy as np
import pandas as pd

def generate_financial_risk_dataset(n_samples=6000, random_seed=42):
    """
    Synthesize a realistic financial risk benchmark dataset based on 
    consumer finance distributions (CFPB / Federal Reserve benchmarks).
    """
    np.random.seed(random_seed)
    
    # 1. Monthly Gross Income: Log-normal distribution
    monthly_income = np.random.lognormal(mean=8.4, sigma=0.55, size=n_samples)
    monthly_income = np.clip(monthly_income, 1800, 25000)
    
    # 2. Debt-to-Income (DTI) ratio (%)
    # Bi-modal: one cohort responsible (10-30%), one cohort stressed (35-75%)
    cohort = np.random.binomial(1, 0.35, size=n_samples)
    dti_healthy = np.random.normal(18, 8, size=n_samples)
    dti_stressed = np.random.normal(48, 14, size=n_samples)
    dti = np.where(cohort == 0, dti_healthy, dti_stressed)
    dti = np.clip(dti, 0.0, 95.0)
    
    # 3. Monthly Debt Payments
    monthly_debt = monthly_income * (dti / 100.0)
    
    # 4. Savings Rate (%)
    # Correlated inversely with DTI
    savings_rate = 32.0 - (0.55 * dti) + np.random.normal(0, 7.5, size=n_samples)
    savings_rate = np.clip(savings_rate, -40.0, 65.0)
    
    # 5. Total Monthly Expenses
    monthly_expenses = monthly_income * (1.0 - (savings_rate / 100.0))
    monthly_expenses = np.clip(monthly_expenses, 800, 30000)
    
    # 6. Essential Expenses (Rent, Food, Healthcare, Utilities, Minimum Debt)
    essential_ratio = np.random.uniform(0.45, 0.85, size=n_samples)
    essential_expenses = monthly_expenses * essential_ratio
    
    # 7. Discretionary Spending Ratio (%)
    discretionary_ratio = (1.0 - essential_ratio) * 100.0
    
    # 8. Emergency Fund Runway (Months of liquid cash)
    runway_latent = (savings_rate * 0.15) + np.random.exponential(scale=3.5, size=n_samples)
    emergency_runway_months = np.clip(runway_latent, 0.0, 24.0)
    liquid_savings = emergency_runway_months * essential_expenses
    
    # 9. Expense Volatility (Coefficient of Variation)
    expense_volatility = np.random.beta(a=2, b=8, size=n_samples) * 1.2
    expense_volatility = np.clip(expense_volatility, 0.04, 0.75)
    
    # 10. Number of Active Debt Accounts
    active_debts_count = np.random.poisson(lam=np.clip(dti / 15.0, 0.5, 6.0), size=n_samples)
    
    # 11. Budget Utilization Ratio (Actual Spending / Target Budget)
    budget_utilization = 0.70 + (0.007 * dti) - (0.005 * savings_rate) + np.random.normal(0, 0.12, size=n_samples)
    budget_utilization = np.clip(budget_utilization, 0.45, 2.20)
    
    # --- Composite Financial Health Score Formulation ---
    # Score 0 (extreme default risk) to 100 (exemplary financial resilience)
    health_score = (
        85.0
        - (0.42 * dti)                          # DTI penalty
        + (0.32 * savings_rate)                 # Savings rate bonus/penalty
        + (3.80 * np.minimum(emergency_runway_months, 6.0)) # Emergency buffer bonus
        - (0.18 * discretionary_ratio)           # Discretionary burn penalty
        - (18.0 * expense_volatility)           # Cashflow volatility penalty
        - (15.0 * np.maximum(0, budget_utilization - 1.0)) # Overspending penalty
        - (2.0 * np.maximum(0, active_debts_count - 2))    # Excessive debt count penalty
        + np.random.normal(0, 2.5, size=n_samples)        # Stochastic perturbation
    )
    health_score = np.clip(health_score, 5.0, 98.5)
    
    # Categorical Risk Tier
    risk_tier = []
    for score in health_score:
        if score >= 78.0:
            risk_tier.append('Low Risk')
        elif score >= 58.0:
            risk_tier.append('Moderate Risk')
        elif score >= 38.0:
            risk_tier.append('Elevated Risk')
        else:
            risk_tier.append('Critical Risk')
            
    df = pd.DataFrame({
        'monthly_income': np.round(monthly_income, 2),
        'monthly_expenses': np.round(monthly_expenses, 2),
        'dti_ratio': np.round(dti, 2),
        'savings_rate': np.round(savings_rate, 2),
        'emergency_runway_months': np.round(emergency_runway_months, 2),
        'liquid_savings': np.round(liquid_savings, 2),
        'discretionary_ratio': np.round(discretionary_ratio, 2),
        'expense_volatility': np.round(expense_volatility, 3),
        'active_debts_count': active_debts_count,
        'budget_utilization': np.round(budget_utilization, 3),
        'health_score': np.round(health_score, 2),
        'risk_tier': risk_tier
    })
    
    return df

if __name__ == '__main__':
    df = generate_financial_risk_dataset(100)
    print("Sample Generated Records:")
    print(df.head(5)[['dti_ratio', 'savings_rate', 'emergency_runway_months', 'health_score', 'risk_tier']])

