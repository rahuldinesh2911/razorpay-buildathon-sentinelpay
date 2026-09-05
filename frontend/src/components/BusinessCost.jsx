import { useState, useEffect } from "react";
import { getCostAnalysis } from "../services/api";

export default function BusinessCost() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getCostAnalysis()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="card error">Failed to load: {error}</div>;
  if (!data) return <div className="card loading">Loading cost analysis...</div>;

  // Find minimum cost threshold
  const minCostEntry = data.threshold_sweep.reduce((min, e) =>
    e.total_cost < min.total_cost ? e : min
  );

  return (
    <section className="business-cost">
      <h2>Business Cost Analysis</h2>
      <p className="section-subtitle">
        Illustrative cost assumptions — not real Razorpay figures
      </p>

      <div className="cost-summary">
        <div className="cost-card">
          <span className="cost-icon">🟢</span>
          <span className="cost-value">₹{data.false_positive_cost}</span>
          <span className="cost-label">False Positive Cost</span>
          <span className="cost-desc">Per wrongly blocked legit txn</span>
        </div>
        <div className="cost-card">
          <span className="cost-icon">🔴</span>
          <span className="cost-value">₹{data.false_negative_cost.toLocaleString()}</span>
          <span className="cost-label">False Negative Cost</span>
          <span className="cost-desc">Per undetected fraud</span>
        </div>
        <div className="cost-card highlight">
          <span className="cost-icon">💰</span>
          <span className="cost-value">₹{data.current_threshold_cost.toLocaleString()}</span>
          <span className="cost-label">Current Total Cost</span>
          <span className="cost-desc">FP×{data.current_false_positives} + FN×{data.current_false_negatives}</span>
        </div>
        <div className="cost-card optimal">
          <span className="cost-icon">🎯</span>
          <span className="cost-value">₹{minCostEntry.total_cost.toLocaleString()}</span>
          <span className="cost-label">Optimal Cost (Threshold {minCostEntry.threshold}%)</span>
          <span className="cost-desc">Best threshold from sweep</span>
        </div>
      </div>

      <div className="sweep-table-container">
        <h3>Threshold Sweep</h3>
        <p className="table-note">Shows how decision threshold affects cost trade-offs</p>
        <div className="table-scroll">
          <table className="sweep-table">
            <thead>
              <tr>
                <th>Threshold</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>False Positives</th>
                <th>False Negatives</th>
                <th>Total Cost</th>
              </tr>
            </thead>
            <tbody>
              {data.threshold_sweep.map((row) => (
                <tr
                  key={row.threshold}
                  className={row.threshold === minCostEntry.threshold ? "optimal-row" : ""}
                >
                  <td>{row.threshold}%</td>
                  <td>{(row.precision * 100).toFixed(1)}%</td>
                  <td>{(row.recall * 100).toFixed(1)}%</td>
                  <td>{row.false_positives}</td>
                  <td>{row.false_negatives}</td>
                  <td className="cost-cell">₹{row.total_cost.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
