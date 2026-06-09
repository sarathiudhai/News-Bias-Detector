import React from 'react';

const CATEGORY_COLORS = {
  anger: '#ef4444',
  fear: '#a855f7',
  sadness: '#3b82f6',
  disgust: '#84cc16',
  surprise: '#f59e0b',
  joy: '#22c55e',
  trust: '#06b6d4',
  anticipation: '#ec4899',
  unknown: '#94a3b8',
};

export default function WordCloud({ words }) {
  if (!words || words.length === 0) return null;

  const maxCount = Math.max(...words.map(w => w.count), 1);

  return (
    <div className="word-cloud glass-card fade-in">
      <h3 className="chart-title">Emotional Language</h3>
      <div className="cloud-container">
        {words.map((w, i) => {
          const scale = 0.7 + (w.count / maxCount) * 1.3;
          const color = CATEGORY_COLORS[w.category] || CATEGORY_COLORS.unknown;
          return (
            <span
              key={i}
              className="cloud-word"
              style={{
                fontSize: `${scale}rem`,
                color,
                animationDelay: `${i * 60}ms`,
              }}
              title={`${w.category} — found ${w.count}×`}
            >
              {w.word}
            </span>
          );
        })}
      </div>
      <div className="cloud-legend">
        {Object.entries(CATEGORY_COLORS).filter(([k]) => k !== 'unknown').map(([cat, color]) => (
          <span key={cat} className="cloud-legend-item">
            <span className="legend-dot" style={{ background: color }} />
            {cat}
          </span>
        ))}
      </div>
    </div>
  );
}
