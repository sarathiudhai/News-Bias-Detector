import React, { useState } from 'react';

export default function SentenceCard({ sentence }) {
  const [showTip, setShowTip] = useState(false);
  const { text, bias, emotion, factual, uncertain } = sentence;

  const biasClass = `bias-${bias.label.toLowerCase()}`;
  const emotionClass = emotion.score > 65 ? 'emotion-high' : emotion.score > 35 ? 'emotion-med' : 'emotion-low';
  const uncertainClass = uncertain ? 'uncertain' : '';

  return (
    <span className={`sentence ${biasClass} ${emotionClass} ${uncertainClass}`}
      onMouseEnter={() => setShowTip(true)} onMouseLeave={() => setShowTip(false)}>
      {text}{' '}
      {showTip && (
        <span className="tooltip" role="tooltip">
          <span className="tooltip-row">
            <span className="tooltip-label">Bias</span>
            <span className="tooltip-value" style={{ color: bias.label === 'Left' ? 'var(--bias-left)' : bias.label === 'Right' ? 'var(--bias-right)' : 'var(--bias-center)' }}>
              {bias.label} {bias.score}%
            </span>
          </span>
          <span className="tooltip-row">
            <span className="tooltip-label">Emotion</span>
            <span className="tooltip-value" style={{ color: 'var(--accent-amber)' }}>{emotion.label} {emotion.score}%</span>
          </span>
          <span className="tooltip-row">
            <span className="tooltip-label">Factual</span>
            <span className="tooltip-value" style={{ color: 'var(--accent-emerald)' }}>{factual.score}%</span>
          </span>
          {emotion.flagged_words?.length > 0 && (
            <span style={{ display: 'block' }}>
              <span className="tooltip-label" style={{ fontSize: '0.7rem' }}>Emotional words:</span>
              <span className="tooltip-words">
                {emotion.flagged_words.map((w, i) => <span key={i} className="tooltip-tag">{w}</span>)}
              </span>
            </span>
          )}
          {factual.entities?.length > 0 && (
            <span style={{ display: 'block', marginTop: '0.3rem' }}>
              <span className="tooltip-label" style={{ fontSize: '0.7rem' }}>Entities:</span>
              <span className="tooltip-words">
                {factual.entities.map((e, i) => <span key={i} className="tooltip-entity-tag">{e}</span>)}
              </span>
            </span>
          )}
          {uncertain && <span style={{ display: 'block', color: 'var(--accent-amber)', marginTop: '0.3rem', fontSize: '0.7rem' }}>⚠ Low confidence</span>}
        </span>
      )}
    </span>
  );
}
