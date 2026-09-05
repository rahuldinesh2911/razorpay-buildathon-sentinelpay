import { useState, useEffect } from "react";
import { getMetrics } from "../services/api";

export default function ModelPerformance() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getMetrics()
      .then(setMetrics)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="card error">Failed to load: {error}</div>;
  if (!metrics) return <div className="card loading">Loading performance data...</div>;

  const cm = metrics.confusion_matrix;
  const total = cm.true_negatives + cm.false_positives + cm.false_negatives + cm.true_positives;

  return (
    <section className="model-performance">
      <h2>Model Performance</h2>
      <p className="section-subtitle">Evaluated on held-out test set — no data leakage</p>

      <div className="performance-grid">
        <div className="confusion-matrix-card">
          <h3>Confusion Matrix</h3>
          <table className="confusion-table">
            <thead>
              <tr>
                <th></th>
                <th>Predicted Legit</th>
                <th>Predicted Fraud</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="row-label">Actual Legit</td>
                <td className="cm-tn">{cm.true_negatives}</td>
                <td className="cm-fp">{cm.false_positives}</td>
              </tr>
              <tr>
                <td className="row-label">Actual Fraud</td>
                <td className="cm-fn">{cm.false_negatives}</td>
                <td className="cm-tp">{cm.true_positives}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="metrics-detail-card">
          <h3>Key Metrics</h3>
          <div className="metric-bars">
            {[
              { label: "Precision", value: metrics.precision },
              { label: "Recall", value: metrics.recall },
              { label: "F1 Score", value: metrics.f1_score },
              { label: "ROC-AUC", value: metrics.roc_auc },
            ].map((m) => (
              <div key={m.label} className="metric-bar-row">
                <span className="metric-bar-label">{m.label}</span>
                <div className="metric-bar-track">
                  <div
                    className="metric-bar-fill"
                    style={{ width: `${m.value * 100}%` }}
                  />
                </div>
                <span className="metric-bar-value">{(m.value * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
          <div className="fpr-note">
            False Positive Rate: {(metrics.false_positive_rate * 100).toFixed(2)}%
          </div>
        </div>
      </div>
    </section>
  );
}
