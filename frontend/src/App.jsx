import { useState } from "react";
import Overview from "./components/Overview";
import TransactionAnalyzer from "./components/TransactionAnalyzer";
import ModelPerformance from "./components/ModelPerformance";
import BusinessCost from "./components/BusinessCost";
import AuditLog from "./components/AuditLog";

export default function App() {
  const [auditRefreshKey, setAuditRefreshKey] = useState(0);

  const handleAnalyzed = () => {
    setAuditRefreshKey((k) => k + 1);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">🛡️</span>
            <h1>SentinelPay</h1>
          </div>
          <p className="tagline">AI Payment Risk Manager</p>
        </div>
      </header>

      <main className="dashboard">
        <Overview />
        <TransactionAnalyzer onAnalyzed={handleAnalyzed} />
        <ModelPerformance />
        <BusinessCost />
        <AuditLog refreshKey={auditRefreshKey} />
      </main>

      <footer className="app-footer">
        <p>
          SentinelPay — Razorpay AI Buildathon. All data is synthetic. Cost figures are illustrative only.
          Not a production system.
        </p>
      </footer>
    </div>
  );
}
