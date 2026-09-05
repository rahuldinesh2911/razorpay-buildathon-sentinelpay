import { useState, useEffect } from "react";
import { getAuditLog } from "../services/api";

export default function AuditLog({ refreshKey }) {
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    getAuditLog()
      .then((data) => setEntries(data.entries))
      .catch((e) => setError(e.message));
  }, [refreshKey]);

  if (error) return <div className="card error">Failed to load audit log: {error}</div>;

  return (
    <section className="audit-log">
      <h2>Audit Log</h2>
      <p className="section-subtitle">
        In-memory log of analyzed transactions (resets on server restart)
      </p>

      {entries.length === 0 ? (
        <div className="empty-state">
          <span className="empty-icon">📋</span>
          <p>No transactions analyzed yet. Use the Transaction Analyzer above to get started.</p>
        </div>
      ) : (
        <div className="table-scroll">
          <table className="audit-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Timestamp</th>
                <th>Amount</th>
                <th>Risk Score</th>
                <th>Level</th>
                <th>Decision</th>
                <th>Top Reasons</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.transaction_id}>
                  <td className="mono">{e.transaction_id}</td>
                  <td>{new Date(e.timestamp).toLocaleTimeString()}</td>
                  <td>₹{Number(e.amount).toLocaleString()}</td>
                  <td>
                    <span className={`score-pill score-${e.risk_level.toLowerCase()}`}>
                      {e.risk_score}
                    </span>
                  </td>
                  <td>
                    <span className={`risk-badge risk-${e.risk_level.toLowerCase()}`}>
                      {e.risk_level}
                    </span>
                  </td>
                  <td>
                    <span className={`decision-badge decision-${e.decision.toLowerCase()}`}>
                      {e.decision}
                    </span>
                  </td>
                  <td className="reasons-cell">
                    {e.reasons.map((r, i) => (
                      <span key={i} className="reason-tag">{r}</span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
