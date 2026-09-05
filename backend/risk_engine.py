"""
backend/risk_engine.py — Core inference + decision engine for SentinelPay.

Loads the trained model once, provides scoring, decision, explanation,
and manages the in-memory audit log.
"""

import logging
import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from config import (
    RANDOM_SEED,
    TEST_SIZE,
    FEATURE_COLUMNS,
    MODEL_PATH,
    DATA_PATH,
    LOW_THRESHOLD,
    HIGH_THRESHOLD,
    FALSE_POSITIVE_COST,
    FALSE_NEGATIVE_COST,
)
from explainability import generate_reasons


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class RiskEngine:
    """Singleton-style risk engine. Loads model once, scores transactions."""

    def __init__(self):
        self.model = None
        self.audit_log = []
        self._metrics_cache = None
        self._cost_analysis_cache = None

    def load(self):
        """Load the persisted model and compute test-set metrics."""
        logger.info("Loading risk model...")
        self.model = joblib.load(MODEL_PATH)
        logger.info("Model loaded successfully.")

        # Compute metrics on held-out test set
        self._compute_metrics()

    def _compute_metrics(self):
        """Compute real metrics on the held-out test set. Called once at startup."""
        df = pd.read_csv(DATA_PATH)
        X = df[FEATURE_COLUMNS]
        y = df["is_fraud"]

        # Reproduce the same split used in training
        _, X_test, _, y_test = train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
        )

        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]

        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
        roc_auc = roc_auc_score(y_test, y_proba)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        total_transactions = len(y_test)
        fraud_rate = float(y_test.mean())

        self._metrics_cache = {
            "total_transactions": total_transactions,
            "fraud_rate": round(fraud_rate, 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(roc_auc), 4),
            "false_positive_rate": round(float(fpr), 4),
            "confusion_matrix": {
                "true_negatives": int(tn),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "true_positives": int(tp),
            },
        }

        # Compute cost analysis using the same test data
        self._compute_cost_analysis(y_test, y_pred, y_proba)

    def _compute_cost_analysis(self, y_test, y_pred_default, y_proba):
        """Compute cost analysis with threshold sweep."""
        y_test_arr = np.array(y_test)

        # Current default threshold cost
        cm_default = confusion_matrix(y_test_arr, y_pred_default)
        tn_d, fp_d, fn_d, tp_d = cm_default.ravel()
        default_cost = fp_d * FALSE_POSITIVE_COST + fn_d * FALSE_NEGATIVE_COST

        # Threshold sweep
        thresholds = list(range(5, 100, 5))
        sweep = []
        for t in thresholds:
            threshold = t / 100.0
            y_pred_t = (y_proba >= threshold).astype(int)
            cm_t = confusion_matrix(y_test_arr, y_pred_t)
            tn_t, fp_t, fn_t, tp_t = cm_t.ravel()
            prec_t = tp_t / (tp_t + fp_t) if (tp_t + fp_t) > 0 else 0.0
            rec_t = tp_t / (tp_t + fn_t) if (tp_t + fn_t) > 0 else 0.0
            cost_t = fp_t * FALSE_POSITIVE_COST + fn_t * FALSE_NEGATIVE_COST

            sweep.append({
                "threshold": t,
                "precision": round(prec_t, 4),
                "recall": round(rec_t, 4),
                "false_positives": int(fp_t),
                "false_negatives": int(fn_t),
                "total_cost": int(cost_t),
            })

        self._cost_analysis_cache = {
            "false_positive_cost": FALSE_POSITIVE_COST,
            "false_negative_cost": FALSE_NEGATIVE_COST,
            "current_threshold_cost": int(default_cost),
            "current_false_positives": int(fp_d),
            "current_false_negatives": int(fn_d),
            "threshold_sweep": sweep,
            "note": "Cost figures are illustrative assumptions for demonstration purposes only.",
        }

    def analyze(self, features: dict) -> dict:
        """Score a transaction and return risk assessment."""
        # Build feature array in correct order
        feature_values = [features[col] for col in FEATURE_COLUMNS]
        X = np.array([feature_values])

        # Get fraud probability
        proba = self.model.predict_proba(X)[0][1]
        risk_score = int(round(proba * 100))
        risk_score = max(0, min(100, risk_score))

        # Determine risk level and decision
        if risk_score <= LOW_THRESHOLD:
            risk_level = "LOW"
            decision = "APPROVE"
        elif risk_score <= HIGH_THRESHOLD:
            risk_level = "MEDIUM"
            decision = "REVIEW"
        else:
            risk_level = "HIGH"
            decision = "DECLINE"

        # Generate explanations
        reasons = generate_reasons(features)

        # Build result
        transaction_id = str(uuid.uuid4())[:8].upper()
        timestamp = datetime.now(timezone.utc).isoformat()

        result = {
            "transaction_id": transaction_id,
            "timestamp": timestamp,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "decision": decision,
            "reasons": reasons,
            "fraud_probability": round(float(proba), 4),
            "input_features": features,
        }

        # Append to audit log
        self.audit_log.append({
            "transaction_id": transaction_id,
            "timestamp": timestamp,
            "amount": features.get("transaction_amount", 0),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "decision": decision,
            "reasons": reasons[:3],  # top 3 for brevity
        })

        return result

    def get_metrics(self) -> dict:
        """Return cached test-set metrics."""
        return self._metrics_cache

    def get_cost_analysis(self) -> dict:
        """Return cached cost analysis."""
        return self._cost_analysis_cache

    def get_audit_log(self) -> list:
        """Return the in-memory audit log."""
        return list(reversed(self.audit_log))  # most recent first


# Module-level singleton
engine = RiskEngine()
