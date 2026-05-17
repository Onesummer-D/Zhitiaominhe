import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器（如需添加token等）
api.interceptors.request.use(
  (config) => {
    // 可在此添加认证信息
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API 方法封装
export const analyzeDispute = (data) => api.post('/api/analyze', data);
export const getCases = (params) => api.get('/api/cases', { params });
export const createCase = (data) => api.post('/api/cases', data);
export const getCaseDetail = (id) => api.get(`/api/cases/${id}`);
export const deleteCase = (id) => api.delete(`/api/cases/${id}`);
export const getKnowledge = (params) => api.get('/api/knowledge', { params });
export const getStats = () => api.get('/api/stats');

export default api;
