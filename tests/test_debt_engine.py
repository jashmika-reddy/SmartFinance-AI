from ml_models.debt_optimizer import DebtOptimizationEngine

def test_debt_avalanche_vs_snowball():
    debts = [
        {'id': 1, 'name': 'High APR Card', 'balance': 5000.0, 'apr': 24.99, 'min_payment': 150.0},
        {'id': 2, 'name': 'Low APR Card', 'balance': 2000.0, 'apr': 9.99, 'min_payment': 60.0},
        {'id': 3, 'name': 'Medium Loan', 'balance': 8000.0, 'apr': 15.50, 'min_payment': 200.0}
    ]
    
    comp = DebtOptimizationEngine.compare_strategies(debts, extra_monthly_payment=250.0)
    
    avalanche = comp['avalanche']
    snowball = comp['snowball']
    
    # Mathematical invariant: Avalanche MUST yield equal or lower total interest than Snowball
    assert avalanche['total_interest_paid'] <= snowball['total_interest_paid']
    assert comp['interest_saved_by_avalanche'] >= 0.0
    
    # Both strategies must eventually eliminate debt (reach 0)
    assert avalanche['monthly_trajectory'][-1] <= 0.01
    assert snowball['monthly_trajectory'][-1] <= 0.01

def test_zero_debt_case():
    comp = DebtOptimizationEngine.compare_strategies([], extra_monthly_payment=100.0)
    assert comp['avalanche']['months_to_payoff'] == 0
    assert comp['interest_saved_by_avalanche'] == 0.0

