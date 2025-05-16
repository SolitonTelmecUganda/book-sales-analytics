// src/components/DataCard.jsx
import React from 'react';

const DataCard = ({ title, children, className = '' }) => {
  return (
    <div className={`bg-white rounded-lg shadow-sm p-6 ${className}`}>
      {title && <h3 className="text-lg font-medium text-gray-700 mb-4">{title}</h3>}
      {children}
    </div>
  );
};

export default DataCard;