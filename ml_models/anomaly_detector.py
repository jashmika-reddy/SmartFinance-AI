import os
import sys

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import numpy as np
from sklearn.ensemble import IsolationForest
from currency_utils import format_inr

class TransactionAnomalyDetector:
    """
    Identifies anomalous spending transactions using statistical thresholds
    and unsupervised Isolation Forest machine learning.
    """
    
    @staticmethod
    def evaluate_transaction(new_amount, category, past_transactions):
        """
        Evaluate if a new transaction amount is anomalous relative to 
        the user's category history and global spending habits.
        
        Returns: (is_anomaly: bool, anomaly_score: float, reason: str)
        """
        if new_amount <= 0:
            return False, 0.0, "Non-positive amount"
            
        # Filter past expenses in the same category
        cat_expenses = [
            tx.amount for tx in past_transactions 
            if tx.type == 'expense' and tx.category.lower() == category.lower() and tx.amount > 0
        ]
        
        all_expenses = [
            tx.amount for tx in past_transactions 
            if tx.type == 'expense' and tx.amount > 0
        ]
        
        # If very few data points, use heuristic benchmark
        if len(cat_expenses) < 3:
            if all_expenses and len(all_expenses) >= 5:
                mean_all = np.mean(all_expenses)
                std_all = np.std(all_expenses)
                if std_all > 0 and (new_amount - mean_all) / std_all > 3.0 and new_amount > 2500:
                    return True, 0.85, f"Amount {format_inr(new_amount)} is exceptionally large compared to typical expenses."
            return False, 0.1, "Insufficient history for category"
            
        # Statistical Metrics for the category
        mean_val = float(np.mean(cat_expenses))
        std_val = float(np.std(cat_expenses))
        q75, q25 = np.percentile(cat_expenses, [75, 25])
        iqr = q75 - q25
        
        # Z-score metric
        z_score = (new_amount - mean_val) / std_val if std_val > 0 else 0.0
        
        # IQR threshold metric
        iqr_threshold = q75 + (2.0 * iqr) if iqr > 0 else (mean_val * 2.5)
        
        # Multi-sample Isolation Forest check if enough samples exist
        if len(cat_expenses) >= 8:
            try:
                X_train = np.array(cat_expenses).reshape(-1, 1)
                iso = IsolationForest(contamination=0.08, random_state=42)
                iso.fit(X_train)
                pred = iso.predict([[new_amount]])[0]
                iso_score = float(-iso.score_samples([[new_amount]])[0]) # higher score = more anomalous
                
                if pred == -1 and new_amount > mean_val:
                    scaled_score = min(0.99, max(0.65, iso_score))
                    return True, round(scaled_score, 2), f"Spike detected: {format_inr(new_amount)} is {z_score:.1f}x deviations above normal {category} average ({format_inr(mean_val)})."
            except Exception:
                pass
                
        # Fallback to combined Z-Score & IQR condition
        if z_score >= 2.5 and new_amount >= iqr_threshold and new_amount > (mean_val * 1.8):
            anomaly_score = min(0.95, round(0.5 + (z_score * 0.1), 2))
            return True, anomaly_score, f"Significant deviation in {category}: {format_inr(new_amount)} vs avg {format_inr(mean_val)}."
            
        return False, 0.05, "Normal transaction within parameters"

