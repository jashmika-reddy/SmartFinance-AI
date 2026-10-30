import copy

class DebtOptimizationEngine:
    """
    Simulates and compares debt payoff strategies:
    - Debt Avalanche (Mathematically optimal: Highest APR first)
    - Debt Snowball (Psychological momentum: Lowest Principal Balance first)
    """

    @staticmethod
    def simulate_payoff(debts_data, extra_monthly_payment=150.0, strategy='avalanche', max_months=360):
        """
        debts_data: list of dicts:
          [{'id': 1, 'name': 'Card A', 'balance': 5000, 'apr': 22.0, 'min_payment': 150}]
        """
        if not debts_data:
            return {
                'strategy': strategy,
                'months_to_payoff': 0,
                'total_interest_paid': 0.0,
                'total_paid': 0.0,
                'monthly_trajectory': [0.0],
                'is_infinite': False
            }

        # Deep copy debt state
        debts = []
        for d in debts_data:
            debts.append({
                'id': d.get('id'),
                'name': d.get('name', 'Debt'),
                'balance': float(d.get('balance', 0.0)),
                'apr': float(d.get('apr', 0.0)),
                'min_payment': float(d.get('min_payment', 25.0)),
                'monthly_rate': (float(d.get('apr', 0.0)) / 100.0) / 12.0
            })

        total_initial_balance = sum(d['balance'] for d in debts)
        if total_initial_balance <= 0:
            return {
                'strategy': strategy,
                'months_to_payoff': 0,
                'total_interest_paid': 0.0,
                'total_paid': 0.0,
                'monthly_trajectory': [0.0],
                'is_infinite': False
            }

        monthly_trajectory = [round(total_initial_balance, 2)]
        total_interest_paid = 0.0
        total_amount_paid = 0.0
        month = 0

        while month < max_months:
            active_debts = [d for d in debts if d['balance'] > 0.01]
            if not active_debts:
                break
                
            month += 1
            available_extra = float(extra_monthly_payment)

            # Sort active debts according to selected strategy
            if strategy == 'avalanche':
                # Highest APR first
                active_debts.sort(key=lambda x: x['apr'], reverse=True)
            else:
                # Lowest balance first (Snowball)
                active_debts.sort(key=lambda x: x['balance'], reverse=False)

            # Step 1: Accrue monthly interest & pay minimum payments
            freed_minimums = 0.0
            for d in active_debts:
                # Interest accrued this month
                monthly_interest = d['balance'] * d['monthly_rate']
                total_interest_paid += monthly_interest
                d['balance'] += monthly_interest
                
                # Check minimum payment
                scheduled_min = min(d['balance'], d['min_payment'])
                d['balance'] -= scheduled_min
                total_amount_paid += scheduled_min
                
                if d['balance'] <= 0.01:
                    d['balance'] = 0.0
                    # When a debt is eliminated, its minimum payment rolls over into the snowball/avalanche budget
                    freed_minimums += d['min_payment'] - scheduled_min

            # Step 2: Apply extra budget + any rolled-over minimums to target debt
            target_pool = available_extra + freed_minimums
            for d in active_debts:
                if target_pool <= 0:
                    break
                if d['balance'] > 0.01:
                    payment = min(d['balance'], target_pool)
                    d['balance'] -= payment
                    total_amount_paid += payment
                    target_pool -= payment

            current_remaining = sum(d['balance'] for d in debts)
            monthly_trajectory.append(round(current_remaining, 2))
            
            if current_remaining <= 0.01:
                break

        is_infinite = (month >= max_months and sum(d['balance'] for d in debts) > 1.0)

        return {
            'strategy': strategy,
            'months_to_payoff': month,
            'years_to_payoff': round(month / 12.0, 1),
            'total_interest_paid': round(total_interest_paid, 2),
            'total_paid': round(total_amount_paid, 2),
            'monthly_trajectory': monthly_trajectory,
            'is_infinite': is_infinite
        }

    @classmethod
    def compare_strategies(cls, debts_data, extra_monthly_payment=150.0):
        """
        Runs both Avalanche and Snowball algorithms and returns side-by-side comparison.
        """
        avalanche_res = cls.simulate_payoff(debts_data, extra_monthly_payment, strategy='avalanche')
        snowball_res = cls.simulate_payoff(debts_data, extra_monthly_payment, strategy='snowball')
        
        interest_saved_by_avalanche = round(
            max(0.0, snowball_res['total_interest_paid'] - avalanche_res['total_interest_paid']), 2
        )
        time_saved_months = max(0, snowball_res['months_to_payoff'] - avalanche_res['months_to_payoff'])
        
        # Harmonize trajectory lengths for Chart.js plotting
        max_len = max(len(avalanche_res['monthly_trajectory']), len(snowball_res['monthly_trajectory']))
        av_traj = avalanche_res['monthly_trajectory'] + [0.0] * (max_len - len(avalanche_res['monthly_trajectory']))
        sn_traj = snowball_res['monthly_trajectory'] + [0.0] * (max_len - len(snowball_res['monthly_trajectory']))
        
        timeline_labels = [f"Mo {m}" for m in range(max_len)]
        
        return {
            'avalanche': avalanche_res,
            'snowball': snowball_res,
            'interest_saved_by_avalanche': interest_saved_by_avalanche,
            'time_saved_months': time_saved_months,
            'timeline_labels': timeline_labels,
            'avalanche_curve': av_traj,
            'snowball_curve': sn_traj
        }

