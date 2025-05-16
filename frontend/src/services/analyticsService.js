// src/services/analyticsService.js
import axios from "axios";

// Create axios instance with base URL and auth headers
const analyticsApi = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Add authorization token to each request
analyticsApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("authToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const analyticsService = {
  // Get dashboard summary data
  getDashboardSummary: async () => {
    try {
      const response = await analyticsApi.get("/analytics/summary/");
      return response.data;
    } catch (error) {
      console.error("Error fetching dashboard summary:", error);
      throw error;
    }
  },

  // Get time series data for sales trends
  getSalesTimeSeries: async (interval = "day", days = 30) => {
    try {
      const response = await analyticsApi.get("/analytics/timeseries/", {
        params: { interval, days },
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching sales time series:", error);
      throw error;
    }
  },

  // Get top performing books
  getTopBooks: async (limit = 10, days = 30) => {
    try {
      const response = await analyticsApi.get("/analytics/top-books/", {
        params: { limit, days },
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching top books:", error);
      throw error;
    }
  },

  // Get sales by region
  getSalesByRegion: async (days = 30) => {
    try {
      const response = await analyticsApi.get("/analytics/sales-by-region/", {
        params: { days },
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching sales by region:", error);
      throw error;
    }
  },

  // Get sales by genre
  getSalesByGenre: async (days = 30) => {
    try {
      const response = await analyticsApi.get("/analytics/sales-by-genre/", {
        params: { days },
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching sales by genre:", error);
      throw error;
    }
  },

  // Generate test data
  generateTestData: async (
    numBooks = 500,
    numSales = 10000,
    skipRedshift = false
  ) => {
    try {
      const response = await analyticsApi.post(
        "/analytics/generate-test-data/",
        {
          num_books: numBooks,
          num_sales: numSales,
          skip_redshift: skipRedshift,
        }
      );
      return response.data;
    } catch (error) {
      console.error("Error generating test data:", error);
      throw error;
    }
  },
};

export default analyticsService;
