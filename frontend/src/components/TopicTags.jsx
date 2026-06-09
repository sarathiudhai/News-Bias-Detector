import React from 'react';

export default function TopicTags({ topics }) {
  if (!topics || topics.length === 0) return null;

  const categoryIcons = {
    People: '👤',
    Organizations: '🏢',
    Locations: '📍',
    Events: '📅',
    Legislation: '⚖️',
    Groups: '👥',
    Facilities: '🏛️',
    Products: '📦',
    Works: '🎨',
  };

  const categoryColors = {
    People: { bg: 'rgba(139,92,246,0.15)', text: '#a78bfa' },
    Organizations: { bg: 'rgba(6,182,212,0.15)', text: '#22d3ee' },
    Locations: { bg: 'rgba(16,185,129,0.15)', text: '#34d399' },
    Events: { bg: 'rgba(245,158,11,0.15)', text: '#fbbf24' },
    Legislation: { bg: 'rgba(59,130,246,0.15)', text: '#60a5fa' },
    Groups: { bg: 'rgba(236,72,153,0.15)', text: '#f472b6' },
    Facilities: { bg: 'rgba(168,85,247,0.15)', text: '#c084fc' },
    Products: { bg: 'rgba(249,115,22,0.15)', text: '#fb923c' },
    Works: { bg: 'rgba(244,63,94,0.15)', text: '#fb7185' },
  };

  return (
    <div className="topic-tags fade-in">
      <h3 className="chart-title">Detected Topics</h3>
      <div className="tags-container">
        {topics.map((t, i) => {
          const colors = categoryColors[t.category] || { bg: 'rgba(148,163,184,0.12)', text: '#94a3b8' };
          const icon = categoryIcons[t.category] || '🏷️';
          return (
            <span
              key={i}
              className="topic-tag"
              style={{
                background: colors.bg,
                color: colors.text,
                animationDelay: `${i * 50}ms`,
              }}
              title={`${t.category} — mentioned ${t.count}×`}
            >
              <span className="tag-icon">{icon}</span>
              {t.name}
              {t.count > 1 && <span className="tag-count">×{t.count}</span>}
            </span>
          );
        })}
      </div>
    </div>
  );
}
