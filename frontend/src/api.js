import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
});

export const analyzeArticle = (data) => api.post('/analyze', data).then(r => r.data);
export const compareArticles = (data) => api.post('/compare', data).then(r => r.data);
export const getHistory = () => api.get('/history').then(r => r.data);
export const getAnalysis = (id) => api.get(`/history/${id}`).then(r => r.data);
export const deleteAnalysis = (id) => api.delete(`/history/${id}`).then(r => r.data);
export default api;
