/**
 * src/api/client.js — Axios instances for both APIs.
 *
 * Usage:
 *   import { coreApi, reportsApi } from './api/client';
 *   const data = await coreApi.get('/assets');
 */

import axios from 'axios';

// Base URL is relative to use Vite's proxy during dev
const CORE_API_URL = import.meta.env.VITE_CORE_API_URL || '';

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
  baseURL: `${CORE_API_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});
coreApi.interceptors.request.use(authInterceptor);



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
