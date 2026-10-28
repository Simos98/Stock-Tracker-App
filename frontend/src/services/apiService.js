import axios from 'axios';

// Relative by default: Vite proxies /api in dev, and Flask serves the built app in prod.
// Set VITE_API_BASE_URL to point at a backend on another origin.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const withRefreshToken = () => ({
  headers: { Authorization: `Bearer ${localStorage.getItem('refreshToken')}` },
});

// Add request interceptor to include auth token in requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  // Requests that set their own token (refresh, logout) keep it
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// When the access token expires, trade the refresh token for a new one and retry once.
// Concurrent 401s share a single refresh request.
let refreshRequest = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const canRefresh =
      error.response?.status === 401 &&
      !original._retried &&
      !original.url.startsWith('/auth/') &&
      localStorage.getItem('refreshToken');
    if (!canRefresh) {
      return Promise.reject(error);
    }

    original._retried = true;
    try {
      refreshRequest ??= api.post('/auth/refresh', null, withRefreshToken()).finally(() => {
        refreshRequest = null;
      });
      const { data } = await refreshRequest;
      localStorage.setItem('token', data.access_token);
      original.headers.Authorization = `Bearer ${data.access_token}`;
      return api(original);
    } catch (refreshError) {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      return Promise.reject(refreshError);
    }
  },
);

// Authentication services
export const authService = {
  login: (credentials) => api.post('/auth/login', credentials),
  signup: (userData) => api.post('/auth/signup', userData),
  // Revoke both tokens server-side, then forget them locally even if that fails
  logout: async () => {
    const requests = [api.post('/auth/logout')];
    if (localStorage.getItem('refreshToken')) {
      requests.push(api.post('/auth/logout', null, withRefreshToken()));
    }
    await Promise.allSettled(requests);
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
  },
};

// User services
export const userService = {
  getMe: () => api.get('/users/me'),
  updateMe: (userData) => api.put('/users/me', userData),
};

// Stock services (market data comes from Alpha Vantage via the backend)
export const stockService = {
  // Search stocks with optional filters
  searchStocks: (params) => api.get('/stocks', { params }),

  // Get details for a specific stock symbol
  getStockDetails: (symbol) => api.get(`/stocks/${symbol}`),

  // Get historical data for a stock
  getHistoricalData: (symbol, params) => api.get(`/stocks/${symbol}/historical`, { params }),
};

// Watchlist services
export const watchlistService = {
  getWatchlist: () => api.get('/watchlist'),
  addToWatchlist: (stockData) => api.post('/watchlist', stockData),
  removeFromWatchlist: (stockSymbol) => api.delete(`/watchlist/${stockSymbol}`),
};

// Preferences services
export const preferencesService = {
  getPreferences: () => api.get('/preferences'),
  updatePreferences: (preferencesData) => api.put('/preferences', preferencesData),
};

// Report services
export const reportService = {
  buildReport: (reportParams) => api.post('/reports/build', reportParams),
};

export default api;
