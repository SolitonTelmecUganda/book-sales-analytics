# Book Sales Analytics Dashboard Frontend

This is the frontend for the Book Sales Analytics Dashboard research project. It provides an interactive user interface for visualizing and analyzing book sales data from our data warehouse.

## Technology Stack

- **React 18**: Modern UI library for building interactive user interfaces
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Recharts**: Composable charting library for React
- **React Router Dom**: Client-side routing
- **Axios**: Promise-based HTTP client
- **Vite**: Next-generation frontend build tool
- **Heroicons**: SVG icon library

## Getting Started

### Prerequisites

- Node.js 14+ (18+ recommended)
- npm 7+ or yarn 1.22+
- Backend API running (see main [README.md](../README.md))

### Installation

1. Install dependencies:
   ```bash
   npm install
   # or
   yarn
   ```

2. Create a `.env` file in the frontend directory:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

3. Start the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. Open your browser and navigate to [http://localhost:3000](http://localhost:3000)

## Build for Production

```bash
npm run build
# or
yarn build
```

The build artifacts will be stored in the `dist/` directory.

## Project Structure

```
src/
├── components/         # Reusable UI components
│   ├── DataCard.jsx    # Container for data displays
│   ├── EmptyState.jsx  # Display for empty data
│   ├── ErrorBoundary.jsx # Error handler component
│   ├── LoadingSpinner.jsx # Loading indicator
│   ├── PageHeader.jsx  # Page header component
│   ├── StatCard.jsx    # KPI stat display
│   └── TimeRangeSelector.jsx # Time range filter
├── layouts/            # Layout components
│   └── DashboardLayout.jsx # Main application layout
├── pages/              # Page components
│   ├── Dashboard.jsx   # Main dashboard page
│   ├── SalesByGenre.jsx # Genre analysis page
│   ├── SalesByRegion.jsx # Regional analysis page
│   ├── Settings.jsx    # Settings and data generation
│   └── TopBooks.jsx    # Top books analysis
├── services/           # API and utility services
│   └── analyticsService.js # API client for analytics
├── App.jsx             # Application routes
├── index.css           # Global styles
└── main.jsx           # Application entry point
```

## Features

- **Interactive Dashboards**: Dynamic data visualization
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Filter by Time Range**: Analyze data for different time periods
- **Multiple Views**: Different perspectives on sales data
- **Error Handling**: Graceful error states and recovery
- **Data Loading States**: Clear indication of data loading
- **Easy Theme Customization**: Through Tailwind CSS configuration

## API Integration

The frontend communicates with the Django REST Framework backend through the `analyticsService.js` which provides methods for:

- Getting dashboard summary data
- Fetching time series data
- Retrieving top books by revenue
- Analyzing sales by region and genre
- Generating test data

All API calls include proper error handling and loading states.

## Customization

### Styling

The app uses Tailwind CSS for styling. You can customize the theme by editing `tailwind.config.js`:

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          // Customize your primary color palette
        },
        // Add more custom colors
      },
      // Add custom fonts, spacing, etc.
    },
  },
  // ...
}
```

### Adding New Charts

To add a new chart:

1. Create a new component or update an existing page
2. Import the desired chart type from Recharts
3. Connect to the appropriate API endpoint
4. Add the chart to the UI with proper loading and error states

## Browser Support

The dashboard is tested and works with:
- Chrome 90+
- Firefox 90+
- Safari 14+
- Edge 90+

## Development Notes

- Use the ErrorBoundary component to catch and display errors gracefully
- Implement proper loading states for all data-fetching operations
- Format numbers and currencies consistently across the app
- Handle empty data states with EmptyState component
- Use proper error handling for all API calls

## Research Focus Areas

As part of our research, we're specifically evaluating:

1. **Visualization Performance**: How well Recharts handles large datasets
2. **Data Loading Patterns**: Optimal strategies for loading analytics data
3. **UI Responsiveness**: Performance across device sizes
4. **State Management**: The sufficiency of React's built-in state management
5. **Build Performance**: Vite vs traditional build tools

## Contributing

This is a research project. Please contact the project maintainers before making contributions.

## License

Proprietary - Internal Research Project