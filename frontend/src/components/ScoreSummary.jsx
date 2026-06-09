import React from 'react';
import BiasBreakdownChart from './BiasBreakdownChart';
import WordCloud from './WordCloud';
import TopicTags from './TopicTags';

const CIRC = 2 * Math.PI * 46; // radius=46

function Gauge({ value, label, sublabel, colorClass }) {
  const offset = CIRC - (value / 100) * CIRC;
  return (
    <div className="gauge-card glass-card fade-in">
      <div className="gauge-ring">
        <svg viewBox="0 0 100 100">
          <circle className="track" cx="50" cy="50" r="46" />
          <circle className={`fill-${colorClass}`} cx="50" cy="50" r="46"
            strokeDasharray={CIRC} strokeDashoffset={offset} />
        </svg>
        <div className="gauge-value">
          {value}<small>{sublabel || ''}</small>
        </div>
      </div>
      <div className="gauge-label">{label}</div>
    </div>
  );
}

export default function ScoreSummary({ data }) {
  if (!data) return null;
  const { overall_bias, overall_emotion, overall_factual_density, readability, bias_distribution, word_cloud, topics } = data;
  const biasColor = overall_bias.label === 'Left' ? 'blue' : overall_bias.label === 'Right' ? 'rose' : 'amber';

  // Readability color: ease_score maps to green (easy) / amber (moderate) / rose (hard)
  const readabilityColor = readability?.ease_score >= 60 ? 'emerald' : readability?.ease_score >= 30 ? 'amber' : 'rose';

  return (
    <div className="results-dashboard">
      {/* Top gauges row */}
      <div className="score-summary">
        <Gauge value={overall_bias.score} label="Political Bias"
          sublabel={overall_bias.label} colorClass={biasColor} />
        <Gauge value={overall_emotion.score} label="Emotional Charge"
          sublabel="intensity" colorClass="amber" />
        <Gauge value={overall_factual_density.score} label="Factual Density"
          sublabel="facts" colorClass="emerald" />
        {readability && (
          <Gauge value={readability.ease_score} label="Readability"
            sublabel={readability.label} colorClass={readabilityColor} />
        )}
      </div>

      {/* Topics */}
      {topics && topics.length > 0 && <TopicTags topics={topics} />}

      {/* Charts row */}
      <div className="charts-row">
        {bias_distribution && <BiasBreakdownChart distribution={bias_distribution} />}
        {word_cloud && word_cloud.length > 0 && <WordCloud words={word_cloud} />}
      </div>
    </div>
  );
}
