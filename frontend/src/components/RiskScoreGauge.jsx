export default function RiskScoreGauge({ score, riskLevel }) {
  const getColor = () => {
    if (score <= 30) return "#10b981";
    if (score <= 70) return "#f59e0b";
    return "#ef4444";
  };

  const color = getColor();
  const rotation = (score / 100) * 180 - 90; // -90 to 90 degrees

  return (
    <div className="gauge-container">
      <svg viewBox="0 0 200 120" className="gauge-svg">
        {/* Background arc */}
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="16"
          strokeLinecap="round"
        />
        {/* Green zone (0-30) */}
        <path
          d="M 20 100 A 80 80 0 0 1 68 32"
          fill="none"
          stroke="rgba(16,185,129,0.3)"
          strokeWidth="16"
          strokeLinecap="round"
        />
        {/* Yellow zone (30-70) */}
        <path
          d="M 68 32 A 80 80 0 0 1 132 32"
          fill="none"
          stroke="rgba(245,158,11,0.3)"
          strokeWidth="16"
        />
        {/* Red zone (70-100) */}
        <path
          d="M 132 32 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="rgba(239,68,68,0.3)"
          strokeWidth="16"
          strokeLinecap="round"
        />
        {/* Needle */}
        <line
          x1="100"
          y1="100"
          x2="100"
          y2="30"
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
          transform={`rotate(${rotation}, 100, 100)`}
          style={{ transition: "transform 0.8s ease-out" }}
        />
        {/* Center dot */}
        <circle cx="100" cy="100" r="6" fill={color} />
        {/* Score text */}
        <text x="100" y="88" textAnchor="middle" fill="white" fontSize="28" fontWeight="bold">
          {score}
        </text>
        <text x="100" y="115" textAnchor="middle" fill="rgba(255,255,255,0.6)" fontSize="10">
          RISK SCORE
        </text>
      </svg>
      <div className={`risk-badge risk-${riskLevel.toLowerCase()}`}>
        {riskLevel}
      </div>
    </div>
  );
}
