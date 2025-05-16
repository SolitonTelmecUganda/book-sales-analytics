// src/components/TimeRangeSelector.jsx

const TimeRangeSelector = ({ selectedRange, onChange }) => {
  const ranges = [
    { value: 7, label: 'Last 7 days' },
    { value: 30, label: 'Last 30 days' },
    { value: 90, label: 'Last 3 months' },
    { value: 365, label: 'Last year' }
  ];

  return (
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
  );
};

export default TimeRangeSelector;