/**
 * src/api/client.js — Axios instances for both APIs.
 *
 * Usage:
 *   import { coreApi, reportsApi } from './api/client';
 *   const data = await coreApi.get('/assets');
 */

import axios from 'axios';

const CORE_API_URL = import.meta.env.VITE_CORE_API_URL || 'http://localhost:8000';
const REPORTS_API_URL = import.meta.env.VITE_REPORTS_API_URL || 'http://localhost:8001';

/** Attach Authorization header from localStorage on every request */
const authInterceptor = (config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

/** core-api (FastAPI) axios instance */
export const coreApi = axios.create({
  baseURL: `${CORE_API_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
});
coreApi.interceptors.request.use(authInterceptor);

/** reports-api (Flask) axios instance */
export const reportsApi = axios.create({
  baseURL: `${REPORTS_API_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
});
reportsApi.interceptors.request.use(authInterceptor);

/** Handle 401 globally — redirect to /login */
const unauthorizedInterceptor = (error) => {
  if (error.response?.status === 401) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  }
  return Promise.reject(error);
};

coreApi.interceptors.response.use(undefined, unauthorizedInterceptor);
reportsApi.interceptors.response.use(undefined, unauthorizedInterceptor);
