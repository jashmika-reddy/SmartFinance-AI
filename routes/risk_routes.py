from flask import Blueprint, render_template, redirect, url_for, flash, g, request
from routes.auth_routes import login_required
from models import db, RiskAssessment
from ml_models.risk_scorer import calculate_risk_assessment, get_model_bundle
from ml_models.monte_carlo import MonteCarloStressTester

risk_bp = Blueprint('risk', __name__)

@risk_bp.route('/risk-assessment')
@login_required
def assessment():
    user = g.user
    assessment_data = calculate_risk_assessment(user)
    
    # Retrieve model metadata from joblib bundle if present
    bundle = get_model_bundle()
    model_metadata = None
    if bundle:
        model_metadata = {
            'metrics': bundle.get('metrics', {}),
            'feature_importances': bundle.get('feature_importances', {}),
            'trained_at': bundle.get('trained_at', 'N/A')
        }
        
    return render_template(
        'risk_assessment.html',
        assessment=assessment_data,
        model_metadata=model_metadata,
        user=user
    )

@risk_bp.route('/risk/re-evaluate', methods=['POST'])
@login_required
def re_evaluate():
    user = g.user
    assessment_data = calculate_risk_assessment(user)
    
    new_record = RiskAssessment(
        user_id=user.id,
        health_score=assessment_data['health_score'],
        risk_tier=assessment_data['risk_tier'],
        dti_ratio=assessment_data['features']['dti_ratio'],
        savings_rate=assessment_data['features']['savings_rate'],
        emergency_runway_months=assessment_data['features']['emergency_runway_months'],
        discretionary_ratio=assessment_data['features']['discretionary_ratio'],
        expense_volatility=assessment_data['features']['expense_volatility'],
        solvency_probability_12m=assessment_data['solvency_probability_12m']
    )
    new_record.set_drivers(assessment_data['drivers'])
    db.session.add(new_record)
    db.session.commit()
    
    flash(f'Financial Risk Profile recalculated! Score: {assessment_data["health_score"]}/100 ({assessment_data["risk_tier"]})', 'success')
    return redirect(url_for('risk.assessment'))

@risk_bp.route('/stress-test')
@login_required
def stress_test():
    user = g.user
    features = calculate_risk_assessment(user)['features']
    
    initial_wealth = user.liquid_savings or 5000.0
    monthly_income = features['monthly_income']
    monthly_expenses = features['monthly_expenses']
    
    simulations = MonteCarloStressTester.run_simulations(
        initial_wealth=initial_wealth,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        horizon_months=12,
        n_simulations=1000
    )
    
    return render_template(
        'stress_test.html',
        simulations=simulations,
        user=user,
        initial_wealth=round(initial_wealth, 2),
        monthly_income=round(monthly_income, 2),
        monthly_expenses=round(monthly_expenses, 2)
    )

