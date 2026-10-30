import os
import sys

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from currency_utils import format_inr, CURRENCY_SYMBOL

class FinancialAdvisorEngine:
    """
    Intelligent prescriptive AI advisory engine that evaluates diagnostic factors
    and formulates tailored, prioritized financial interventions.
    """

    @staticmethod
    def generate_recommendations(user, assessment, debts, budgets, transactions):
        """
        Synthesizes user diagnostics into actionable, prioritized financial advice.
        """
        recommendations = []
        features = assessment.get('features', {})
        health_score = assessment.get('health_score', 50.0)
        risk_tier = assessment.get('risk_tier', 'Moderate Risk')
        
        dti = features.get('dti_ratio', 0.0)
        runway = features.get('emergency_runway_months', 3.0)
        savings_rate = features.get('savings_rate', 10.0)
        disc_ratio = features.get('discretionary_ratio', 30.0)
        monthly_income = features.get('monthly_income', 4000.0)
        monthly_expenses = features.get('monthly_expenses', 3000.0)
        
        # 1. Critical Priority: Emergency Fund Deficit
        if runway < 2.0:
            deficit = max(0.0, (3.0 - runway) * (monthly_expenses * 0.65))
            recommendations.append({
                'id': 'rec_emergency_critical',
                'priority': 'High Priority',
                'category': 'Emergency Cushion',
                'title': 'Emergency Runway Is Critically Under-Funded',
                'summary': f'You currently possess only {runway:.1f} months of survival runway. Any sudden income disruption or medical emergency risks immediate insolvency.',
                'action_steps': [
                    f'Target an immediate baseline reserve of {format_inr(deficit, decimals=0)} (3 months of essential expenses).',
                    'Direct 100% of non-essential surplus into a liquid mutual fund or high-interest bank fixed deposit (FD).',
                    'Temporarily pause discretionary lifestyle spending until the 3-month buffer is achieved.'
                ],
                'potential_impact': '+14 pts to Financial Health Score',
                'badge_color': 'red'
            })
        elif runway < 4.0:
            recommendations.append({
                'id': 'rec_emergency_moderate',
                'priority': 'Medium Priority',
                'category': 'Emergency Cushion',
                'title': 'Fortify Emergency Buffer to 6 Months',
                'summary': f'With {runway:.1f} months of runway, you have a foundation, but economic shocks require a 6-month buffer.',
                'action_steps': [
                    'Automate an automatic transfer of 5% of monthly salary into a recurring deposit or liquid fund on salary day.',
                    'Keep emergency reserves strictly separated from your daily spending UPI/checking account.'
                ],
                'potential_impact': '+6 pts to Financial Health Score',
                'badge_color': 'amber'
            })

        # 2. Critical Priority: High APR Debt
        high_apr_debts = [d for d in debts if d.interest_rate_apr >= 15.0]
        if high_apr_debts:
            total_high_apr = sum(d.principal_balance for d in high_apr_debts)
            highest_apr_debt = max(high_apr_debts, key=lambda x: x.interest_rate_apr)
            annual_interest_leak = sum(d.principal_balance * (d.interest_rate_apr / 100.0) for d in high_apr_debts)
            
            recommendations.append({
                'id': 'rec_debt_avalanche',
                'priority': 'High Priority',
                'category': 'Debt Optimization',
                'title': f'Eliminate Toxic High-Interest Debt ({highest_apr_debt.debt_name} at {highest_apr_debt.interest_rate_apr}%)',
                'summary': f'You are carrying {format_inr(total_high_apr, decimals=0)} across high-interest balances, burning approximately {format_inr(annual_interest_leak, decimals=0)} annually in dead-weight interest fees.',
                'action_steps': [
                    f'Deploy the Debt Avalanche method: pay minimums on all debts, and attack {highest_apr_debt.debt_name} with every excess Rupee.',
                    'Look into balance transfer options or a low-cost debt consolidation personal loan to freeze compounding interest.',
                    'Avoid making only the minimum payment, which prolongs payoff by years.'
                ],
                'potential_impact': f'Saves ~{format_inr(annual_interest_leak, decimals=0)}/yr & +12 pts to Score',
                'badge_color': 'red'
            })
        elif dti > 36.0:
            recommendations.append({
                'id': 'rec_dti_high',
                'priority': 'High Priority',
                'category': 'Debt Optimization',
                'title': f'De-leverage to Reduce Debt-to-Income ({dti:.1f}%)',
                'summary': 'Your DTI ratio is in the elevated risk zone (>36%). Lenders and banks consider this higher default exposure.',
                'action_steps': [
                    'Freeze new credit card spending or consumer EMI financing applications.',
                    'Allocate extra income from Diwali bonuses or tax refunds towards principal reductions.'
                ],
                'potential_impact': '+9 pts to Financial Health Score',
                'badge_color': 'amber'
            })

        # 3. Discretionary Spending / Cashflow Leak
        if disc_ratio > 35.0:
            disc_dollars = (disc_ratio / 100.0) * monthly_expenses
            potential_trim = disc_dollars * 0.20
            recommendations.append({
                'id': 'rec_discretionary_trim',
                'priority': 'Medium Priority',
                'category': 'Spending Efficiency',
                'title': f'Optimize Discretionary Lifestyle Burn ({format_inr(disc_dollars, decimals=0)}/mo)',
                'summary': f'{disc_ratio:.1f}% of your expenditures fall into lifestyle and discretionary categories.',
                'action_steps': [
                    f'Trimming just 20% ({format_inr(potential_trim, decimals=0)}/mo) frees up {format_inr(potential_trim * 12, decimals=0)} per year.',
                    'Audit monthly recurring app subscriptions, food delivery orders, and impulse shopping.',
                    'Apply the 50/30/20 rule: 50% Needs, 30% Wants, 20% Savings & Debt Acceleration.'
                ],
                'potential_impact': f'Recovers +{format_inr(potential_trim * 12, decimals=0)}/yr into wealth',
                'badge_color': 'blue'
            })

        # 4. Budget Envelope Overspending
        overbudget_items = []
        for b in budgets:
            spent = sum(
                tx.amount for tx in transactions 
                if tx.type == 'expense' and tx.category.lower() == b.category.lower()
            )
            if spent > b.monthly_limit:
                overbudget_items.append((b.category, spent, b.monthly_limit))
                
        if overbudget_items:
            cat_names = ", ".join([item[0] for item in overbudget_items])
            recommendations.append({
                'id': 'rec_budget_overrun',
                'priority': 'Medium Priority',
                'category': 'Budget Discipline',
                'title': f'Enforce Budget Caps in Breached Categories ({cat_names})',
                'summary': f'You have exceeded your monthly envelopes in {len(overbudget_items)} categories.',
                'action_steps': [
                    f'Institute immediate mid-month spending freeze for {cat_names}.',
                    'Set up UPI/SMS alerts when 80% of category allowance is consumed.',
                    'Re-balance surplus from under-spent categories if mandatory expenses arose.'
                ],
                'potential_impact': 'Prevents cashflow deficit & +5 pts to Score',
                'badge_color': 'amber'
            })

        # 5. Low Risk / Wealth Acceleration (if score is healthy)
        if health_score >= 75.0 and not high_apr_debts and runway >= 5.0:
            recommendations.append({
                'id': 'rec_invest_growth',
                'priority': 'Opportunity',
                'category': 'Wealth Acceleration',
                'title': 'Strong Foundation: Shift Focus to Long-Term Compounding',
                'summary': 'Your emergency reserves and debt ratios are stellar. Capitalize on your strong liquidity to accelerate long-term wealth.',
                'action_steps': [
                    'Maximize tax-advantaged instruments (EPF, PPF, NPS, ELSS tax-saving funds).',
                    'Invest surplus in low-cost, broad-market index funds (e.g., Nifty 50 / Nifty Next 50).',
                    'Consider Systematic Investment Planning (SIP) into diversified equity funds on salary day.'
                ],
                'potential_impact': 'Long-term compound wealth multiplier',
                'badge_color': 'emerald'
            })

        # Fallback if no specific condition met
        if not recommendations:
            recommendations.append({
                'id': 'rec_maintain_healthy',
                'priority': 'General Practice',
                'category': 'Financial Health',
                'title': 'Maintain Current Financial Trajectory',
                'summary': 'Your current spending, debt levels, and emergency liquidity remain within safe target ranges.',
                'action_steps': [
                    'Conduct a monthly ledger audit to ensure recurring bills have not unexpectedly increased.',
                    'Keep your emergency fund parked in an interest-bearing high-yield vehicle.'
                ],
                'potential_impact': 'Sustained top-tier financial resilience',
                'badge_color': 'blue'
            })

        return recommendations


    @staticmethod
    def answer_query(query_text, user_context):
        """
        Conversational assistant logic for user financial queries.
        Provides analytical answers with actionable guidance tailored to user's profile.
        """
        q = query_text.lower().strip()
        score = user_context.get('health_score', 65.0)
        dti = user_context.get('dti', 25.0)
        runway = user_context.get('runway', 3.5)
        
        if 'debt' in q and ('invest' in q or 'pay off' in q):
            return {
                'answer': (
                    "**Avalanche Rule of Thumb:** If your debt interest rate (APR) is higher than 10-12% (e.g. credit cards at 36-42% or personal loans at 15-20%), "
                    "paying off the debt is an **unbeatable guaranteed return on investment**. "
                    "No equity mutual fund or fixed deposit can consistently beat a guaranteed 36% APR credit card charge. "
                    "However, if you have low-interest subsidized debt (such as an 8% education loan with 80E tax deduction), investing in Nifty broad-market index funds via SIP historically yields 12-14% over the long horizon."
                ),
                'key_points': [
                    "Guaranteed Return: Clearing a 36% credit card balance = risk-free 36% ROI.",
                    "Always capture employer EPF / gratuity benefits first.",
                    f"Your current DTI is {dti:.1f}%. Target keeping total debt obligations under 30% of income."
                ]
            }
        elif 'emergency' in q or 'runway' in q or 'how much save' in q:
            return {
                'answer': (
                    f"Your current emergency runway is **{runway:.1f} months**. "
                    "The standard financial resilience guideline recommends **3 to 6 months of essential expenditures** (rent/home loan EMI, groceries, utilities, minimum debt service). "
                    "If you work in a volatile sector, run a business, or are the sole earner, aim for 6 to 9 months."
                ),
                'key_points': [
                    "Keep emergency reserves in High-Interest Savings Accounts, Sweep FDs, or Liquid Mutual Funds, never in volatile equities.",
                    "Do not keep excessive cash idle in zero-interest accounts, as inflation diminishes purchasing power over time."
                ]
            }
        elif 'credit' in q or 'score' in q or 'improve' in q:
            return {
                'answer': (
                    f"Your SmartFinance Financial Health Score is **{score:.1f}/100**. "
                    "To systematically improve your score and CIBIL rating:\n"
                    "1. Lower your Credit Card Utilization below 30% across all bank cards.\n"
                    "2. Build your emergency reserve up to at least 4-6 months of living expenses.\n"
                    "3. Automate recurring EMI auto-debits to guarantee 100% on-time payment track record.\n"
                    "4. Avoid making multiple hard credit card or loan inquiries in short succession."
                ),
                'key_points': [
                    "Payment track record and credit utilization form ~65% of traditional credit scores.",
                    "Our ML model heavily weights DTI and Cashflow Volatility for overall solvency risk."
                ]
            }
        elif '50/30/20' in q or 'budget' in q:
            return {
                'answer': (
                    "The **50/30/20 budgeting framework** divides your monthly in-hand income into three distinct buckets:\n"
                    "- **50% Needs:** House Rent / Home Loan EMI, Groceries, Utilities, School/Healthcare fees, Minimum Debt payments.\n"
                    "- **30% Wants:** Dining out, Weekend trips, Subscriptions, Shopping, Hobbies.\n"
                    "- **20% Savings & Debt Acceleration:** Emergency fund, SIP in Mutual Funds, PPF, NPS, additional debt prepayment."
                ),
                'key_points': [
                    "Use our Budgets module to set specific category limits corresponding to these buckets.",
                    "If your Needs exceed 50%, look into refinancing loans or optimizing lifestyle expenses."
                ]
            }
        else:
            return {
                'answer': (
                    f"Based on your current profile (Financial Health Score: {score:.1f}, Runway: {runway:.1f} mo, DTI: {dti:.1f}%), "
                    "the single most impactful lever you can pull right now is ensuring essential expenses are fully capped, "
                    "maintaining automated monthly contributions to your emergency reserve, and targeting high-interest liabilities."
                ),
                'key_points': [
                    "Check the 'Action Plan' tab for tailored, prioritized recommendations.",
                    "Run Monte Carlo Stress Tests to see how your reserves withstand economic shocks."
                ]
            }

