from models import User, Transaction
from ml_models.risk_scorer import calculate_risk_assessment
from ml_models.anomaly_detector import TransactionAnomalyDetector
from ml_models.monte_carlo import MonteCarloStressTester

def test_risk_scoring_bounds():
    # Test High-resilience profile
    healthy_user = User(
        username='test_healthy',
        email='healthy@test.com',
        monthly_income=8000.0,
        liquid_savings=35000.0
    )
    res_healthy = calculate_risk_assessment(healthy_user)
    assert 0.0 <= res_healthy['health_score'] <= 100.0
    assert res_healthy['risk_tier'] in ['Low Risk', 'Moderate Risk', 'Elevated Risk', 'Critical Risk']
    assert res_healthy['solvency_probability_12m'] >= 80.0

    # Test Stressed profile
    stressed_user = User(
        username='test_stressed',
        email='stressed@test.com',
        monthly_income=2500.0,
        liquid_savings=200.0
    )
    res_stressed = calculate_risk_assessment(stressed_user)
    assert res_stressed['health_score'] < res_healthy['health_score']

def test_anomaly_detector_statistical_spike():
    # Past normal grocery expenses around $50-$80
    past_txs = [
        Transaction(title='Groceries 1', amount=55.0, type='expense', category='Groceries'),
        Transaction(title='Groceries 2', amount=65.0, type='expense', category='Groceries'),
        Transaction(title='Groceries 3', amount=72.0, type='expense', category='Groceries'),
        Transaction(title='Groceries 4', amount=60.0, type='expense', category='Groceries'),
        Transaction(title='Groceries 5', amount=58.0, type='expense', category='Groceries'),
        Transaction(title='Groceries 6', amount=80.0, type='expense', category='Groceries'),
        Transaction(title='Groceries 7', amount=62.0, type='expense', category='Groceries'),
        Transaction(title='Groceries 8', amount=70.0, type='expense', category='Groceries')
    ]
    
    # Normal transaction: $68
    is_anom, score, reason = TransactionAnomalyDetector.evaluate_transaction(68.0, 'Groceries', past_txs)
    assert is_anom is False
    
    # Extreme Outlier Spike: $950 in groceries
    is_anom_spike, score_spike, reason_spike = TransactionAnomalyDetector.evaluate_transaction(950.0, 'Groceries', past_txs)
    assert is_anom_spike is True
    assert score_spike >= 0.50

def test_monte_carlo_stress_testing():
    sim = MonteCarloStressTester.run_simulations(
        initial_wealth=10000.0,
        monthly_income=5000.0,
        monthly_expenses=3800.0,
        horizon_months=12,
        n_simulations=500
    )
    
    assert 'baseline' in sim
    assert 'stagflation' in sim
    assert 'job_loss' in sim
    assert 'medical_emergency' in sim
    
    base = sim['baseline']
    assert len(base['months']) == 13
    assert len(base['p10']) == 13
    assert len(base['p50']) == 13
    assert len(base['p90']) == 13
    
    # Statistical ordering: P10 <= P50 <= P90
    for i in range(13):
        assert base['p10'][i] <= base['p50'][i] + 0.01
        assert base['p50'][i] <= base['p90'][i] + 0.01
        
    # Insolvency probability should be between 0% and 100%
    assert 0.0 <= base['insolvency_probability'] <= 100.0

