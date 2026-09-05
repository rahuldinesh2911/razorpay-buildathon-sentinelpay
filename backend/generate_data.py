"""
backend/generate_data.py — Synthetic dataset generation for SentinelPay.

Fraud is determined by a weighted, noisy combination of multiple signals,
not by any single feature. Class imbalance is enforced (~5% fraud rate).
"""

import os
import numpy as np
import pandas as pd
from config import RANDOM_SEED, NUM_SAMPLES, FRAUD_RATE, DATA_PATH, FEATURE_COLUMNS

def generate_dataset():
    rng = np.random.RandomState(RANDOM_SEED)
    n = NUM_SAMPLES

    # --- Generate features ---
    transaction_amount = rng.lognormal(mean=7.0, sigma=1.5, size=n).clip(10, 500000)
    transaction_hour = rng.randint(0, 24, size=n)
    account_age_days = rng.exponential(scale=365, size=n).astype(int).clip(0, 3650)
    transactions_last_1h = rng.poisson(lam=1.5, size=n).clip(0, 20)
    transactions_last_24h = (transactions_last_1h * rng.uniform(2, 8, size=n)).astype(int).clip(0, 100)
    failed_attempts = rng.choice([0, 0, 0, 0, 0, 1, 1, 2, 3, 5], size=n)
    new_device = rng.binomial(1, 0.15, size=n)
    location_changed = rng.binomial(1, 0.10, size=n)
    international_transaction = rng.binomial(1, 0.08, size=n)
    device_change_count = rng.poisson(lam=0.5, size=n).clip(0, 10)
    avg_historical_amount = rng.lognormal(mean=6.5, sigma=1.0, size=n).clip(10, 200000)

    # --- Generate fraud labels from multi-signal weighted score + noise ---
    # Normalize signals to [0, 1] range for combination
    amount_deviation = np.abs(transaction_amount - avg_historical_amount) / (avg_historical_amount + 1)
    amount_signal = np.clip(amount_deviation / 5.0, 0, 1)

    velocity_signal = np.clip(transactions_last_1h / 8.0, 0, 1)
    failed_signal = np.clip(failed_attempts / 3.0, 0, 1)
    new_device_loc_signal = (new_device & location_changed).astype(float)
    device_signal = new_device.astype(float) * 0.5
    account_age_signal = np.clip(1.0 - account_age_days / 365.0, 0, 1)
    hour_signal = np.where((transaction_hour >= 1) & (transaction_hour <= 5), 0.5, 0.0)
    intl_signal = international_transaction.astype(float) * 0.3

    # Weighted combination
    fraud_score = (
        0.20 * amount_signal +
        0.20 * velocity_signal +
        0.15 * failed_signal +
        0.15 * new_device_loc_signal +
        0.10 * device_signal +
        0.08 * account_age_signal +
        0.07 * hour_signal +
        0.05 * intl_signal
    )

    # Add noise so classes overlap — no perfect separation
    fraud_score += rng.normal(0, 0.12, size=n)
    fraud_score = np.clip(fraud_score, 0, 1)

    # Set threshold to achieve target fraud rate
    threshold = np.percentile(fraud_score, (1 - FRAUD_RATE) * 100)
    is_fraud = (fraud_score >= threshold).astype(int)

    actual_rate = is_fraud.mean()
    print(f"Generated {n} transactions | Fraud rate: {actual_rate:.2%} ({is_fraud.sum()} frauds)")

    # --- Build DataFrame ---
    df = pd.DataFrame({
        "transaction_amount": np.round(transaction_amount, 2),
        "transaction_hour": transaction_hour,
        "account_age_days": account_age_days,
        "transactions_last_1h": transactions_last_1h,
        "transactions_last_24h": transactions_last_24h,
        "failed_attempts": failed_attempts,
        "new_device": new_device,
        "location_changed": location_changed,
        "international_transaction": international_transaction,
        "device_change_count": device_change_count,
        "avg_historical_amount": np.round(avg_historical_amount, 2),
        "is_fraud": is_fraud,
    })

    # Save
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
    print(f"Saved to {DATA_PATH}")
    return df


if __name__ == "__main__":
    generate_dataset()
