// src/components/OptimizedTimeRangeSelector.jsx
import React from "react";

const OptimizedTimeRangeSelector = ({
  selectedRange,
  onChange,
  intervalMode = "auto", // 'auto', 'day', 'week', 'month', 'quarter', 'year'
  onIntervalModeChange,
}) => {
  const ranges = [
    { value: 7, label: "Last 7 days" },
    { value: 30, label: "Last 30 days" },
    { value: 90, label: "Last 3 months" },
    { value: 180, label: "Last 6 months" },
    { value: 365, label: "Last year" },
    { value: 730, label: "Last 2 years" },
  ];

  const intervals = [
    { value: "auto", label: "Auto" },
    { value: "day", label: "Daily" },
    { value: "week", label: "Weekly" },
    { value: "month", label: "Monthly" },
    { value: "quarter", label: "Quarterly" },
    { value: "year", label: "Yearly" },
  ];

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-500">Time range:</span>
        <select
          value={selectedRange}
          onChange={(e) => onChange(Number(e.target.value))}
          className="select text-sm"
        >
          {ranges.map((range) => (
            <option key={range.value} value={range.value}>
              {range.label}
            </option>
          ))}
        </select>
      </div>

      {onIntervalModeChange && (
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">Interval:</span>
          <select
            value={intervalMode}
            onChange={(e) => onIntervalModeChange(e.target.value)}
            className="select text-sm"
          >
            {intervals.map((interval) => (
              <option key={interval.value} value={interval.value}>
                {interval.label}
              </option>
            ))}
          </select>

          {intervalMode !== "auto" && selectedRange > 365 && (
            <span className="text-xs text-amber-600 font-medium">
              Note: Fine-grained intervals for large date ranges may affect
              performance
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default OptimizedTimeRangeSelector;
