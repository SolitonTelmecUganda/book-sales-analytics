# api/views.py
import time

import pandas as pd
import redshift_connector
from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.data_export import DataWarehouseExporter


class RedshiftAPIView(APIView):
    """Base class for all views that access Redshift data warehouse"""
    permission_classes = [AllowAny]

    def get_redshift_connection(self):
        """Get connection to Redshift"""
        try:
            conn = redshift_connector.connect(
                host=settings.REDSHIFT_HOST,
                database=settings.REDSHIFT_DB,
                user=settings.REDSHIFT_USER,
                password=settings.REDSHIFT_PASSWORD,
                port=settings.REDSHIFT_PORT
            )
            conn.autocommit = True
            return conn
        except redshift_connector.Error as e:
            print(f"Error connecting to Redshift: {e}")
            raise

    def execute_query(self, query, params=None):
        """Execute query on Redshift and return as DataFrame"""
        conn = self.get_redshift_connection()
        cursor = conn.cursor()

        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Fetch all rows
            rows = cursor.fetchall()

            # Create DataFrame
            df = pd.DataFrame(rows, columns=columns)

            return df
        finally:
            cursor.close()
            conn.close()


class DashboardSummaryView(RedshiftAPIView):
    """Get overall summary statistics for dashboard"""

    def get(self, request):
        query = """
                SELECT (SELECT COUNT(*) FROM analytics.fact_sales)                AS total_sales, \
                       (SELECT SUM(quantity) FROM analytics.fact_sales)           AS total_books_sold, \
                       (SELECT SUM(sale_amount) FROM analytics.fact_sales)        AS total_revenue, \
                       (SELECT COUNT(DISTINCT book_id) FROM analytics.fact_sales) AS unique_books_sold \
                """

        df = self.execute_query(query)

        if df.empty:
            return Response({"error": "No data available"}, status=status.HTTP_404_NOT_FOUND)

        summary = df.iloc[0].to_dict()

        # Convert to appropriate types
        for k, v in summary.items():
            if pd.isna(v):
                summary[k] = 0
            elif isinstance(v, (pd.Timestamp, pd.Period)):
                summary[k] = v.strftime('%Y-%m-%d')

        return Response(summary)


class SalesTimeSeriesView(RedshiftAPIView):
    """Get time series data for sales trends"""

    def get(self, request):
        # Get query parameters
        interval = request.query_params.get('interval', 'day')
        days = int(request.query_params.get('days', 30))

        # Validate interval
        valid_intervals = ['day', 'week', 'month']
        if interval not in valid_intervals:
            return Response(
                {"error": f"Invalid interval. Must be one of: {', '.join(valid_intervals)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build query based on interval
        # Note: Using INTERVAL with a fixed string instead of parameterized query for the days part
        query = f"""
        SELECT 
            DATE_TRUNC('{interval}', sale_date)::DATE AS period,
            COUNT(*) AS num_sales,
            SUM(quantity) AS books_sold,
            SUM(sale_amount) AS revenue
        FROM analytics.fact_sales
        WHERE sale_date >= CURRENT_DATE - INTERVAL '{days} days'
        GROUP BY DATE_TRUNC('{interval}', sale_date)::DATE
        ORDER BY period
        """

        # No parameter needed now since we've incorporated 'days' directly in the query
        df = self.execute_query(query)

        if df.empty:
            return Response({"error": "No data available for the specified time range"},
                            status=status.HTTP_404_NOT_FOUND)

        # Convert period to datetime if it's not already
        try:
            if df['period'].dtype != 'datetime64[ns]':
                df['period'] = pd.to_datetime(df['period'])

            # Convert to JSON-friendly format
            result = {
                'period': df['period'].dt.strftime('%Y-%m-%d').tolist(),
                'num_sales': df['num_sales'].tolist(),
                'books_sold': df['books_sold'].tolist(),
                'revenue': [float(x) for x in df['revenue']]
            }
        except Exception as e:
            # Fallback if datetime conversion fails
            result = {
                'period': [str(x) for x in df['period'].tolist()],
                'num_sales': df['num_sales'].tolist(),
                'books_sold': df['books_sold'].tolist(),
                'revenue': [float(x) for x in df['revenue']]
            }

        return Response(result)


class TopBooksView(RedshiftAPIView):
    """Get top performing books"""

    def get(self, request):
        # Get query parameters
        limit = int(request.query_params.get('limit', 10))
        days = int(request.query_params.get('days', 30))

        query = f"""
                SELECT b.book_id, 
                       b.title, 
                       b.author, 
                       b.genre, 
                       COUNT(s.sale_id)   AS num_sales, 
                       SUM(s.quantity)    AS total_quantity, 
                       SUM(s.sale_amount) AS total_revenue
                FROM analytics.dim_book b
                         JOIN analytics.fact_sales s ON b.book_id = s.book_id
                WHERE s.sale_date >= CURRENT_DATE - INTERVAL '{days} days'
                GROUP BY b.book_id, b.title, b.author, b.genre
                ORDER BY total_revenue DESC
                LIMIT {limit}
                """

        df = self.execute_query(query)

        if df.empty:
            return Response({"error": "No data available"}, status=status.HTTP_404_NOT_FOUND)

        # Convert to list of dicts
        result = df.to_dict('records')

        # Ensure numeric values are native Python types, not numpy/pandas types
        for i, book in enumerate(result):
            result[i]['total_quantity'] = int(book['total_quantity']) if pd.notna(book['total_quantity']) else 0
            result[i]['num_sales'] = int(book['num_sales']) if pd.notna(book['num_sales']) else 0
            result[i]['total_revenue'] = float(book['total_revenue']) if pd.notna(book['total_revenue']) else 0

        return Response(result)


class SalesByRegionView(RedshiftAPIView):
    """Get sales breakdown by region"""

    def get(self, request):
        days = int(request.query_params.get('days', 30))

        query = f"""
                SELECT region, 
                       COUNT(*)         AS num_transactions, 
                       SUM(quantity)    AS books_sold, 
                       SUM(sale_amount) AS revenue
                FROM analytics.fact_sales
                WHERE sale_date >= CURRENT_DATE - INTERVAL '{days} days'
                GROUP BY region
                ORDER BY revenue DESC
                """

        df = self.execute_query(query)

        if df.empty:
            return Response({"error": "No data available"}, status=status.HTTP_404_NOT_FOUND)

        # Convert to list of dicts
        result = df.to_dict('records')

        # Ensure numeric values are native Python types
        for i, region in enumerate(result):
            result[i]['num_transactions'] = int(region['num_transactions']) if pd.notna(
                region['num_transactions']) else 0
            result[i]['books_sold'] = int(region['books_sold']) if pd.notna(region['books_sold']) else 0
            result[i]['revenue'] = float(region['revenue']) if pd.notna(region['revenue']) else 0

        return Response(result)


class SalesByGenreView(RedshiftAPIView):
    """Get sales breakdown by book genre"""

    def get(self, request):
        days = int(request.query_params.get('days', 30))

        query = f"""
                SELECT b.genre, 
                       COUNT(s.sale_id)   AS num_sales, 
                       SUM(s.quantity)    AS books_sold, 
                       SUM(s.sale_amount) AS revenue
                FROM analytics.dim_book b
                         JOIN analytics.fact_sales s ON b.book_id = s.book_id
                WHERE s.sale_date >= CURRENT_DATE - INTERVAL '{days} days'
                GROUP BY b.genre
                ORDER BY revenue DESC
                """

        df = self.execute_query(query)

        if df.empty:
            return Response({"error": "No data available"}, status=status.HTTP_404_NOT_FOUND)

        # Convert to list of dicts
        result = df.to_dict('records')

        # Ensure numeric values are native Python types
        for i, genre in enumerate(result):
            result[i]['num_sales'] = int(genre['num_sales']) if pd.notna(genre['num_sales']) else 0
            result[i]['books_sold'] = int(genre['books_sold']) if pd.notna(genre['books_sold']) else 0
            result[i]['revenue'] = float(genre['revenue']) if pd.notna(genre['revenue']) else 0

        return Response(result)


@api_view(['POST'])
@permission_classes([AllowAny])
def generate_test_data(request):
    """Generate test data and upload to S3 and Redshift"""
    try:
        # Get parameters
        num_books = int(request.data.get('num_books', 500))
        num_sales = int(request.data.get('num_sales', 10000))
        skip_redshift = request.data.get('skip_redshift', False)

        # Validate
        if num_books <= 0 or num_sales <= 0:
            return Response(
                {"error": "Number of books and sales must be positive"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate data
        exporter = DataWarehouseExporter()
        result = exporter.generate_test_data(num_books=num_books, num_sales=num_sales)

        # Load to Redshift if requested
        redshift_result = None
        if not skip_redshift:
            redshift_result = exporter.load_to_redshift(result['books_key'], result['sales_key'])

        return Response({
            "status": "success",
            "generated": {
                "books": num_books,
                "sales": num_sales
            },
            "s3": {
                "books_key": result['books_key'],
                "sales_key": result['sales_key']
            },
            "redshift": redshift_result
        })

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class OptimizedSalesTimeSeriesView(APIView):
    """Optimized view for time series data with improved performance for large date ranges."""

    def get(self, request):
        start_time = time.time()

        # Get query parameters
        interval = request.query_params.get('interval', 'auto')
        days = int(request.query_params.get('days', 30))

        # Cache key based on parameters
        cache_key = f"sales_timeseries_{interval}_{days}"
        cached_data = cache.get(cache_key)

        if cached_data:
            # Add processing time info
            processing_info = {
                "cached": True,
                "processing_time_ms": round((time.time() - start_time) * 1000)
            }
            cached_data["processing_info"] = processing_info
            return Response(cached_data)

        # Determine appropriate time granularity based on the time range
        if interval == 'auto':
            if days <= 30:
                interval = 'day'
            elif days <= 90:
                interval = 'week'
            elif days <= 365:
                interval = 'month'
            else:
                interval = 'quarter'

        # Validate interval
        valid_intervals = ['day', 'week', 'month', 'quarter', 'year']
        if interval not in valid_intervals:
            return Response(
                {"error": f"Invalid interval. Must be one of: {', '.join(valid_intervals)} or 'auto'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set a max limit for raw data points to return
        max_data_points = 100

        # Use appropriate query based on the time period for optimal performance
        if days <= 90:
            # For smaller date ranges, use the detailed sales_by_day view
            df = self._query_daily_sales(days, interval)
        else:
            # For larger date ranges, use the pre-aggregated views
            df = self._query_aggregated_sales(days, interval, max_data_points)

        if df.empty:
            return Response({"error": "No data available for the specified time range"},
                            status=status.HTTP_404_NOT_FOUND)

        # Convert to JSON-friendly format with proper data types
        result = self._prepare_response(df, interval)

        # Add processing time information
        processing_time = time.time() - start_time
        result["processing_info"] = {
            "cached": False,
            "interval_used": interval,
            "data_points": len(result["period"]),
            "processing_time_ms": round(processing_time * 1000)
        }

        # Cache the result (adjust timeout based on time range)
        cache_timeout = min(days * 60, 86400)  # Cache longer for bigger ranges, max 24 hours
        cache.set(cache_key, result, cache_timeout)

        return Response(result)

    def _query_daily_sales(self, days, interval):
        """Query daily sales from the sales_by_day view for smaller time ranges."""
        conn = self._get_redshift_connection()
        cursor = conn.cursor()

        try:
            # Use the pre-aggregated view for faster queries
            query = f"""
            SELECT 
                DATE_TRUNC('{interval}', day)::DATE AS period,
                SUM(num_sales) AS num_sales,
                SUM(total_books_sold) AS books_sold,
                SUM(total_revenue) AS revenue
            FROM analytics.sales_by_day
            WHERE day >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE_TRUNC('{interval}', day)::DATE
            ORDER BY period
            """

            cursor.execute(query, [days])

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            # Fetch all rows
            rows = cursor.fetchall()

            # Create DataFrame
            df = pd.DataFrame(rows, columns=columns)

            return df
        finally:
            cursor.close()
            conn.close()

    def _query_aggregated_sales(self, days, interval, max_points):
        """Query pre-aggregated sales data for larger time ranges."""
        conn = self._get_redshift_connection()
        cursor = conn.cursor()

        try:
            # For large time periods, first check if we should use the monthly_sales view
            if interval in ['month', 'quarter', 'year']:
                # Use monthly_sales view which is pre-aggregated
                query = f"""
                SELECT 
                    DATE_TRUNC('{interval}', month)::DATE AS period,
                    SUM(num_sales) AS num_sales,
                    SUM(total_books_sold) AS books_sold,
                    SUM(total_revenue) AS revenue
                FROM analytics.monthly_sales
                WHERE month >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE_TRUNC('{interval}', month)::DATE
                ORDER BY period
                """
            else:
                # For custom intervals or if we need to downsample, use this approach
                # First determine how many days to aggregate per point to stay under max_points
                bucket_size = max(1, days // max_points)

                query = f"""
                WITH date_series AS (
                    SELECT
                        CURRENT_DATE - (n || ' days')::INTERVAL AS day
                    FROM generate_series(0, %s) n
                ),
                bucketed_dates AS (
                    SELECT
                        -- Create buckets of days
                        CURRENT_DATE - ((n/{bucket_size}) * {bucket_size} || ' days')::INTERVAL AS period
                    FROM generate_series(0, %s) n
                ),
                aggregated AS (
                    SELECT 
                        bd.period,
                        SUM(COALESCE(s.num_sales, 0)) AS num_sales,
                        SUM(COALESCE(s.total_books_sold, 0)) AS books_sold,
                        SUM(COALESCE(s.total_revenue, 0)) AS revenue
                    FROM bucketed_dates bd
                    LEFT JOIN analytics.sales_by_day s ON DATE_TRUNC('day', s.day) = DATE_TRUNC('day', bd.period)
                    GROUP BY bd.period
                    ORDER BY bd.period
                )
                SELECT * FROM aggregated
                """

                cursor.execute(query, [days, days])

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            # Fetch all rows
            rows = cursor.fetchall()

            # Create DataFrame
            df = pd.DataFrame(rows, columns=columns)

            return df
        except Exception as e:
            print(f"Error in _query_aggregated_sales: {str(e)}")
            # Fallback to a simpler query if the above fails
            try:
                fallback_query = f"""
                SELECT 
                    DATE_TRUNC('{interval}', sale_date)::DATE AS period,
                    COUNT(*) AS num_sales,
                    SUM(quantity) AS books_sold,
                    SUM(sale_amount) AS revenue
                FROM analytics.fact_sales
                WHERE sale_date >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE_TRUNC('{interval}', sale_date)::DATE
                ORDER BY period
                """

                cursor.execute(fallback_query, [days])

                # Get column names
                columns = [desc[0] for desc in cursor.description]

                # Fetch all rows
                rows = cursor.fetchall()

                # Create DataFrame
                df = pd.DataFrame(rows, columns=columns)

                return df
            except Exception as fallback_error:
                print(f"Fallback query also failed: {str(fallback_error)}")
                return pd.DataFrame()
        finally:
            cursor.close()
            conn.close()

    def _prepare_response(self, df, interval):
        """Prepare the response data from the DataFrame."""
        try:
            # Convert period to datetime if it's not already
            if df['period'].dtype != 'datetime64[ns]':
                df['period'] = pd.to_datetime(df['period'])

            # Format date based on interval
            date_format = '%Y-%m-%d'  # Default format
            if interval == 'month':
                date_format = '%Y-%m'
            elif interval == 'quarter':
                # Custom handling for quarters
                df['year'] = df['period'].dt.year
                df['quarter'] = df['period'].dt.quarter
                periods = [f"{year}-Q{quarter}" for year, quarter in zip(df['year'], df['quarter'])]

                result = {
                    'period': periods,
                    'num_sales': df['num_sales'].fillna(0).astype(int).tolist(),
                    'books_sold': df['books_sold'].fillna(0).astype(int).tolist(),
                    'revenue': df['revenue'].fillna(0).astype(float).tolist()
                }
                return result
            elif interval == 'year':
                date_format = '%Y'

            # Standard formatting for most intervals
            result = {
                'period': df['period'].dt.strftime(date_format).tolist(),
                'num_sales': df['num_sales'].fillna(0).astype(int).tolist(),
                'books_sold': df['books_sold'].fillna(0).astype(int).tolist(),
                'revenue': df['revenue'].fillna(0).astype(float).tolist()
            }
            return result
        except Exception as e:
            print(f"Error in _prepare_response: {str(e)}")
            # Fallback if date conversion fails
            result = {
                'period': [str(x) for x in df['period'].tolist()],
                'num_sales': df['num_sales'].fillna(0).astype(int).tolist(),
                'books_sold': df['books_sold'].fillna(0).astype(int).tolist(),
                'revenue': df['revenue'].fillna(0).astype(float).tolist()
            }
            return result

    def _get_redshift_connection(self):
        """Get connection to Redshift."""
        import redshift_connector

        conn = redshift_connector.connect(
            host=settings.REDSHIFT_HOST,
            database=settings.REDSHIFT_DB,
            user=settings.REDSHIFT_USER,
            password=settings.REDSHIFT_PASSWORD,
            port=settings.REDSHIFT_PORT
        )
        conn.autocommit = True
        return conn