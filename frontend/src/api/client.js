import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = axios.create({ baseURL });

api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem('token');
  if (t) {
    cfg.headers.Authorization = `Bearer ${t}`;
  }
  return cfg;
});

export async function fetchMe() {
  const res = await api.get('/auth/me');
  return res.data;
}
