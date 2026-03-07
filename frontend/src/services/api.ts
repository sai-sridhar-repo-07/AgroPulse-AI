/**
 * AgroPulse AI - API Service Layer
 * Centralized Axios instance with JWT auth, retry logic, and error handling
 */
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';
import {
  CropRecommendationRequest,
  CropRecommendationResponse,
  YieldPredictionRequest,
  YieldPredictionResponse,
  PriceForecastRequest,
  PriceForecastResponse,
  AlertListResponse,
  ExplanationRequest,
  ExplanationResponse,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// ─── Axios Instance ─────────────────────────────────────────────────────────
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Request Interceptor (attach JWT) ────────────────────────────────────────
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor (handle 401) ──────────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', res.data.access_token);
          // Retry original request
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
            return apiClient(error.config);
          }
        } catch {
          // Refresh failed → logout
          localStorage.clear();
          window.location.href = '/login';
        }
      } else {
        localStorage.clear();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth API ─────────────────────────────────────────────────────────────────
export const authAPI = {
  login: async (username: string, password: string) => {
    const res = await apiClient.post('/auth/login', { username, password });
    return res.data;
  },
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('id_token');
    localStorage.removeItem('refresh_token');
  },
  getProfile: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
};

// ─── Predictions API ──────────────────────────────────────────────────────────
export const predictAPI = {
  cropRecommendation: async (
    data: CropRecommendationRequest
  ): Promise<CropRecommendationResponse> => {
    const res = await apiClient.post('/predict/crop', data);
    return res.data;
  },

  yieldPrediction: async (
    data: YieldPredictionRequest
  ): Promise<YieldPredictionResponse> => {
    const res = await apiClient.post('/predict/yield', data);
    return res.data;
  },

  priceForecast: async (
    data: PriceForecastRequest
  ): Promise<PriceForecastResponse> => {
    const res = await apiClient.post('/predict/price', data);
    return res.data;
  },
};

// ─── Alerts API ───────────────────────────────────────────────────────────────
export const alertsAPI = {
  getAlerts: async (farmerId: string, state: string = '', rainfallMm: number = 800): Promise<AlertListResponse> => {
    const res = await apiClient.get(`/alerts/${farmerId}`, {
      params: { state, rainfall_mm: rainfallMm },
    });
    return res.data;
  },
};

// ─── Explanation API (Bedrock GenAI) ─────────────────────────────────────────
export const explanationAPI = {
  generateExplanation: async (
    data: ExplanationRequest
  ): Promise<ExplanationResponse> => {
    const res = await apiClient.post('/generate-explanation', data);
    return res.data;
  },
};

// ─── Health API ───────────────────────────────────────────────────────────────
export const healthAPI = {
  check: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },
};

export default apiClient;
