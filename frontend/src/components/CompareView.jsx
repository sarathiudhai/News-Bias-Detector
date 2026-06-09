import React, { useState } from 'react';
import { compareArticles } from '../api';
import ScoreSummary from './ScoreSummary';
import ArticleReader from './ArticleReader';

export default function CompareView() {
  const [mode1, setMode1] = useState('text');
  const [mode2, setMode2] = useState('text');
  const [input1, setInput1] = useState('');
  const [input2, setInput2] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCompare = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const a1 = mode1 === 'url' ? { url: input1 } : { text: input1 };
      const a2 = mode2 === 'url' ? { url: input2 } : { text: input2 };
      const data = await compareArticles({ article1: a1, article2: a2 });
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Comparison failed. Please try again.');
    } finally { setLoading(false); }
  };

  const renderInput = (mode, setMode, input, setInput, label) => (
    <div className="glass-card" style={{ flex: 1 }}>
      <h3 style={{ marginBottom: '0.75rem', fontSize: '0.95rem', fontWeight: 600 }}>{label}</h3>
      <div className="input-toggle">
        <button className={`toggle-btn ${mode === 'text' ? 'active' : ''}`} onClick={() => setMode('text')}>Paste Text</button>
        <button className={`toggle-btn ${mode === 'url' ? 'active' : ''}`} onClick={() => setMode('url')}>Enter URL</button>
      </div>
      {mode === 'url'
        ? <input className="input-field" placeholder="https://example.com/article" value={input} onChange={e => setInput(e.target.value)} />
        : <textarea className="input-textarea" placeholder="Paste article text here..." value={input} onChange={e => setInput(e.target.value)} style={{ minHeight: '120px' }} />
      }
    </div>
  );

  return (
    <div className="fade-in">
      <div className="compare-grid" style={{ marginBottom: '1rem' }}>
        {renderInput(mode1, setMode1, input1, setInput1, 'Article 1')}
        {renderInput(mode2, setMode2, input2, setInput2, 'Article 2')}
      </div>
      <button className="submit-btn" onClick={handleCompare} disabled={loading || (!input1 || !input2)}
        style={{ width: '100%' }}>
        {loading ? 'Comparing...' : '⚡ Compare Articles'}
      </button>
      {error && <div className="error-box" style={{ marginTop: '1rem' }}>{error}</div>}
      {loading && <div className="loading-overlay"><div className="spinner" /><div className="loading-text">Running NLP analysis on both articles...</div></div>}
      {result && (
        <div className="fade-in" style={{ marginTop: '2rem' }}>
          <div className="compare-bar glass-card">
            <div style={{ textAlign: 'center' }}>
              <h4 style={{ marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Article 1</h4>
              <div className="compare-scores">
                <div className="mini-score"><div className="value" style={{ color: 'var(--accent-blue)' }}>{result.article1.overall_bias.score}</div><div className="label">Bias</div></div>
                <div className="mini-score"><div className="value" style={{ color: 'var(--accent-amber)' }}>{result.article1.overall_emotion.score}</div><div className="label">Emotion</div></div>
                <div className="mini-score"><div className="value" style={{ color: 'var(--accent-emerald)' }}>{result.article1.overall_factual_density.score}</div><div className="label">Factual</div></div>
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <h4 style={{ marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Article 2</h4>
              <div className="compare-scores">
                <div className="mini-score"><div className="value" style={{ color: 'var(--accent-blue)' }}>{result.article2.overall_bias.score}</div><div className="label">Bias</div></div>
                <div className="mini-score"><div className="value" style={{ color: 'var(--accent-amber)' }}>{result.article2.overall_emotion.score}</div><div className="label">Emotion</div></div>
                <div className="mini-score"><div className="value" style={{ color: 'var(--accent-emerald)' }}>{result.article2.overall_factual_density.score}</div><div className="label">Factual</div></div>
              </div>
            </div>
          </div>
          <div className="compare-grid">
            <ArticleReader data={result.article1} />
            <ArticleReader data={result.article2} />
          </div>
        </div>
      )}
    </div>
  );
}
