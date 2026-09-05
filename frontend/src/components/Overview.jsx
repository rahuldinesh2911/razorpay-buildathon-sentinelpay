import { useState, useEffect } from "react";
import { getMetrics } from "../services/api";

export default function Overview() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getMetrics()
      .then(setMetrics)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="card error">Failed to load metrics: {error}</div>;
  if (!metrics) return <div className="card loading">Loading metrics...</div>;

  const stats = [
    { label: "Total Transactions", value: metrics.total_transactions.toLocaleString(), icon: "📊" },
    { label: "Fraud Rate", value: `${(metrics.fraud_rate * 100).toFixed(1)}%`, icon: "🎯" },
    { label: "Precision", value: `${(metrics.precision * 100).toFixed(1)}%`, icon: "🔬" },
    { label: "Recall", value: `${(metrics.recall * 100).toFixed(1)}%`, icon: "📡" },
    { label: "F1 Score", value: `${(metrics.f1_score * 100).toFixed(1)}%`, icon: "⚡" },
    { label: "ROC-AUC", value: `${(metrics.roc_auc * 100).toFixed(1)}%`, icon: "📈" },
  ];

  return (
    <section className="overview">
      <h2>Model Overview</h2>
      <p className="section-subtitle">Held-out test set performance ({metrics.total_transactions} transactions)</p>
      <div className="stats-grid">
        {stats.map((s) => (
          <div key={s.label} className="stat-card">
            <span className="stat-icon">{s.icon}</span>
            <span className="stat-value">{s.value}</span>
            <span className="stat-label">{s.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
