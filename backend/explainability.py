"""
backend/explainability.py — Deterministic explanation generation for SentinelPay.

Generates human-readable reasons based on feature values and thresholds.
No LLM dependency — purely rule-based.
"""


def generate_reasons(features: dict) -> list[str]:
    """
    Given a dict of transaction features, return a list of human-readable
    risk-factor reasons. Order: most concerning signals first.
    """
    reasons = []

    # Amount deviation from historical average
    avg = features.get("avg_historical_amount", 0)
    amount = features.get("transaction_amount", 0)
    if avg > 0:
        deviation = abs(amount - avg) / avg
        if deviation > 3.0:
            reasons.append(f"Transaction amount (₹{amount:,.0f}) is {deviation:.1f}x the customer's average (₹{avg:,.0f})")
        elif deviation > 1.5:
            reasons.append(f"Transaction amount is notably higher than customer's average")

    # New device + location change (compound signal)
    new_device = features.get("new_device", 0)
    location_changed = features.get("location_changed", 0)
    if new_device and location_changed:
        reasons.append("New device detected with simultaneous location change")
    elif new_device:
        reasons.append("Transaction from an unrecognized device")
    elif location_changed:
        reasons.append("Sudden geographic/IP location change detected")

    # Transaction velocity
    txn_1h = features.get("transactions_last_1h", 0)
    txn_24h = features.get("transactions_last_24h", 0)
    if txn_1h >= 5:
        reasons.append(f"Unusually high transaction velocity: {txn_1h} transactions in the last hour")
    elif txn_1h >= 3:
        reasons.append(f"Elevated transaction velocity: {txn_1h} transactions in the last hour")

    if txn_24h >= 20:
        reasons.append(f"Very high 24-hour transaction volume: {txn_24h} transactions")

    # Failed attempts
    failed = features.get("failed_attempts", 0)
    if failed >= 3:
        reasons.append(f"Multiple failed payment attempts ({failed}) — possible credential testing")
    elif failed >= 1:
        reasons.append(f"{failed} recent failed payment attempt(s)")

    # Device change count
    device_changes = features.get("device_change_count", 0)
    if device_changes >= 3:
        reasons.append(f"Frequent device switching ({device_changes} distinct devices recently)")

    # Account age
    account_age = features.get("account_age_days", 0)
    if account_age < 7:
        reasons.append(f"Very new account ({account_age} days old)")
    elif account_age < 30:
        reasons.append(f"Relatively new account ({account_age} days old)")

    # Transaction hour (late night)
    hour = features.get("transaction_hour", 12)
    if 1 <= hour <= 5:
        reasons.append(f"Transaction at unusual hour ({hour}:00)")

    # International transaction
    if features.get("international_transaction", 0):
        reasons.append("Cross-border/international transaction")

    # If no risk factors found, note that
    if not reasons:
        reasons.append("No significant risk indicators detected")

    return reasons
