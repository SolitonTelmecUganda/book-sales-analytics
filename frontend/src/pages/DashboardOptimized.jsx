// Updated Dashboard component with optimized time series handling
import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import optimizedAnalyticsService  from '../services/optimizedAnalyticsService';
import PageHeader from '../components/PageHeader';
import OptimizedTimeRangeSelector from '../components/OptimizedTimeRangeSelector';
import StatCard from '../components/StatCard';
import DataCard from '../components/DataCard';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { 
  CurrencyDollarIcon, 
  ShoppingBagIcon, 
  DocumentIcon, 
  BookOpenIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const Dashboard = () => {
  const [timeRange, setTimeRange] = useState(30);
  const [intervalMode, setIntervalMode] = useState('auto');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [timeSeriesData, setTimeSeriesData] = useState([]);
  const [topBooks, setTopBooks] = useState([]);
  const [genreData, setGenreData] = useState([]);
  const [processingInfo, setProcessingInfo] = useState(null);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Start with summary data which should be fast
        const summaryData = await optimizedAnalyticsService.getDashboardSummary();
        setSummary(summaryData);
        
        // Fetch time series data with interval parameter
        const timeSeries = await optimizedAnalyticsService.getSalesTimeSeries(intervalMode, timeRange);
        
        // Extract processing info if available
        if (timeSeries.processing_info) {
          setProcessingInfo(timeSeries.processing_info);
          delete timeSeries.processing_info;
        }
        
        // Format time series data
        if (timeSeries && timeSeries.period) {
          const formattedTimeSeries = timeSeries.period.map((date, index) => ({
            date,
            revenue: timeSeries.revenue?.[index] || 0,
            books: timeSeries.books_sold?.[index] || 0,
            sales: timeSeries.num_sales?.[index] || 0
          }));
          setTimeSeriesData(formattedTimeSeries);
        } else {
          setTimeSeriesData([]);
        }
        
        // Fetch remaining data with lower priority (parallel)
        Promise.allSettled([
          optimizedAnalyticsService.getTopBooks(5, timeRange),
          optimizedAnalyticsService.getSalesByGenre(timeRange)
        ]).then(results => {
          if (results[0].status === 'fulfilled') {
            setTopBooks(results[0].value || []);
          }
          
          if (results[1].status === 'fulfilled') {
            setGenreData((results[1].value || []).slice(0, 5));
          }
        });
        
        setError(null);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to fetch dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timeRange, intervalMode]);

  // Set up colors for charts
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#a05195'];

  // Helper function to format date for tooltip
  const formatTooltipDate = (date) => {
    try {
      // Handle different date formats from backend
      if (date.includes('-Q')) {
        // For quarterly data: "2023-Q1"
        return `Q${date.split('-Q')[1]} ${date.split('-Q')[0]}`;
      } else if (date.length === 7) {
        // For monthly data: "2023-05"
        const [year, month] = date.split('-');
        return new Date(year, month - 1).toLocaleDateString(undefined, { year: 'numeric', month: 'long' });
      } else if (date.length === 4) {
        // For yearly data: "2023"
        return date;
      } else {
        // For daily data: "2023-05-21"
        return new Date(date).toLocaleDateString();
      }
    } catch (e) {
      return date;
    }
  };

  // Helper function to format X-axis ticks
  const formatXAxisTick = (date) => {
    try {
      // Handle different date formats from backend
      if (date.includes('-Q')) {
        // For quarterly data: "2023-Q1"
        return `Q${date.split('-Q')[1]}`;
      } else if (date.length === 7) {
        // For monthly data: "2023-05"
        const [year, month] = date.split('-');
        return new Date(year, month - 1).toLocaleDateString(undefined, { month: 'short' });
      } else if (date.length === 4) {
        // For yearly data: "2023"
        return date;
      } else {
        // For daily data: "2023-05-21"
        const d = new Date(date);
        return `${d.getMonth()+1}/${d.getDate()}`;
      }
    } catch (e) {
      return date;
    }
  };

  return (
    <div>
      <PageHeader 
        title="Book Sales Dashboard" 
        description="Overview of your book sales performance"
      >
        <OptimizedTimeRangeSelector 
          selectedRange={timeRange} 
          onChange={setTimeRange}
          intervalMode={intervalMode}
          onIntervalModeChange={setIntervalMode}
        />
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
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Processing Info */}
      {processingInfo && (
        <div className="mb-6 flex justify-end">
          <div className="text-xs flex items-center text-gray-500">
            <ClockIcon className="h-4 w-4 mr-1" />
            {processingInfo.cached ? (
              <span>Loaded from cache in {processingInfo.processing_time_ms}ms</span>
            ) : (
              <span>
                Query processed in {processingInfo.processing_time_ms}ms 
                {processingInfo.interval_used && ` (${processingInfo.interval_used} intervals)`} 
                {processingInfo.data_points && ` • ${processingInfo.data_points} data points`}
              </span>
            )}
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
                    tickFormatter={formatXAxisTick}
                    // For large datasets, limit the number of ticks
                    interval={timeSeriesData.length > 60 ? Math.ceil(timeSeriesData.length / 12) : 0}
                  />
                  <YAxis 
                    tickFormatter={(value) => `$${value.toLocaleString()}`}
                  />
                  <Tooltip
                    formatter={(value, name) => [
                      `$${value.toLocaleString()}`,
                      'Revenue'
                    ]}
                    labelFormatter={formatTooltipDate}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    name="Revenue"
                    stroke="#0ea5e9"
                    strokeWidth={2}
                    dot={timeSeriesData.length < 60} // Only show dots for smaller datasets
                    activeDot={{ r: 8 }}
                  />
                  {/* Add reference line for average */}
                  {timeSeriesData.length > 0 && (
                    <ReferenceLine 
                      y={timeSeriesData.reduce((sum, item) => sum + item.revenue, 0) / timeSeriesData.length} 
                      stroke="#0ea5e9" 
                      strokeDasharray="3 3"
                      label={{
                        value: "Avg",
                        fill: "#0ea5e9",
                        fontSize: 12
                      }}
                    />
                  )}
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
                    tickFormatter={formatXAxisTick}
                    // For large datasets, limit the number of ticks
                    interval={timeSeriesData.length > 60 ? Math.ceil(timeSeriesData.length / 12) : 0}
                  />
                  <YAxis />
                  <Tooltip
                    formatter={(value, name) => [
                      value.toLocaleString(),
                      name === 'books' ? 'Books Sold' : 'Number of Sales'
                    ]}
                    labelFormatter={formatTooltipDate}
                  />
                  <Legend />
                  <Bar 
                    dataKey="books" 
                    name="Books Sold" 
                    fill="#8b5cf6" 
                  />
                  <Bar 
                    dataKey="sales" 
                    name="Number of Sales" 
                    fill="#22c55e" 
                  />
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
                  <XAxis type="number" tickFormatter={(value) => `$${value.toLocaleString()}`} />
                  <YAxis 
                    type="category" 
                    dataKey="title" 
                    width={150}
                    tickFormatter={(value) => value && value.length > 20 ? `${value.substring(0, 20)}...` : value || ''}
                  />
                  <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
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
                    label={({ name, percent }) => `${name || 'Unknown'}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {genreData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
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
      
      {/* Performance Tips */}
      {timeRange > 180 && (
        <div className="mt-6 bg-blue-50 border-l-4 border-blue-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                <span className="font-medium">Performance Tip:</span> When viewing data for large time periods, using Auto or Monthly/Quarterly intervals 
                provides the best performance. Processing time: {processingInfo?.processing_time_ms ? `${processingInfo.processing_time_ms}ms` : 'N/A'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;