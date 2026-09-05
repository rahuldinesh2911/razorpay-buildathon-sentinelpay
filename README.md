# SentinelPay — AI Payment Risk Manager

> Razorpay AI Buildathon — Track 2: AI Risk Manager

A lightweight, explainable ML system — served through a React web frontend and a FastAPI backend — that scores payment transactions for fraud risk and recommends **APPROVE / REVIEW / DECLINE** decisions, backed by measurable business-cost trade-off analysis.

## Problem

Payment platforms must catch fraudulent transactions without over-blocking legitimate ones. Missed fraud causes direct financial loss (false negatives); over-blocking causes customer friction and lost business (false positives). SentinelPay treats this explicitly as a **cost-sensitive decision problem**, not just a classification problem.

## Solution

SentinelPay uses a trained **RandomForest** ML model to score transactions on a 0–100 risk scale, make threshold-based decisions (APPROVE/REVIEW/DECLINE), and provide deterministic, explainable reasons for every decision — all served through a professional React + FastAPI web application.

## Key Features

- **Real ML Model**: RandomForestClassifier trained on synthetic data with balanced class weights
- **Explainable Decisions**: Every scored transaction returns human-readable risk factor reasons
- **Business Cost Analysis**: FP/FN cost trade-off with threshold sweep visualization
- **Real-Time Scoring**: React frontend calls FastAPI backend for live risk assessment
- **Audit Log**: In-memory log of all analyzed transactions (resets on restart)
- **No Fabricated Metrics**: All numbers come from actual sklearn.metrics on held-out test data

## Architecture

```
React Frontend (Vite)
      ↓  HTTP/JSON (fetch)
FastAPI REST API
      ↓
Risk Engine (risk_engine.py)
      ↓
RandomForest Model (joblib-loaded once at startup)
      ↓
Risk Score (0–100)
      ↓
Decision Engine (APPROVE / REVIEW / DECLINE)
      ↓
Explanation (explainability.py) + Audit Log (in-memory)
```

## ML Approach

- **Model**: `RandomForestClassifier` (scikit-learn) with `class_weight='balanced'`
- **Dataset**: 10,000 synthetic transactions, ~5% fraud rate, reproducible (seed=42)
- **Features**: 11 signals including amount, velocity, device, location, account age
- **Fraud Generation**: Multi-signal weighted combination with noise (no single-feature shortcuts)
- **Split**: 80/20 stratified train/test
- **Evaluation**: All metrics computed on held-out test set only

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/analyze` | Score a transaction → risk score, decision, reasons |
| `GET` | `/api/metrics` | Model performance metrics (precision, recall, F1, ROC-AUC, confusion matrix) |
| `GET` | `/api/cost-analysis` | Business cost analysis with threshold sweep |
| `GET` | `/api/audit-log` | In-memory audit log of analyzed transactions |
| `GET` | `/api/health` | Health check, confirms model is loaded |

## Installation & Running

### Prerequisites
- Python 3.10+
- Node.js 18+

### Terminal 1 — Backend

```bash
cd backend
pip install -r requirements.txt   # first time only
python generate_data.py           # generate synthetic dataset
python train.py                   # train and evaluate model
uvicorn main:app --reload         # start API server on :8000
```

### Terminal 2 — Frontend

```bash
cd frontend
npm install                       # first time only
npm run dev                       # start dev server on :5173
```

Open http://localhost:5173 in your browser.

## Screenshots

*(Add screenshots of the running application here)*

## Limitations

- **Not production-ready**: This is a hackathon MVP for demonstration purposes
- **Synthetic data only**: The dataset is algorithmically generated, not real transaction data
- **In-memory audit log**: Resets when the server restarts
- **No authentication**: No user auth, sessions, or access control
- **Illustrative costs**: FP cost (₹150) and FN cost (₹2,500) are example figures, not real Razorpay costs

## Safety Statement

SentinelPay is a **defensive** risk-analysis tool only. It does not:
- Process real payments or move money
- Contain fraud evasion techniques or attack automation
- Use real customer or transaction data
- Include databases, auth, Docker, Kubernetes, or cloud infrastructure

All data is synthetic. All cost figures are illustrative assumptions for demonstration purposes only.

---

Built for the Razorpay AI Buildathon 2026.
