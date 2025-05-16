// src/components/StatCard.jsx
import React from 'react';

const StatCard = ({ title, value, trend, trendValue, icon }) => {
  const isPositive = trend === 'up';
  const trendColor = isPositive ? 'text-success-600' : 'text-rose-600';
  const bgColor = isPositive ? 'bg-success-100' : 'bg-rose-100';
  
  return (
    <div className="bg-white rounded-lg shadow-sm p-6 flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-600">{title}</h3>
        {icon && <div className="text-primary-500">{icon}</div>}
      </div>
      <div className="text-3xl font-bold text-gray-900 mb-2">{value}</div>
      {trendValue && (
        <div className="flex items-center">
          <span className={`${trendColor} flex items-center`}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-5 w-5 mr-1" 
              viewBox="0 0 20 20" 
              fill="currentColor"
            >
              {isPositive ? (
                <path 
                  fillRule="evenodd" 
                  d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" 
                  clipRule="evenodd" 
                />
              ) : (
                <path 
                  fillRule="evenodd" 
                  d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" 
                  clipRule="evenodd" 
                />
              )}
            </svg>
            {trendValue}
          </span>
          <span className="text-gray-500 ml-2 text-sm">vs last period</span>
        </div>
      )}
    </div>
  );
}

export default StatCard;