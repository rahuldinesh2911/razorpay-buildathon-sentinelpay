# PROJECT_SPEC.md
## SentinelPay — AI Payment Risk Manager
### Razorpay AI Buildathon — Track 2: AI Risk Manager

---

## 1. Overview

**Project Name:** SentinelPay — AI Payment Risk Manager

**One-line description:** A lightweight, explainable ML system — served through a React web frontend and a FastAPI backend — that scores payment transactions for fraud risk and recommends APPROVE / REVIEW / DECLINE decisions, backed by measurable business-cost trade-off analysis.

**Problem statement:** Payment platforms must catch fraudulent transactions without over-blocking legitimate ones. Missed fraud causes direct financial loss (false negatives); over-blocking causes customer friction and lost business (false positives). SentinelPay treats this explicitly as a cost-sensitive decision problem, not just a classification problem.

**Scope discipline:** This is a hackathon MVP, not a production system. It is a **defensive risk-analysis tool only**. It does not process real payments, move money, or contain any offensive/evasion techniques. All data is synthetic.

---

## 2. Core Product Flow

```
React Frontend
    ↓
FastAPI REST API
    ↓
Risk Engine
    ↓
RandomForest Model
    ↓
Risk Score (0–100)
    ↓
Decision Engine (configurable thresholds)
    ↓
APPROVE / REVIEW / DECLINE
    ↓
Explanation + Audit Log
```

The ML model and decision engine are fully deterministic and reproducible given the same input and config — no randomness at inference time, no LLM in the decision path. The React frontend is a pure presentation/interaction layer; it never computes risk itself — it always calls the FastAPI backend and renders real returned data.

---

## 3. Dataset

### 3.1 Approach
Synthetic, generated with a reproducible random seed (`RANDOM_SEED` in `backend/config.py`).

### 3.2 Features

| Feature | Type | Description |
|---|---|---|
| `transaction_amount` | float | Transaction value (₹) |
| `transaction_hour` | int (0–23) | Hour of day |
| `account_age_days` | int | Age of the account |
| `transactions_last_1h` | int | Transaction velocity, last hour |
| `transactions_last_24h` | int | Transaction velocity, last 24h |
| `failed_attempts` | int | Recent failed auth/payment attempts |
| `new_device` | binary | Transaction from an unrecognized device |
| `location_changed` | binary | Sudden geographic/IP change |
| `international_transaction` | binary | Cross-border transaction |
| `device_change_count` | int | Number of distinct devices recently used |
| `avg_historical_amount` | float | Customer's historical average transaction amount (used to derive an amount-deviation signal) |

Target: `is_fraud` (binary label). **Not** included as a feature; no leakage.

### 3.3 Realism requirements
- Fraud is **not** determined by a single obvious feature (e.g., not "new_device == 1 → fraud").
- Fraud probability is generated as a weighted, noisy combination of multiple signals (velocity, new device + location change together, failed attempts, deviation from historical amount, account age), with random noise added so classes overlap.
- Class imbalance is enforced (target: roughly 3–8% fraud rate, configurable).
- Data is split into train/test using a stratified split (e.g., 80/20) so the fraud rate is preserved in both sets, with the held-out test set never used during training.

### 3.4 Data files
- `backend/data/transactions.csv` — full generated dataset (train/test split handled at load time, or stored as separate files if simpler).

---

## 4. Machine Learning

- **Model:** `RandomForestClassifier` (scikit-learn). Chosen for reliability, fast training, native probability outputs, and easy feature-importance-based explanations.
- **Class imbalance handling:** `class_weight='balanced'` (or equivalent), evaluated to confirm it materially helps before committing.
- **Training pipeline (`backend/train.py`):**
  1. Load dataset.
  2. Stratified train/test split (fixed seed).
  3. Fit `RandomForestClassifier` on train set.
  4. Evaluate on held-out test set only.
  5. Persist model with `joblib` to `backend/models/risk_model.pkl`.
- **Inference:** `backend/risk_engine.py` loads the persisted model **once at FastAPI startup** and reuses it for every request. The model is never retrained during an API call.
- **No fabricated metrics.** All displayed numbers come from actual `sklearn.metrics` calculations on the real held-out test set, computed once at startup (or cached) and served via `GET /api/metrics`. If performance is weak, the dataset/features are iterated on rather than the numbers being altered.

### 4.1 Evaluation metrics
- Precision, Recall, F1-score
- Confusion matrix
- ROC-AUC
- False-positive rate
- All computed via `sklearn.metrics` on the test set.

---

## 5. Risk Scoring

- Model outputs a fraud probability `p ∈ [0, 1]` from `predict_proba`.
- Risk score = `round(p * 100)`, clipped to `[0, 100]`.
- Default bands (configurable in `backend/config.py`, **not** hardcoded in logic):

| Score range | Risk level | Default decision |
|---|---|---|
| 0–30 | LOW | APPROVE |
| 31–70 | MEDIUM | REVIEW |
| 71–100 | HIGH | DECLINE |

- Thresholds are explicitly presented in the UI (Business Cost / Model Performance sections) as **configurable risk-policy choices**, not universal truths.
- Where practical, a threshold-vs-cost sweep is used to illustrate how the "optimal" threshold shifts depending on the assumed cost ratio between false positives and false negatives.

---

## 6. Business Cost Analysis

Illustrative, clearly-labeled example costs (configurable in `backend/config.py`, **not** claimed to be Razorpay's real figures):

- `false_positive_cost = ₹150` (friction/support cost of wrongly blocking a legitimate transaction)
- `false_negative_cost = ₹2500` (loss from an undetected fraudulent transaction)

**Formula:**
```
Total Cost = (False Positives × FP Cost) + (False Negatives × FN Cost)
```

**Deliverables (served via `GET /api/cost-analysis`, rendered in the Business Cost section of the frontend):**
- Cost computed at the current/default threshold on the test set.
- A threshold sweep table/chart showing, for a range of thresholds: precision, recall, false positives, false negatives, and total estimated cost — so the trade-off is visible rather than asserted.
- All cost figures are explicitly labeled in the UI and README as **illustrative assumptions for demonstration purposes only**.

---

## 7. Explainability

- Every scored transaction returns a structured explanation as part of the `POST /api/analyze` response, e.g.:

```json
{
  "risk_score": 87,
  "risk_level": "HIGH",
  "decision": "DECLINE",
  "reasons": [
    "New device detected",
    "Unusually high transaction velocity",
    "Multiple failed attempts",
    "Unusual transaction amount vs. customer history",
    "Recent location change"
  ]
}
```

- Explanations are derived deterministically from feature values / thresholds and (optionally) model feature importances — implemented in `backend/explainability.py`.
- An LLM **may** optionally be used purely to phrase the explanation in more natural language (P2, optional), but it **never** influences the score or decision. The core decision path has zero LLM dependency and is fully reproducible without any API calls.
- The React frontend only renders the `reasons` array and decision fields returned by the API — it does not generate or alter explanations client-side.

---

## 8. AI Agent / Orchestration Concept

Presented conceptually as an agentic risk-review workflow, implemented as a clean Python orchestration layer inside the FastAPI backend (no multi-agent framework):

1. Receive transaction input via `POST /api/analyze`.
2. Extract/validate features.
3. Query trained ML model for risk probability.
4. Apply configured risk policy (thresholds) → decision.
5. Generate explanation from contributing signals.
6. Return risk score, decision, explanation as JSON.
7. Append record to the in-memory audit log.

No external agent framework, no unnecessary orchestration complexity — a plain function/class pipeline inside `risk_engine.py` is sufficient and preferred.

---

## 9. Architecture

```
React Frontend (Vite)
      ↓  HTTP/JSON (fetch/axios)
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

- **Frontend:** React + Vite, modern responsive UI, Tailwind CSS if convenient. Talks to the backend exclusively via REST calls — no direct ML logic in the browser.
- **Backend:** Python + FastAPI, synchronous, no auth. Owns the model, the decision policy, the cost config, and the audit log.
- **ML:** pandas, numpy, scikit-learn, joblib — unchanged from the original design.
- The backend is the single source of truth for risk scores and metrics; the frontend never fabricates or caches stale numbers beyond a single response.

---

## 10. FastAPI Backend

### 10.1 Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/analyze` | Accepts transaction feature payload, returns risk score, risk level, decision, and reasons. Also appends the result to the in-memory audit log. |
| `GET` | `/api/metrics` | Returns held-out test-set metrics: precision, recall, F1, confusion matrix, ROC-AUC, false-positive rate, total transactions, fraud rate. |
| `GET` | `/api/cost-analysis` | Returns FP/FN cost config, total estimated cost at the current threshold, and the threshold-sweep table (precision/recall/FP/FN/cost per threshold). |
| `GET` | `/api/audit-log` | Returns the in-memory list of analyzed transactions (timestamp, transaction ID, amount, risk score, decision, key reasons). |
| `GET` | `/api/health` | Simple liveness/readiness check, confirms the model is loaded. |

### 10.2 Backend behavior rules
- The model is loaded **once**, at application startup (e.g., via a FastAPI startup event or module-level load), and reused for every request.
- The backend **never retrains** the model in response to an API call.
- No database — the audit log is a simple in-memory list (e.g., a Python list or `deque`) scoped to the running server process. It resets on restart; this is acceptable and should be stated clearly in the README.
- No authentication, no sessions beyond in-memory state, no external services.
- Endpoints are simple, synchronous, and return plain JSON — no streaming, no websockets required.
- CORS is enabled (permissive, since there's no auth) so the Vite dev server can call the API directly during local development.

---

## 11. React Frontend

Built with React + Vite, modern responsive layout, Tailwind CSS used if it speeds up styling (not mandatory if plain CSS is faster to ship reliably).

**Sections / components:**

**A. Overview** — Total transactions, fraud rate, precision, recall, F1, false positives, false negatives (pulled from `GET /api/metrics`).

**B. Transaction Analyzer** (core demo feature)
- Form inputs: amount, hour, account age, transactions last 1h/24h, failed attempts, new device, location changed, international transaction, device change count.
- "Analyze Transaction" button → calls `POST /api/analyze`.
- Result view: risk score (numeric + visual gauge/bar), color-coded risk level badge (LOW/MEDIUM/HIGH), decision badge (APPROVE/REVIEW/DECLINE), and a list of risk-factor reasons.

**C. Risk Score Visualization** — A simple gauge, progress bar, or colored meter representing the 0–100 score, driven entirely by the value returned from the API (no client-side scoring logic).

**D. Model Performance** — Confusion matrix, precision, recall, F1, ROC-AUC, pulled from `GET /api/metrics`.

**E. Business Cost Analysis** — FP cost, FN cost, total estimated cost, threshold comparison table/chart, pulled from `GET /api/cost-analysis`.

**F. Audit Log** — Table of analyzed transactions pulled from `GET /api/audit-log`: timestamp, transaction ID, amount, risk score, decision, key reasons.

**G. Responsive design** — Layout adapts cleanly to a laptop-sized demo screen and to smaller windows; this is a hackathon-demo requirement, not a full mobile-optimization effort.

**Suggested structure:**
- `services/` — a thin API client (e.g., `api.js`) wrapping `fetch`/`axios` calls to the five endpoints.
- `components/` — one component per section above (Overview, TransactionAnalyzer, RiskScoreGauge, ModelPerformance, BusinessCost, AuditLog).
- `App.jsx` — layout/composition of the above into the dashboard.

**UI/UX:** Fintech/payment-security visual theme, clear color-coded risk states (e.g., green/amber/red), no overdesign — the Transaction Analyzer remains the visual and narrative centerpiece, unchanged from the original concept.

---

## 12. Project Structure

```
sentinelpay/
├── backend/
│   ├── main.py                 # FastAPI app, endpoint definitions, startup model load
│   ├── risk_engine.py          # Inference + decision engine (scoring, decision, audit log)
│   ├── explainability.py       # Deterministic reason/explanation generation
│   ├── config.py               # Thresholds, costs, feature lists, random seed
│   ├── train.py                # Data loading, training, evaluation, model persistence
│   ├── generate_data.py        # Synthetic dataset generation
│   ├── requirements.txt
│   ├── data/
│   │   └── transactions.csv
│   ├── models/
│   │   └── risk_model.pkl
│   └── tests/
│       └── test_risk_engine.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── components/
│       │   ├── Overview.jsx
│       │   ├── TransactionAnalyzer.jsx
│       │   ├── RiskScoreGauge.jsx
│       │   ├── ModelPerformance.jsx
│       │   ├── BusinessCost.jsx
│       │   └── AuditLog.jsx
│       └── services/
│           └── api.js
│
├── README.md
└── PROJECT_SPEC.md
```

Structure may be simplified further if it improves reliability (e.g., fewer components, flatter folders), but no essential module should be merged away to the point of harming clarity.

---

## 13. Testing (`backend/tests/test_risk_engine.py`)

Minimum coverage (backend-focused, since the ML/decision logic lives entirely server-side):
1. Clearly low-risk/normal transaction → APPROVE.
2. Clearly high-risk/suspicious transaction → DECLINE.
3. Ambiguous/medium-signal transaction → REVIEW.
4. Edge cases (e.g., zero account age, extreme amount, all-zero signals).
5. Risk score is always within `[0, 100]`.
6. Decision is always exactly one of `APPROVE`, `REVIEW`, `DECLINE`.

Optionally, a basic smoke test can hit `/api/health` and `/api/analyze` via FastAPI's `TestClient` to confirm the API layer works end-to-end, but this is P1/P2, not a substitute for the risk-engine unit tests above.

The application (backend + frontend) must run without errors from a clean setup.

---

## 14. Safety Constraints

SentinelPay is a **defensive** fintech/risk-analysis project. It explicitly excludes:
- Real payment processing or money movement.
- Fraud evasion techniques or attack automation.
- Credential theft, unauthorized access, or offensive security content.
- Databases, authentication, Docker, Kubernetes, microservices, Redis, message queues, cloud infrastructure, or multi-agent frameworks — all explicitly out of scope for this MVP.
- Any use of real customer or transaction data (synthetic/demo data only).

---

## 15. Local Development Flow

**Terminal 1 — Backend:**
```
cd backend
pip install -r requirements.txt   # first time only
uvicorn main:app --reload
```

**Terminal 2 — Frontend:**
```
cd frontend
npm install
npm run dev
```

The Vite dev server proxies or directly calls the FastAPI backend (typically `http://localhost:8000`); the frontend dev server typically runs on `http://localhost:5173`. CORS is enabled on the backend so this works without extra configuration.

---

## 16. Demo Script (5-Minute Flow)

1. Start the backend (`uvicorn main:app --reload`) and frontend (`npm run dev`); open the React dashboard.
2. Enter a normal, low-signal transaction in the Transaction Analyzer → Analyze → **APPROVE**.
3. Enter a suspicious, high-signal transaction → Analyze → **HIGH RISK / DECLINE**.
4. Walk through the displayed reasons (returned live from `/api/analyze`).
5. Show real model metrics from the Model Performance section (precision/recall/F1/confusion matrix/ROC-AUC), sourced from `/api/metrics`.
6. Show the false-positive vs. false-negative cost breakdown and threshold trade-off in the Business Cost section, sourced from `/api/cost-analysis`.
7. Show the Audit Log updating live with each analyzed transaction.
8. Briefly narrate the architecture: React frontend → FastAPI → risk engine → RandomForest model → decision engine → explanation + audit log.

Every step in this flow is treated as P0 and must work reliably against the real running backend — no mocked or hardcoded frontend data.

---

## 17. README Contents (to be generated later)

Project title; one-line description; problem; solution; key features; architecture (React + FastAPI + ML, per Section 9); ML approach; dataset description; evaluation methodology; metrics; business-cost methodology; API endpoint reference (Section 10.1); **installation and run instructions for both backend and frontend, exactly as in Section 15**; screenshots section; limitations (including that the audit log is in-memory and resets on restart); future improvements; safety statement.

Explicit disclaimers that the system is **not production-ready**, the dataset is **not real Razorpay data**, and cost figures are **illustrative, not real Razorpay costs**.

---

## 18. Engineering Priorities

**P0 — Must work:**
- Working FastAPI backend
- Working React frontend
- ML model (trained, persisted, loaded once)
- Held-out evaluation
- Risk scoring
- Approve/Review/Decline
- Explainability
- Transaction Analyzer (frontend form → real API call → real result)
- Real API integration end-to-end (no mocked frontend data)

**P1 — Should have:**
- Business cost analysis
- Audit log
- Metrics dashboard (Model Performance section)
- Tests

**P2 — Nice to have:**
- Extra visualizations
- Model comparison
- Optional LLM explanation phrasing layer

P2 work — and frontend visual polish beyond a clean, professional baseline — must never consume time needed for P0 ML/backend functionality. Do not let frontend styling iterate at the expense of a working `/api/analyze` → decision → explanation pipeline.

---

## 19. Development Rules

1. Read this spec fully before coding.
2. Inspect existing files before creating new ones.
3. Build incrementally: backend + ML first, then wire the frontend to real endpoints, then polish UI.
4. Run both the backend (`uvicorn`) and frontend (`npm run dev`) after major changes to confirm end-to-end behavior.
5. Fix errors rather than suppressing or ignoring them.
6. Never fabricate metrics or hardcode fake predictions labeled as ML output, on either the backend or frontend.
7. Keep dependencies minimal:
   - Backend: `fastapi`, `uvicorn`, `pandas`, `numpy`, `scikit-learn`, `joblib`, `pydantic` (bundled with FastAPI).
   - Frontend: `react`, `vite`, optionally `tailwindcss`, plus a minimal HTTP client (`fetch` is sufficient; `axios` optional).
8. Prefer simple, reliable implementations over impressive-sounding complexity.
9. No technologies beyond what this spec requires — explicitly no database, no auth, no Docker, no Kubernetes, no microservices, no Redis, no message queues, no cloud infrastructure, no multi-agent frameworks.
10. Keep configuration (thresholds, costs, seed) visible and centralized in `backend/config.py`.
11. The frontend must always consume real data from the FastAPI backend — never hardcode metrics, scores, or audit-log entries client-side.
12. Final application must run locally with exactly the two commands in Section 15 (one per terminal).

---

## 20. Final Acceptance Criteria

- [ ] Dataset can be generated.
- [ ] Model can be trained.
- [ ] Model is evaluated on held-out data.
- [ ] Actual (non-fabricated) metrics are displayed in the frontend.
- [ ] FastAPI backend starts cleanly and loads the model once at startup.
- [ ] `POST /api/analyze` returns a real, model-derived risk score and decision.
- [ ] `GET /api/metrics`, `/api/cost-analysis`, `/api/audit-log`, `/api/health` all work.
- [ ] React frontend runs via Vite and consumes all five endpoints correctly.
- [ ] New transactions can be analyzed through the Transaction Analyzer UI.
- [ ] Risk score is generated by the trained model, not the frontend.
- [ ] Approve/review/decline decision works end-to-end.
- [ ] Reasons are displayed in the UI.
- [ ] Business-cost calculation works and is shown in the UI.
- [ ] Audit log works (in-memory) and updates live in the UI.
- [ ] Project runs locally via the two-terminal flow in Section 15.
- [ ] README is complete and explains both run commands clearly.
- [ ] No fake claims are made anywhere in the app or docs.
- [ ] No real financial transactions are performed.
- [ ] No database, auth, Docker, Kubernetes, microservices, Redis, message queues, cloud infrastructure, or multi-agent frameworks were introduced.

---

**Core story to keep front-and-center throughout implementation:**
> Detect payment risk → quantify risk → make a defensible decision → explain it → measure the business trade-off — now served through a professional React + FastAPI web application instead of Streamlit.
