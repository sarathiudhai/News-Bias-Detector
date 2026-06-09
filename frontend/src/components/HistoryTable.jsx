import React, { useEffect, useState } from 'react';
import { getHistory, getAnalysis, deleteAnalysis } from '../api';

export default function HistoryTable({ onLoadAnalysis }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(null);

  useEffect(() => {
    setLoading(true);
    getHistory()
      .then(data => { setHistory(data); setError(''); })
      .catch(() => setError('Failed to load history.'))
      .finally(() => setLoading(false));
  }, []);

  const handleClick = async (id) => {
    if (deleting) return; // Don't load while deleting
    try {
      const data = await getAnalysis(id);
      onLoadAnalysis(data);
    } catch {
      setError('Failed to load analysis.');
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation(); // Prevent row click from firing
    if (!window.confirm('Delete this analysis? This cannot be undone.')) return;

    setDeleting(id);
    try {
      await deleteAnalysis(id);
      setHistory(prev => prev.filter(h => h.id !== id));
      setError('');
    } catch {
      setError('Failed to delete analysis.');
    } finally {
      setDeleting(null);
    }
  };

  if (loading) return <div className="loading-overlay"><div className="spinner" /><div className="loading-text">Loading history...</div></div>;
  if (error && history.length === 0) return <div className="error-box">{error}</div>;
  if (history.length === 0) return (
    <div className="empty-state fade-in">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      <p>No analyses yet. Run your first analysis to see it here.</p>
    </div>
  );

  return (
    <div className="glass-card fade-in" style={{ overflowX: 'auto' }}>
      {error && <div className="error-box" style={{ marginBottom: '1rem' }}>{error}</div>}
      <table className="history-table">
        <thead>
          <tr>
            <th>Title</th><th>Date</th><th>Bias</th><th>Emotion</th><th>Factual</th><th style={{ width: 60 }}></th>
          </tr>
        </thead>
        <tbody>
          {history.map(h => (
            <tr key={h.id} onClick={() => handleClick(h.id)} className={deleting === h.id ? 'deleting' : ''}>
              <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {h.title || 'Untitled'}
              </td>
              <td style={{ whiteSpace: 'nowrap', color: 'var(--text-muted)' }}>
                {h.created_at ? new Date(h.created_at).toLocaleDateString() : '—'}
              </td>
              <td>
                <span className={`badge badge-${(h.bias_label || 'center').toLowerCase()}`}>
                  {h.bias_label || '—'} {h.bias_score ?? ''}
                </span>
              </td>
              <td><span style={{ color: 'var(--accent-amber)' }}>{h.emotion_score ?? '—'}</span></td>
              <td><span style={{ color: 'var(--accent-emerald)' }}>{h.factual_score ?? '—'}</span></td>
              <td>
                <button
                  className="delete-btn"
                  onClick={(e) => handleDelete(e, h.id)}
                  disabled={deleting === h.id}
                  title="Delete this analysis"
                >
                  {deleting === h.id ? (
                    <svg className="delete-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
                      <path d="M10 11v6" />
                      <path d="M14 11v6" />
                      <path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2" />
                    </svg>
                  )}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
