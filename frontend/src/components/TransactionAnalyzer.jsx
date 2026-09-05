import { useState } from "react";
import { analyzeTransaction } from "../services/api";
import RiskScoreGauge from "./RiskScoreGauge";

const defaultValues = {
  transaction_amount: 5000,
  transaction_hour: 14,
  account_age_days: 365,
  transactions_last_1h: 1,
  transactions_last_24h: 5,
  failed_attempts: 0,
  new_device: 0,
  location_changed: 0,
  international_transaction: 0,
  device_change_count: 0,
  avg_historical_amount: 4500,
};

const fieldConfig = [
  { key: "transaction_amount", label: "Transaction Amount (₹)", type: "number", min: 1, max: 1000000, step: 1 },
  { key: "transaction_hour", label: "Transaction Hour (0–23)", type: "number", min: 0, max: 23 },
  { key: "account_age_days", label: "Account Age (days)", type: "number", min: 0 },
  { key: "transactions_last_1h", label: "Transactions Last 1h", type: "number", min: 0 },
  { key: "transactions_last_24h", label: "Transactions Last 24h", type: "number", min: 0 },
  { key: "failed_attempts", label: "Failed Attempts", type: "number", min: 0 },
  { key: "new_device", label: "New Device", type: "toggle" },
  { key: "location_changed", label: "Location Changed", type: "toggle" },
  { key: "international_transaction", label: "International Transaction", type: "toggle" },
  { key: "device_change_count", label: "Device Change Count", type: "number", min: 0 },
  { key: "avg_historical_amount", label: "Avg Historical Amount (₹)", type: "number", min: 0, step: 1 },
];

export default function TransactionAnalyzer({ onAnalyzed }) {
  const [form, setForm] = useState(defaultValues);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = { ...form };
      // Ensure numbers
      for (const f of fieldConfig) {
        if (f.type === "number") {
          data[f.key] = Number(data[f.key]);
        }
      }
      const res = await analyzeTransaction(data);
      setResult(res);
      if (onAnalyzed) onAnalyzed();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (preset) => {
    if (preset === "low") {
      setForm({
        transaction_amount: 500,
        transaction_hour: 14,
        account_age_days: 800,
        transactions_last_1h: 0,
        transactions_last_24h: 2,
        failed_attempts: 0,
        new_device: 0,
        location_changed: 0,
        international_transaction: 0,
        device_change_count: 0,
        avg_historical_amount: 450,
      });
    } else if (preset === "high") {
      setForm({
        transaction_amount: 150000,
        transaction_hour: 3,
        account_age_days: 5,
        transactions_last_1h: 8,
        transactions_last_24h: 30,
        failed_attempts: 4,
        new_device: 1,
        location_changed: 1,
        international_transaction: 1,
        device_change_count: 4,
        avg_historical_amount: 2000,
      });
    } else if (preset === "medium") {
      setForm({
        transaction_amount: 15000,
        transaction_hour: 22,
        account_age_days: 45,
        transactions_last_1h: 3,
        transactions_last_24h: 12,
        failed_attempts: 1,
        new_device: 1,
        location_changed: 0,
        international_transaction: 0,
        device_change_count: 2,
        avg_historical_amount: 5000,
      });
    }
  };

  return (
    <section className="analyzer">
      <h2>Transaction Analyzer</h2>
      <p className="section-subtitle">Enter transaction details to get a real-time risk assessment</p>

      <div className="preset-buttons">
        <button className="preset-btn preset-low" onClick={() => loadPreset("low")}>📗 Low Risk Preset</button>
        <button className="preset-btn preset-med" onClick={() => loadPreset("medium")}>📙 Medium Risk Preset</button>
        <button className="preset-btn preset-high" onClick={() => loadPreset("high")}>📕 High Risk Preset</button>
      </div>

      <div className="analyzer-layout">
        <form onSubmit={handleSubmit} className="analyzer-form">
          <div className="form-grid">
            {fieldConfig.map((f) => (
              <div key={f.key} className="form-field">
                <label htmlFor={f.key}>{f.label}</label>
                {f.type === "toggle" ? (
                  <button
                    type="button"
                    className={`toggle-btn ${form[f.key] ? "active" : ""}`}
                    onClick={() => handleChange(f.key, form[f.key] ? 0 : 1)}
                  >
                    {form[f.key] ? "Yes" : "No"}
                  </button>
                ) : (
                  <input
                    id={f.key}
                    type="number"
                    value={form[f.key]}
                    onChange={(e) => handleChange(f.key, e.target.value)}
                    min={f.min}
                    max={f.max}
                    step={f.step || 1}
                  />
                )}
              </div>
            ))}
          </div>
          <button type="submit" className="analyze-btn" disabled={loading}>
            {loading ? "Analyzing..." : "🔍 Analyze Transaction"}
          </button>
        </form>

        {result && (
          <div className="analyzer-result">
            <RiskScoreGauge score={result.risk_score} riskLevel={result.risk_level} />

            <div className={`decision-badge decision-${result.decision.toLowerCase()}`}>
              {result.decision === "APPROVE" && "✅ "}
              {result.decision === "REVIEW" && "⚠️ "}
              {result.decision === "DECLINE" && "🚫 "}
              {result.decision}
            </div>

            <div className="result-details">
              <div className="detail-row">
                <span className="detail-label">Transaction ID</span>
                <span className="detail-value">{result.transaction_id}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Fraud Probability</span>
                <span className="detail-value">{(result.fraud_probability * 100).toFixed(2)}%</span>
              </div>
            </div>

            <div className="reasons">
              <h4>Risk Factors</h4>
              <ul>
                {result.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {error && <div className="error-msg">❌ {error}</div>}
      </div>
    </section>
  );
}
