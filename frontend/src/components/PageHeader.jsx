// src/components/PageHeader.jsx
import React from 'react';

const PageHeader = ({ title, description, children }) => {
  return (
    <div className="pb-5 border-b border-gray-200 sm:flex sm:items-center sm:justify-between mb-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        {description && <p className="mt-2 text-sm text-gray-500">{description}</p>}
      </div>
      <div className="mt-3 sm:mt-0 sm:ml-4">{children}</div>
    </div>
  );
};

export default PageHeader;