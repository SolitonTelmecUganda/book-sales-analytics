// src/pages/SalesByGenre.jsx
import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, PieChart, Pie, Cell, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { analyticsService } from '../services/analyticsService';
import PageHeader from '../components/PageHeader';
import TimeRangeSelector from '../components/TimeRangeSelector';
import DataCard from '../components/DataCard';
import LoadingSpinner from '../components/LoadingSpinner';

const SalesByGenre = () => {
  const [timeRange, setTimeRange] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [genreData, setGenreData] = useState([]);
  
  // Set up colors for charts
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c'];
  
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const data = await analyticsService.getSalesByGenre(timeRange);
        setGenreData(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching genre data:', err);
        setError('Failed to fetch sales by genre data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timeRange]);

  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index }) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div>
      <PageHeader 
        title="Sales by Genre" 
        description="Analysis of book sales performance by genre category"
      >
        <TimeRangeSelector 
          selectedRange={timeRange} 
          onChange={setTimeRange} 
        />
      </PageHeader>

      {loading && (
        <div className="flex justify-center items-center h-48">
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Pie Chart */}
        <DataCard title="Revenue Distribution by Genre">
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={genreData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomizedLabel}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="revenue"
                  nameKey="genre"
                >
                  {genreData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value, name, props) => [formatCurrency(value), 'Revenue']}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </DataCard>

        {/* Bar Chart */}
        <DataCard title="Books Sold by Genre">
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={genreData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis 
                  type="category" 
                  dataKey="genre" 
                  width={90} 
                  tick={{fontSize: 12}}
                  tickFormatter={(value) => value.length > 15 ? `${value.substring(0, 15)}...` : value}
                />
                <Tooltip formatter={(value) => value.toLocaleString()} />
                <Legend />
                <Bar dataKey="books_sold" name="Books Sold" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </DataCard>
      </div>

      {/* Detailed Table */}
      <DataCard title="Genre Sales Details">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Genre</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Number of Sales</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Books Sold</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Revenue</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Avg. Revenue per Book</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {!loading && genreData.map((genre, index) => (
                <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{genre.genre}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">{genre.num_sales?.toLocaleString() || '0'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">{genre.books_sold?.toLocaleString() || '0'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right font-medium">{formatCurrency(genre.revenue)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                    {formatCurrency(genre.books_sold > 0 ? genre.revenue / genre.books_sold : 0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataCard>
    </div>
  );
};

export default SalesByGenre;