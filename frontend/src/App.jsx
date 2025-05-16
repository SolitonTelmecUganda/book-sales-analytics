// src/App.jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import Dashboard from './pages/Dashboard';
import TopBooks from './pages/TopBooks';
import SalesByRegion from './pages/SalesByRegion';
import SalesByGenre from './pages/SalesByGenre';
import Settings from './pages/Settings';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary 
      fallbackMessage="Something went wrong with the application. Please refresh the page."
      showDetails={true}
    >
      <Router>
        <Routes>
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={
              <ErrorBoundary fallbackMessage="Error loading dashboard">
                <Dashboard />
              </ErrorBoundary>
            } />
            <Route path="top-books" element={
              <ErrorBoundary fallbackMessage="Error loading top books data">
                <TopBooks />
              </ErrorBoundary>
            } />
            <Route path="sales-by-region" element={
              <ErrorBoundary fallbackMessage="Error loading regional sales data">
                <SalesByRegion />
              </ErrorBoundary>
            } />
            <Route path="sales-by-genre" element={
              <ErrorBoundary fallbackMessage="Error loading genre sales data">
                <SalesByGenre />
              </ErrorBoundary>
            } />
            <Route path="settings" element={
              <ErrorBoundary fallbackMessage="Error loading settings">
                <Settings />
              </ErrorBoundary>
            } />
          </Route>
        </Routes>
      </Router>
    </ErrorBoundary>
  );
}

export default App;