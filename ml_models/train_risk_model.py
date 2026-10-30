import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, classification_report

from ml_models.synthetic_data import generate_financial_risk_dataset

MODEL_BUNDLE_PATH = os.path.join(os.path.dirname(__file__), 'risk_model_bundle.joblib')

FEATURE_COLUMNS = [
    'monthly_income',
    'monthly_expenses',
    'dti_ratio',
    'savings_rate',
    'emergency_runway_months',
    'discretionary_ratio',
    'expense_volatility',
    'active_debts_count',
    'budget_utilization'
]

def train_and_export_model(n_samples=8000, save_path=MODEL_BUNDLE_PATH):
    """
    Train Random Forest Regressor & Classifier on multi-factor personal financial profiles.
    Evaluates cross-validation performance and persists artifacts for real-time inference.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating synthetic financial dataset ({n_samples} samples)...")
    df = generate_financial_risk_dataset(n_samples=n_samples, random_seed=42)
    
    X = df[FEATURE_COLUMNS]
    y_reg = df['health_score']
    y_clf = df['risk_tier']
    
    # Split train/test
    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X, y_reg, y_clf, test_size=0.20, random_state=42, stratify=y_clf
    )
    
    # Feature Scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 1. Regressor (Score 0-100)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Training Random Forest Regressor...")
    regressor = RandomForestRegressor(
        n_estimators=120,
        max_depth=14,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    regressor.fit(X_train_scaled, y_reg_train)
    
    # Evaluate Regressor
    y_reg_pred = regressor.predict(X_test_scaled)
    mae = mean_absolute_error(y_reg_test, y_reg_pred)
    rmse = np.sqrt(mean_squared_error(y_reg_test, y_reg_pred))
    r2 = r2_score(y_reg_test, y_reg_pred)
    
    # 2. Classifier (Risk Tier)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Training Random Forest Classifier...")
    classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )
    classifier.fit(X_train_scaled, y_clf_train)
    
    # Evaluate Classifier
    y_clf_pred = classifier.predict(X_test_scaled)
    clf_report = classification_report(y_clf_test, y_clf_pred, output_dict=True)
    
    # Feature Importances
    importances = dict(zip(FEATURE_COLUMNS, regressor.feature_importances_))
    # Sort descending
    sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))
    
    bundle = {
        'regressor': regressor,
        'classifier': classifier,
        'scaler': scaler,
        'feature_columns': FEATURE_COLUMNS,
        'feature_importances': sorted_importances,
        'classes': list(classifier.classes_),
        'metrics': {
            'mae': round(float(mae), 3),
            'rmse': round(float(rmse), 3),
            'r2_score': round(float(r2), 4),
            'classifier_accuracy': round(float(clf_report['accuracy']), 4)
        },
        'trained_at': datetime.utcnow().isoformat()
    }
    
    # Persist bundle
    joblib.dump(bundle, save_path)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Model bundle saved successfully to {save_path}")
    print(f"Metrics: R2={r2:.4f}, RMSE={rmse:.3f}, MAE={mae:.3f}, Acc={clf_report['accuracy']:.4f}")
    print("Top Feature Importances:")
    for feat, imp in list(sorted_importances.items())[:5]:
        print(f"  - {feat}: {imp*100:.2f}%")
        
    return bundle

if __name__ == '__main__':
    train_and_export_model()
