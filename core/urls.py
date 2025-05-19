# api/urls.py
from django.urls import path
from .views import (
    DashboardSummaryView,
    SalesTimeSeriesView,
    TopBooksView,
    SalesByRegionView,
    SalesByGenreView,
    generate_test_data,
    OptimizedSalesTimeSeriesView
)

urlpatterns = [
    path('analytics/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('analytics/timeseries/', SalesTimeSeriesView.as_view(), name='sales-timeseries'),
    path('analytics/top-books/', TopBooksView.as_view(), name='top-books'),
    path('analytics/sales-by-region/', SalesByRegionView.as_view(), name='sales-by-region'),
    path('analytics/sales-by-genre/', SalesByGenreView.as_view(), name='sales-by-genre'),
    path('analytics/generate-test-data/', generate_test_data, name='generate-test-data'),
    path('analytics/optimized-timeseries/', OptimizedSalesTimeSeriesView.as_view(), name='optimized-sales-timeseries'),
]