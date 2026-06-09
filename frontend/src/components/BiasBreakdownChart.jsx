import React from 'react';

const COLORS = {
  left: { fill: '#3b82f6', bg: 'rgba(59,130,246,0.15)' },
  center: { fill: '#94a3b8', bg: 'rgba(148,163,184,0.12)' },
  right: { fill: '#f43f5e', bg: 'rgba(244,63,94,0.15)' },
};

export default function BiasBreakdownChart({ distribution }) {
  if (!distribution || distribution.total === 0) return null;

  const { left, center, right, total } = distribution;
  const data = [
    { label: 'Left', count: left, color: COLORS.left },
    { label: 'Center', count: center, color: COLORS.center },
    { label: 'Right', count: right, color: COLORS.right },
  ];

  // Donut chart math
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  let cumulativeOffset = 0;

  const segments = data.map((d) => {
    const pct = d.count / total;
    const dashLength = pct * circumference;
    const offset = -cumulativeOffset;
    cumulativeOffset += dashLength;
    return { ...d, pct, dashLength, offset };
  });

  return (
    <div className="breakdown-chart glass-card fade-in">
      <h3 className="chart-title">Bias Distribution</h3>
      <div className="breakdown-content">
        <div className="donut-wrapper">
          <svg viewBox="0 0 150 150" className="donut-svg">
            {segments.map((seg, i) => (
              <circle
                key={i}
                cx="75" cy="75" r={radius}
                fill="none"
                stroke={seg.color.fill}
                strokeWidth="14"
                strokeDasharray={`${seg.dashLength} ${circumference - seg.dashLength}`}
                strokeDashoffset={seg.offset}
                strokeLinecap="butt"
                style={{ transition: 'stroke-dasharray 1s ease, stroke-dashoffset 1s ease' }}
              />
            ))}
            <text x="75" y="70" textAnchor="middle" fill="var(--text-primary)" fontSize="18" fontWeight="700">
              {total}
            </text>
            <text x="75" y="88" textAnchor="middle" fill="var(--text-muted)" fontSize="10">
              sentences
            </text>
          </svg>
        </div>
        <div className="breakdown-legend">
          {segments.map((seg, i) => (
            <div key={i} className="legend-item">
              <span className="legend-dot" style={{ background: seg.color.fill }} />
              <span className="legend-label">{seg.label}</span>
              <span className="legend-count">{seg.count}</span>
              <span className="legend-pct">{Math.round(seg.pct * 100)}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
