import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { analyticsService } from "../services/analyticsService";
import PageHeader from "../components/PageHeader";
import TimeRangeSelector from "../components/TimeRangeSelector";
import StatCard from "../components/StatCard";
import DataCard from "../components/DataCard";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import {
  CurrencyDollarIcon,
  ShoppingBagIcon,
  DocumentIcon,
  BookOpenIcon,
} from "@heroicons/react/24/outline";

const Dashboard = () => {
  const [timeRange, setTimeRange] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [timeSeriesData, setTimeSeriesData] = useState([]);
  const [topBooks, setTopBooks] = useState([]);
  const [genreData, setGenreData] = useState([]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value) => {
    return new Intl.NumberFormat("en-US").format(value);
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch all data in parallel
        const results = await Promise.allSettled([
          analyticsService.getDashboardSummary(),
          analyticsService.getSalesTimeSeries("day", timeRange),
          analyticsService.getTopBooks(5, timeRange),
          analyticsService.getSalesByGenre(timeRange),
        ]);

        // Process results, handling any failed promises
        if (results[0].status === "fulfilled") {
          setSummary(results[0].value);
        }

        if (results[1].status === "fulfilled") {
          // Format time series data, handling possible missing properties
          const timeSeries = results[1].value;
          if (timeSeries && timeSeries.period) {
            const formattedTimeSeries = timeSeries.period.map(
              (date, index) => ({
                date,
                revenue: timeSeries.revenue?.[index] || 0,
                books: timeSeries.books_sold?.[index] || 0,
                sales: timeSeries.num_sales?.[index] || 0,
              })
            );
            setTimeSeriesData(formattedTimeSeries);
          } else {
            setTimeSeriesData([]);
          }
        }

        if (results[2].status === "fulfilled") {
          setTopBooks(results[2].value || []);
        }

        if (results[3].status === "fulfilled") {
          // Limit to top 5 genres, handling empty data
          setGenreData((results[3].value || []).slice(0, 5));
        }

        // Check if any requests failed
        const failedResults = results.filter((r) => r.status === "rejected");
        if (failedResults.length > 0) {
          console.error(
            "Some dashboard data failed to load:",
            failedResults.map((r) => r.reason)
          );
          setError(
            "Some dashboard data failed to load. You may see partial information."
          );
        } else {
          setError(null);
        }
      } catch (err) {
        console.error("Error fetching dashboard data:", err);
        setError("Failed to fetch dashboard data. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timeRange]);

  if (loading && !summary) {
    return (
      <div className="flex justify-center items-center h-96">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Set up colors for charts
  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#a05195"];

  return (
    <div>
      <PageHeader
        title="Book Sales Dashboard"
        description="Overview of your book sales performance"
      >
        <TimeRangeSelector selectedRange={timeRange} onChange={setTimeRange} />
      </PageHeader>

      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-50 flex justify-center items-center z-10">
          <LoadingSpinner />
        </div>
      )}

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatCard
          title="Total Revenue"
          value={formatCurrency(summary?.total_revenue || 0)}
          trend="up"
          trendValue="12%"
          icon={<CurrencyDollarIcon className="h-6 w-6" />}
        />
        <StatCard
          title="Books Sold"
          value={formatNumber(summary?.total_books_sold || 0)}
          trend="up"
          trendValue="8%"
          icon={<BookOpenIcon className="h-6 w-6" />}
        />
        <StatCard
          title="Total Sales"
          value={formatNumber(summary?.total_sales || 0)}
          trend="up"
          trendValue="5%"
          icon={<ShoppingBagIcon className="h-6 w-6" />}
        />
        <StatCard
          title="Unique Books Sold"
          value={formatNumber(summary?.unique_books_sold || 0)}
          trend="down"
          trendValue="3%"
          icon={<DocumentIcon className="h-6 w-6" />}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Revenue Over Time */}
        <DataCard title="Revenue Over Time">
          {timeSeriesData.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={timeSeriesData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(date) => {
                      try {
                        const d = new Date(date);
                        return `${d.getMonth() + 1}/${d.getDate()}`;
                      } catch (e) {
                        return date;
                      }
                    }}
                  />
                  <YAxis
                    tickFormatter={(value) => `${value.toLocaleString()}`}
                  />
                  <Tooltip
                    formatter={(value, name) => [
                      `${value.toLocaleString()}`,
                      "Revenue",
                    ]}
                    labelFormatter={(label) => {
                      try {
                        const d = new Date(label);
                        return d.toLocaleDateString();
                      } catch (e) {
                        return label;
                      }
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    name="Revenue"
                    stroke="#0ea5e9"
                    strokeWidth={2}
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState
              title="No revenue data available"
              message="Try adjusting the time range or check that your data is loaded correctly."
            />
          )}
        </DataCard>

        {/* Books Sold Over Time */}
        <DataCard title="Books Sold Over Time">
          {timeSeriesData.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={timeSeriesData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(date) => {
                      try {
                        const d = new Date(date);
                        return `${d.getMonth() + 1}/${d.getDate()}`;
                      } catch (e) {
                        return date;
                      }
                    }}
                  />
                  <YAxis />
                  <Tooltip
                    formatter={(value, name) => [
                      value.toLocaleString(),
                      name === "books" ? "Books Sold" : "Number of Sales",
                    ]}
                    labelFormatter={(label) => {
                      try {
                        const d = new Date(label);
                        return d.toLocaleDateString();
                      } catch (e) {
                        return label;
                      }
                    }}
                  />
                  <Legend />
                  <Bar dataKey="books" name="Books Sold" fill="#8b5cf6" />
                  <Bar dataKey="sales" name="Number of Sales" fill="#22c55e" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState
              title="No sales data available"
              message="Try adjusting the time range or check that your data is loaded correctly."
            />
          )}
        </DataCard>
      </div>

      {/* Additional Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Books */}
        <DataCard title="Top 5 Books by Revenue">
          {topBooks.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={topBooks}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    tickFormatter={(value) => `${value.toLocaleString()}`}
                  />
                  <YAxis
                    type="category"
                    dataKey="title"
                    width={150}
                    tickFormatter={(value) =>
                      value && value.length > 20
                        ? `${value.substring(0, 20)}...`
                        : value || ""
                    }
                  />
                  <Tooltip formatter={(value) => `${value.toLocaleString()}`} />
                  <Legend />
                  <Bar dataKey="total_revenue" name="Revenue" fill="#0ea5e9" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState
              title="No book data available"
              message="Try adjusting the time range or check that your data is loaded correctly."
            />
          )}
        </DataCard>

        {/* Sales by Genre */}
        <DataCard title="Top Genres by Revenue">
          {genreData.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={genreData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="revenue"
                    nameKey="genre"
                    label={({ name, percent }) =>
                      `${name || "Unknown"}: ${(percent * 100).toFixed(0)}%`
                    }
                  >
                    {genreData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `${value.toLocaleString()}`} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState
              title="No genre data available"
              message="Try adjusting the time range or check that your data is loaded correctly."
            />
          )}
        </DataCard>
      </div>
    </div>
  );
};

export default Dashboard;
