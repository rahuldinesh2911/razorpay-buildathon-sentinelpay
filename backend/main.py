"""
backend/main.py — FastAPI application for SentinelPay.

Endpoints:
  POST /api/analyze       — Score a transaction
  GET  /api/metrics       — Model performance metrics
  GET  /api/cost-analysis — Business cost analysis
  GET  /api/audit-log     — In-memory audit log
  GET  /api/health        — Health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from risk_engine import engine


# --- Pydantic models ---

class TransactionInput(BaseModel):
    transaction_amount: float = Field(..., gt=0, description="Transaction value in ₹")
    transaction_hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    account_age_days: int = Field(..., ge=0, description="Account age in days")
    transactions_last_1h: int = Field(..., ge=0, description="Transactions in last hour")
    transactions_last_24h: int = Field(..., ge=0, description="Transactions in last 24h")
    failed_attempts: int = Field(..., ge=0, description="Recent failed attempts")
    new_device: int = Field(..., ge=0, le=1, description="New device (0 or 1)")
    location_changed: int = Field(..., ge=0, le=1, description="Location changed (0 or 1)")
    international_transaction: int = Field(..., ge=0, le=1, description="International (0 or 1)")
    device_change_count: int = Field(..., ge=0, description="Distinct devices recently used")
    avg_historical_amount: float = Field(..., ge=0, description="Customer's avg transaction amount")

class ReasonResponse(BaseModel):
    transaction_id: str
    timestamp: str
    risk_score: int
    risk_level: str
    decision: str
    reasons: List[str]
    fraud_probability: float
    input_features: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool

# --- App lifecycle ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load model and compute metrics
    engine.load()
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title="SentinelPay API",
    description="AI Payment Risk Manager — Razorpay AI Buildathon",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — permissive for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Endpoints ---

@app.get("/api/health", response_model=HealthResponse)
def health():
    return {
        "status": "healthy",
        "model_loaded": engine.model is not None,
    }


@app.post("/api/analyze", response_model=ReasonResponse)
def analyze_transaction(txn: TransactionInput):
    if engine.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    features = txn.model_dump()
    result = engine.analyze(features)
    return result


@app.get("/api/metrics")
def get_metrics():
    metrics = engine.get_metrics()
    if metrics is None:
        raise HTTPException(status_code=503, detail="Metrics not available")
    return metrics


@app.get("/api/cost-analysis")
def get_cost_analysis():
    cost = engine.get_cost_analysis()
    if cost is None:
        raise HTTPException(status_code=503, detail="Cost analysis not available")
    return cost


@app.get("/api/audit-log")
def get_audit_log():
    return {"entries": engine.get_audit_log()}
