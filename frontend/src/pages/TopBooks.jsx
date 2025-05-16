// src/pages/TopBooks.jsx
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { analyticsService } from '../services/analyticsService';
import PageHeader from '../components/PageHeader';
import TimeRangeSelector from '../components/TimeRangeSelector';
import DataCard from '../components/DataCard';
import LoadingSpinner from '../components/LoadingSpinner';

const TopBooks = () => {
  const [timeRange, setTimeRange] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [books, setBooks] = useState([]);
  const [limit, setLimit] = useState(10);

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
        const data = await analyticsService.getTopBooks(limit, timeRange);
        setBooks(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching top books:', err);
        setError('Failed to fetch top books data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timeRange, limit]);

  return (
    <div>
      <PageHeader 
        title="Top Books" 
        description={`Top ${limit} books by revenue over the selected time period`}
      >
        <div className="flex space-x-4">
          <TimeRangeSelector 
            selectedRange={timeRange} 
            onChange={setTimeRange} 
          />
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="select text-sm"
          >
            <option value={5}>Top 5</option>
            <option value={10}>Top 10</option>
            <option value={20}>Top 20</option>
            <option value={50}>Top 50</option>
          </select>
        </div>
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
        {/* Revenue Chart */}
        <DataCard title="Top Books by Revenue">
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={books}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(value) => `$${value.toLocaleString()}`} />
                <YAxis 
                  type="category" 
                  dataKey="title" 
                  width={140}
                  tickFormatter={(value) => value.length > 25 ? `${value.substring(0, 25)}...` : value}
                />
                <Tooltip 
                  formatter={(value, name) => {
                    if (name === 'total_revenue') return [`$${value.toLocaleString()}`, 'Revenue'];
                    return [value.toLocaleString(), name];
                  }}
                />
                <Legend />
                <Bar dataKey="total_revenue" name="Revenue" fill="#0ea5e9" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </DataCard>

        {/* Quantity Chart */}
        <DataCard title="Top Books by Quantity Sold">
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={books}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis 
                  type="category" 
                  dataKey="title" 
                  width={140}
                  tickFormatter={(value) => value.length > 25 ? `${value.substring(0, 25)}...` : value}
                />
                <Tooltip />
                <Legend />
                <Bar dataKey="total_quantity" name="Quantity Sold" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </DataCard>
      </div>

      {/* Detailed Table */}
      <DataCard title="Top Books Details">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Author</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Genre</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity Sold</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Revenue</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {!loading && books.map((book, index) => (
                <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{book.title}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{book.author}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{book.genre}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">{book.total_quantity.toLocaleString()}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right font-medium">{formatCurrency(book.total_revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataCard>
    </div>
  );
};

export default TopBooks;