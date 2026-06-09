import React from 'react';

export default function BiasFlowChart({ flow }) {
  if (!flow || flow.length < 2) return null;

  const W = 800;
  const H = 160;
  const PAD_X = 40;
  const PAD_Y = 20;
  const chartW = W - PAD_X * 2;
  const chartH = H - PAD_Y * 2;

  const stepX = chartW / Math.max(flow.length - 1, 1);
  const midY = PAD_Y + chartH / 2;

  // Build polyline points
  const points = flow.map((f, i) => {
    const x = PAD_X + i * stepX;
    const y = midY - f.direction * (chartH / 2);
    return { x, y, ...f };
  });

  const polyline = points.map(p => `${p.x},${p.y}`).join(' ');

  // Area fill (gradient below/above center line)
  const areaPath = `M ${points[0].x},${midY} ` +
    points.map(p => `L ${p.x},${p.y}`).join(' ') +
    ` L ${points[points.length - 1].x},${midY} Z`;

  return (
    <div className="bias-flow glass-card fade-in">
      <h3 className="chart-title">Bias Flow Across Article</h3>
      <div className="flow-chart-wrapper">
        <svg viewBox={`0 0 ${W} ${H}`} className="flow-svg" preserveAspectRatio="none">
          <defs>
            <linearGradient id="flowGradLeft" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="flowGradRight" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#f43f5e" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Background zones */}
          <rect x={PAD_X} y={PAD_Y} width={chartW} height={chartH / 2}
            fill="rgba(59,130,246,0.04)" rx="4" />
          <rect x={PAD_X} y={midY} width={chartW} height={chartH / 2}
            fill="rgba(244,63,94,0.04)" rx="4" />

          {/* Center line */}
          <line x1={PAD_X} y1={midY} x2={W - PAD_X} y2={midY}
            stroke="rgba(255,255,255,0.1)" strokeWidth="1" strokeDasharray="4,4" />

          {/* Area fill */}
          <path d={areaPath} fill="url(#flowGradLeft)" opacity="0.6" />

          {/* Line */}
          <polyline points={polyline} fill="none"
            stroke="url(#biasFlowLine)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
            style={{ filter: 'drop-shadow(0 0 4px rgba(139,92,246,0.4))' }} />

          <defs>
            <linearGradient id="biasFlowLine" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#3b82f6" />
              <stop offset="50%" stopColor="#8b5cf6" />
              <stop offset="100%" stopColor="#f43f5e" />
            </linearGradient>
          </defs>

          {/* Dots */}
          {points.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r="3.5"
              fill={p.label === 'Left' ? '#3b82f6' : p.label === 'Right' ? '#f43f5e' : '#94a3b8'}
              stroke="var(--bg-primary)" strokeWidth="1.5"
              className="flow-dot" />
          ))}

          {/* Axis labels */}
          <text x={PAD_X - 5} y={PAD_Y + 12} textAnchor="end" fill="#3b82f6" fontSize="9" fontWeight="600">LEFT</text>
          <text x={PAD_X - 5} y={H - PAD_Y - 4} textAnchor="end" fill="#f43f5e" fontSize="9" fontWeight="600">RIGHT</text>
          <text x={PAD_X - 5} y={midY + 3} textAnchor="end" fill="var(--text-muted)" fontSize="8">CENTER</text>

          {/* Sentence markers */}
          <text x={PAD_X} y={H - 2} fill="var(--text-muted)" fontSize="8">S1</text>
          <text x={W - PAD_X} y={H - 2} textAnchor="end" fill="var(--text-muted)" fontSize="8">S{flow.length}</text>
        </svg>
      </div>
    </div>
  );
}
