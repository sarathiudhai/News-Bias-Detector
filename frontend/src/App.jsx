import React, { useState } from 'react';
import './index.css';
import { analyzeArticle } from './api';
import ScoreSummary from './components/ScoreSummary';
import ArticleReader from './components/ArticleReader';
import CompareView from './components/CompareView';
import HistoryTable from './components/HistoryTable';
import ExportButton from './components/ExportButton';

function App() {
  const [tab, setTab] = useState('analyze');
  const [mode, setMode] = useState('text');
  const [input, setInput] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [theme, setTheme] = useState('dark');

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    document.documentElement.classList.toggle('light-theme', next === 'light');
  };

  const handleAnalyze = async () => {
    if (!input.trim()) return;
    setLoading(true); setError(''); setResult(null);
    try {
      const payload = mode === 'url' ? { url: input } : { text: input };
      const data = await analyzeArticle(payload);
      setResult(data);
    } catch (e) {
      const detail = e.response?.data?.detail || 'Analysis failed.';
      setError(detail + (mode === 'url' ? ' Try pasting the article text directly instead.' : ''));
    } finally { setLoading(false); }
  };

  const handleLoadFromHistory = (data) => {
    setResult(data); setTab('analyze');
  };

  return (
    <>
      <header className="app-header">
        <div className="app-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="url(#grad)" strokeWidth="2" strokeLinecap="round">
            <defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#3b82f6"/><stop offset="100%" stopColor="#8b5cf6"/></linearGradient></defs>
            <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
          </svg>
          Bias Detector
        </div>
        <div className="header-actions">
          <div className="tab-bar">
            {['analyze', 'compare', 'history'].map(t => (
              <button key={t} className={`tab-btn ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
                {t === 'analyze' ? '🔍 Analyze' : t === 'compare' ? '⚖️ Compare' : '📋 History'}
              </button>
            ))}
          </div>
          <button className="theme-toggle" onClick={toggleTheme} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      <main className="main-content" id="analysis-report">
        {tab === 'analyze' && (
          <div className="fade-in">
            <div className="input-section glass-card">
              <div className="input-header">
                <div className="input-toggle">
                  <button className={`toggle-btn ${mode === 'text' ? 'active' : ''}`} onClick={() => setMode('text')}>📝 Paste Text</button>
                  <button className={`toggle-btn ${mode === 'url' ? 'active' : ''}`} onClick={() => setMode('url')}>🔗 Enter URL</button>
                </div>
                {result && <ExportButton />}
              </div>
              {mode === 'url'
                ? <input className="input-field" placeholder="https://www.example.com/news-article" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleAnalyze()} />
                : <textarea className="input-textarea" placeholder="Paste the full article text here for analysis..." value={input} onChange={e => setInput(e.target.value)} />
              }
              <button className="submit-btn" onClick={handleAnalyze} disabled={loading || !input.trim()}>
                {loading ? '⏳ Analyzing...' : '⚡ Analyze Article'}
              </button>
            </div>

            {error && <div className="error-box" style={{ marginBottom: '1.5rem' }}>{error}</div>}
            {loading && <div className="loading-overlay"><div className="spinner" /><div className="loading-text">Running bias, emotion &amp; factual analysis...</div></div>}
            {result && (
              <>
                <ScoreSummary data={result} />
                <ArticleReader data={result} />
              </>
            )}
          </div>
        )}
        {tab === 'compare' && <CompareView />}
        {tab === 'history' && <HistoryTable onLoadAnalysis={handleLoadFromHistory} />}
      </main>
    </>
  );
}

export default App;
