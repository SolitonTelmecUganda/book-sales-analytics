// src/pages/Settings.jsx
import React, { useState } from 'react';
import { analyticsService } from '../services/analyticsService';
import PageHeader from '../components/PageHeader';
import DataCard from '../components/DataCard';
import LoadingSpinner from '../components/LoadingSpinner';

const Settings = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [formState, setFormState] = useState({
    numBooks: 500,
    numSales: 10000,
    skipRedshift: false
  });

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormState(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : Number(value)
    }));
  };

  const handleGenerateData = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const data = await analyticsService.generateTestData(
        formState.numBooks,
        formState.numSales,
        formState.skipRedshift
      );
      setResult(data);
    } catch (err) {
      console.error('Error generating test data:', err);
      setError('Failed to generate test data. Please check your configuration and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader 
        title="Settings" 
        description="Configure your dashboard and generate test data"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DataCard title="Generate Test Data">
          <form onSubmit={handleGenerateData}>
            <div className="space-y-4">
              <div>
                <label htmlFor="numBooks" className="block text-sm font-medium text-gray-700">
                  Number of Books
                </label>
                <input
                  type="number"
                  name="numBooks"
                  id="numBooks"
                  className="input mt-1 block w-full"
                  min="10"
                  max="10000"
                  value={formState.numBooks}
                  onChange={handleInputChange}
                />
                <p className="mt-1 text-sm text-gray-500">
                  Number of unique books to generate (10-10,000)
                </p>
              </div>

              <div>
                <label htmlFor="numSales" className="block text-sm font-medium text-gray-700">
                  Number of Sales
                </label>
                <input
                  type="number"
                  name="numSales"
                  id="numSales"
                  className="input mt-1 block w-full"
                  min="100"
                  max="100000"
                  value={formState.numSales}
                  onChange={handleInputChange}
                />
                <p className="mt-1 text-sm text-gray-500">
                  Number of sales transactions to generate (100-100,000)
                </p>
              </div>

              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    id="skipRedshift"
                    name="skipRedshift"
                    type="checkbox"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    checked={formState.skipRedshift}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="skipRedshift" className="font-medium text-gray-700">
                    Skip Redshift Loading
                  </label>
                  <p className="text-gray-500">
                    Generate and upload data to S3, but skip loading to Redshift
                  </p>
                </div>
              </div>

              <div className="pt-4">
                <button
                  type="submit"
                  className="btn btn-primary inline-flex items-center"
                  disabled={loading}
                >
                  {loading && (
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  )}
                  Generate Test Data
                </button>
              </div>
            </div>
          </form>

          {loading && (
            <div className="mt-6 p-4 bg-gray-50 rounded-md">
              <LoadingSpinner size="md" />
              <p className="text-center mt-2 text-sm text-gray-600">
                Generating test data... This may take a moment.
              </p>
            </div>
          )}

          {error && (
            <div className="mt-6 bg-red-50 border-l-4 border-red-400 p-4">
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

          {result && (
            <div className="mt-6 p-4 bg-green-50 border-l-4 border-green-400 rounded-md">
              <h3 className="text-lg font-medium text-green-800">Data Generation Successful!</h3>
              <div className="mt-2 text-sm text-green-700">
                <p>
                  <span className="font-medium">Generated: </span>
                  {result.generated.books.toLocaleString()} books and {result.generated.sales.toLocaleString()} sales
                </p>
                <p className="mt-1">
                  <span className="font-medium">Data stored in S3: </span>
                  <code className="bg-green-100 px-1 py-0.5 rounded">
                    s3://{result.s3.books_key.split('/')[0]}/{result.s3.books_key}
                  </code>
                </p>
                
                {result.redshift && (
                  <div className="mt-2">
                    <p className="font-medium">Redshift Import:</p>
                    {result.redshift.success ? (
                      <p className="text-green-700">
                        Successfully loaded {result.redshift.book_count} books and {result.redshift.sales_count} sales records.
                      </p>
                    ) : (
                      <p className="text-red-700">
                        Redshift import failed: {result.redshift.error}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </DataCard>

        <DataCard title="Dashboard Configuration">
          <div className="space-y-4">
            <p className="text-sm text-gray-500">
              Additional dashboard configuration options will be available in future updates.
            </p>
            
            <div>
              <h3 className="text-lg font-medium text-gray-700 mb-2">About this Dashboard</h3>
              <p className="text-sm text-gray-600">
                This dashboard provides analytics for book sales data using:
              </p>
              <ul className="mt-2 list-disc list-inside text-sm text-gray-600 space-y-1">
                <li>Django backend with Django Rest Framework (DRF) API</li>
                <li>AWS S3 for data storage</li>
                <li>AWS Redshift for data warehousing</li>
                <li>React.js frontend with Tailwind CSS</li>
                <li>Recharts for data visualization</li>
              </ul>
            </div>
            
            <div className="mt-4">
              <h3 className="text-lg font-medium text-gray-700 mb-2">Redshift Connection</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-600">Status</p>
                  <div className="flex items-center mt-1">
                    <span className="h-2.5 w-2.5 rounded-full bg-green-500 mr-1.5"></span>
                    <span className="text-sm text-gray-700">Connected</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Database</p>
                  <p className="text-sm text-gray-700 mt-1">analytics</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Host</p>
                  <p className="text-sm text-gray-700 mt-1">booksales-analytics.xxxx.region.redshift.amazonaws.com</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Port</p>
                  <p className="text-sm text-gray-700 mt-1">5439</p>
                </div>
              </div>
            </div>
          </div>
        </DataCard>
      </div>
    </div>
  );
};

export default Settings;