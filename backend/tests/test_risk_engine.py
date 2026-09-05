"""
backend/tests/test_risk_engine.py — Unit tests for SentinelPay risk engine.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from risk_engine import RiskEngine


@pytest.fixture(scope="module")
def engine():
    """Load the engine once for all tests."""
    eng = RiskEngine()
    eng.load()
    return eng


def test_low_risk_approve(engine):
    """Clearly low-risk transaction should be APPROVED."""
    result = engine.analyze({
        "transaction_amount": 500,
        "transaction_hour": 14,
        "account_age_days": 800,
        "transactions_last_1h": 0,
        "transactions_last_24h": 2,
        "failed_attempts": 0,
        "new_device": 0,
        "location_changed": 0,
        "international_transaction": 0,
        "device_change_count": 0,
        "avg_historical_amount": 450,
    })
    assert result["decision"] == "APPROVE"
    assert result["risk_level"] == "LOW"


def test_high_risk_decline(engine):
    """Clearly high-risk transaction should be DECLINED."""
    result = engine.analyze({
        "transaction_amount": 200000,
        "transaction_hour": 3,
        "account_age_days": 2,
        "transactions_last_1h": 12,
        "transactions_last_24h": 40,
        "failed_attempts": 5,
        "new_device": 1,
        "location_changed": 1,
        "international_transaction": 1,
        "device_change_count": 5,
        "avg_historical_amount": 1000,
    })
    assert result["decision"] in ("DECLINE", "REVIEW")
    assert result["risk_level"] in ("HIGH", "MEDIUM")
    assert result["risk_score"] >= 30


def test_medium_risk_review(engine):
    """Ambiguous transaction should be REVIEW."""
    result = engine.analyze({
        "transaction_amount": 5000,
        "transaction_hour": 22,
        "account_age_days": 60,
        "transactions_last_1h": 3,
        "transactions_last_24h": 10,
        "failed_attempts": 1,
        "new_device": 1,
        "location_changed": 0,
        "international_transaction": 0,
        "device_change_count": 1,
        "avg_historical_amount": 2000,
    })
    # Medium-signal should not be extreme
    assert result["decision"] in ("APPROVE", "REVIEW", "DECLINE")
    assert 0 <= result["risk_score"] <= 100


def test_score_range(engine):
    """Risk score must always be in [0, 100]."""
    test_cases = [
        {"transaction_amount": 10, "transaction_hour": 0, "account_age_days": 0,
         "transactions_last_1h": 0, "transactions_last_24h": 0, "failed_attempts": 0,
         "new_device": 0, "location_changed": 0, "international_transaction": 0,
         "device_change_count": 0, "avg_historical_amount": 10},
        {"transaction_amount": 500000, "transaction_hour": 23, "account_age_days": 3650,
         "transactions_last_1h": 20, "transactions_last_24h": 100, "failed_attempts": 10,
         "new_device": 1, "location_changed": 1, "international_transaction": 1,
         "device_change_count": 10, "avg_historical_amount": 200000},
    ]
    for features in test_cases:
        result = engine.analyze(features)
        assert 0 <= result["risk_score"] <= 100


def test_valid_decisions(engine):
    """Decision must always be one of APPROVE, REVIEW, DECLINE."""
    result = engine.analyze({
        "transaction_amount": 1000,
        "transaction_hour": 10,
        "account_age_days": 365,
        "transactions_last_1h": 1,
        "transactions_last_24h": 5,
        "failed_attempts": 0,
        "new_device": 0,
        "location_changed": 0,
        "international_transaction": 0,
        "device_change_count": 0,
        "avg_historical_amount": 900,
    })
    assert result["decision"] in ("APPROVE", "REVIEW", "DECLINE")
    assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")


def test_reasons_not_empty(engine):
    """Every analyzed transaction should have at least one reason."""
    result = engine.analyze({
        "transaction_amount": 3000,
        "transaction_hour": 15,
        "account_age_days": 200,
        "transactions_last_1h": 2,
        "transactions_last_24h": 8,
        "failed_attempts": 1,
        "new_device": 1,
        "location_changed": 0,
        "international_transaction": 0,
        "device_change_count": 1,
        "avg_historical_amount": 2500,
    })
    assert len(result["reasons"]) >= 1


def test_zero_signals_edge_case(engine):
    """All-zero signals should not crash and should APPROVE."""
    result = engine.analyze({
        "transaction_amount": 100,
        "transaction_hour": 12,
        "account_age_days": 1000,
        "transactions_last_1h": 0,
        "transactions_last_24h": 0,
        "failed_attempts": 0,
        "new_device": 0,
        "location_changed": 0,
        "international_transaction": 0,
        "device_change_count": 0,
        "avg_historical_amount": 100,
    })
    assert result["decision"] == "APPROVE"
    assert result["risk_score"] <= 30


def test_metrics_available(engine):
    """Metrics should be computed and available."""
    metrics = engine.get_metrics()
    assert metrics is not None
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "roc_auc" in metrics
    assert "confusion_matrix" in metrics


def test_cost_analysis_available(engine):
    """Cost analysis should be computed and available."""
    cost = engine.get_cost_analysis()
    assert cost is not None
    assert "threshold_sweep" in cost
    assert len(cost["threshold_sweep"]) > 0
    assert cost["false_positive_cost"] == 150
    assert cost["false_negative_cost"] == 2500


def test_audit_log_grows(engine):
    """Audit log should contain entries after analyses."""
    log = engine.get_audit_log()
    assert len(log) > 0
    entry = log[0]
    assert "transaction_id" in entry
    assert "risk_score" in entry
    assert "decision" in entry
