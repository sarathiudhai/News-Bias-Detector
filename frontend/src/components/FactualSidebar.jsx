import React from 'react';

export default function FactualSidebar({ paragraphs }) {
  if (!paragraphs || paragraphs.length === 0) return null;

  return (
    <div className="factual-sidebar glass-card fade-in">
      <h3>Factual Density</h3>
      {paragraphs.map((p, i) => {
        const s = p.factual_score;
        const level = s >= 60 ? 'high' : s >= 35 ? 'mid' : 'low';
        return (
          <div key={i} className="para-meter">
            <div className="para-meter-label">Paragraph {i + 1} — {s}%</div>
            <div className="meter-track">
              <div className={`meter-fill ${level}`} style={{ width: `${s}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
