// src/services/optimizedAnalyticsService.js
import axios from 'axios';

// Create axios instance with base URL and auth headers
const analyticsApi = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  // Add timeout for queries that might take longer
  timeout: 60000, // 60 seconds timeout for large queries
});

// Add authorization token to each request
analyticsApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add request / response timing info
analyticsApi.interceptors.request.use(
  (config) => {
    config.metadata = { startTime: new Date() };
    return config;
  },
  (error) => Promise.reject(error)
);

analyticsApi.interceptors.response.use(
  (response) => {
    const endTime = new Date();
    const startTime = response.config.metadata.startTime;
    const elapsedTimeMs = endTime - startTime;
    
    // Add timing info if not already present
    if (response.data && !response.data.processing_info) {
      response.data.processing_info = {
        processing_time_ms: elapsedTimeMs,
        cached: false
      };
    }
    
    return response;
  },
  (error) => Promise.reject(error)
);

export const optimizedAnalyticsService = {
  // Get dashboard summary data
  getDashboardSummary: async () => {
    try {
      const response = await analyticsApi.get('/analytics/summary/');
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard summary:', error);
      throw error;
    }
  },

  // Get time series data with optimized interval parameter
  getSalesTimeSeries: async (interval = 'auto', days = 30) => {
    try {
      const response = await analyticsApi.get('/analytics/optimized-timeseries/', {
        params: { interval, days }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching sales time series:', error);
      throw error;
    }
  },

  // Get top performing books
  getTopBooks: async (limit = 10, days = 30) => {
    try {
      const response = await analyticsApi.get('/analytics/top-books/', {
        params: { limit, days }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching top books:', error);
      throw error;
    }
  },

  // Get sales by region
  getSalesByRegion: async (days = 30) => {
    try {
      const response = await analyticsApi.get('/analytics/sales-by-region/', {
        params: { days }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching sales by region:', error);
      throw error;
    }
  },

  // Get sales by genre
  getSalesByGenre: async (days = 30) => {
    try {
      const response = await analyticsApi.get('/analytics/sales-by-genre/', {
        params: { days }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching sales by genre:', error);
      throw error;
    }
  },

  // Generate test data
  generateTestData: async (numBooks = 500, numSales = 10000, skipRedshift = false) => {
    try {
      const response = await analyticsApi.post('/analytics/generate-test-data/', {
        num_books: numBooks,
        num_sales: numSales,
        skip_redshift: skipRedshift
      });
      return response.data;
    } catch (error) {
      console.error('Error generating test data:', error);
      throw error;
    }
  },
  
  // Check API performance (useful for testing)
  checkApiPerformance: async () => {
    try {
      const startTime = Date.now();
      
      // Test different time ranges
      const ranges = [30, 90, 365, 730];
      const results = {};
      
      for (const days of ranges) {
        const rangeStartTime = Date.now();
        const response = await analyticsApi.get('/analytics/timeseries/', {
          params: { interval: 'auto', days }
        });
        const rangeDuration = Date.now() - rangeStartTime;
        
        results[`${days} days`] = {
          duration_ms: rangeDuration,
          data_points: response.data.period?.length || 0,
          processing_info: response.data.processing_info
        };
      }
      
      // Calculate total duration
      const totalDuration = Date.now() - startTime;
      
      return {
        total_duration_ms: totalDuration,
        results
      };
    } catch (error) {
      console.error('Error checking API performance:', error);
      throw error;
    }
  }
};

export default optimizedAnalyticsService;