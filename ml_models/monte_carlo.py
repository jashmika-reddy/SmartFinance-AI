import numpy as np

class MonteCarloStressTester:
    """
    Simulates forward financial net cashflow and liquid wealth trajectories
    using stochastic Monte Carlo simulations (Geometric Brownian Motion with Jump/Drift Shocks).
    """

    @staticmethod
    def run_simulations(initial_wealth, monthly_income, monthly_expenses, horizon_months=12, n_simulations=1000):
        """
        Runs 1,000 stochastic simulation paths across 4 economic stress test scenarios.
        """
        np.random.seed(42)
        timeline = list(range(0, horizon_months + 1))
        
        # Scenarios definition
        scenarios = {
            'baseline': {
                'name': 'Baseline Trajectory',
                'description': 'Normal economic conditions: 3.5% inflation, standard cashflow variance.',
                'income_mult': np.ones(horizon_months),
                'expense_drift': 1.0 + np.linspace(0.0, 0.035, horizon_months),
                'lump_shock': np.zeros(horizon_months),
                'volatility': 0.08
            },
            'stagflation': {
                'name': 'Stagflation Shock',
                'description': 'Severe inflation (+12%) and real wage compression (-6%).',
                'income_mult': np.linspace(1.0, 0.94, horizon_months),
                'expense_drift': 1.0 + np.linspace(0.0, 0.14, horizon_months),
                'lump_shock': np.zeros(horizon_months),
                'volatility': 0.14
            },
            'job_loss': {
                'name': 'Sudden Job Loss (3-Month Severance)',
                'description': 'Income ceases completely in months 2, 3, and 4, then recovers to 85%.',
                'income_mult': np.array([1.0, 0.0, 0.0, 0.0, 0.85, 0.85, 0.90, 0.90, 1.0, 1.0, 1.0, 1.0]),
                'expense_drift': np.ones(horizon_months),
                'lump_shock': np.zeros(horizon_months),
                'volatility': 0.12
            },
            'medical_emergency': {
                'name': 'Unforeseen Health Emergency',
                'description': 'Sudden critical medical/liability outflow of 2.5x normal monthly burn in month 3.',
                'income_mult': np.ones(horizon_months),
                'expense_drift': 1.0 + np.linspace(0.0, 0.04, horizon_months),
                'lump_shock': np.array([0, 0, 2.5 * monthly_expenses] + [0] * (horizon_months - 3)),
                'volatility': 0.10
            }
        }
        
        results = {}
        
        for sc_key, sc_data in scenarios.items():
            # Matrix of shape (n_simulations, horizon_months + 1)
            paths = np.zeros((n_simulations, horizon_months + 1))
            paths[:, 0] = initial_wealth
            
            insolvent_count = 0
            
            for m in range(horizon_months):
                inc_factor = sc_data['income_mult'][m]
                exp_factor = sc_data['expense_drift'][m]
                shock = sc_data['lump_shock'][m]
                vol = sc_data['volatility']
                
                # Stochastic noise in monthly expenses and income
                inc_noise = np.random.normal(1.0, vol * 0.7, size=n_simulations)
                exp_noise = np.random.normal(1.0, vol, size=n_simulations)
                
                sim_income = (monthly_income * inc_factor) * inc_noise
                sim_expense = (monthly_expenses * exp_factor) * exp_noise + shock
                
                # Monthly net cashflow
                net_flow = sim_income - sim_expense
                
                # Wealth at month m+1
                paths[:, m + 1] = paths[:, m] + net_flow
                
            # Compute summary percentiles
            p10 = np.percentile(paths, 10, axis=0)
            p50 = np.percentile(paths, 50, axis=0)
            p90 = np.percentile(paths, 90, axis=0)
            
            # Count insolvency: any path that dips below 0 at any point
            min_per_path = np.min(paths, axis=1)
            insolvency_prob = round(float(np.mean(min_per_path <= 0.0) * 100.0), 1)
            
            results[sc_key] = {
                'name': sc_data['name'],
                'description': sc_data['description'],
                'months': timeline,
                'p10': [round(float(v), 2) for v in p10],
                'p50': [round(float(v), 2) for v in p50],
                'p90': [round(float(v), 2) for v in p90],
                'insolvency_probability': insolvency_prob,
                'final_median_wealth': round(float(p50[-1]), 2),
                'min_observed_wealth': round(float(np.min(p10)), 2)
            }
            
        return results

