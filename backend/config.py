# backend/config.py — Centralized configuration for SentinelPay

RANDOM_SEED = 42

# --- Dataset ---
NUM_SAMPLES = 10000
FRAUD_RATE = 0.05  # ~5% fraud
TEST_SIZE = 0.2    # 80/20 stratified split

# --- Feature list (order matters for model input) ---
FEATURE_COLUMNS = [
    "transaction_amount",
    "transaction_hour",
    "account_age_days",
    "transactions_last_1h",
    "transactions_last_24h",
    "failed_attempts",
    "new_device",
    "location_changed",
    "international_transaction",
    "device_change_count",
    "avg_historical_amount",
]

# --- Risk thresholds (configurable) ---
LOW_THRESHOLD = 30      # score 0–30 → LOW → APPROVE
HIGH_THRESHOLD = 70     # score 71–100 → HIGH → DECLINE
                        # score 31–70 → MEDIUM → REVIEW

# --- Business cost parameters (illustrative, not real figures) ---
FALSE_POSITIVE_COST = 150    # ₹ — friction/support cost of wrongly blocking a legit txn
FALSE_NEGATIVE_COST = 2500   # ₹ — loss from undetected fraud

# --- Model paths ---
MODEL_PATH = "models/risk_model.pkl"
DATA_PATH = "data/transactions.csv"
