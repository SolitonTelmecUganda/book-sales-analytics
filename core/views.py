# api/views.py
import pandas as pd
import redshift_connector
from django.conf import settings
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
        conn = redshift_connector.connect(
            host=settings.REDSHIFT_HOST,
            database=settings.REDSHIFT_DB,
            user=settings.REDSHIFT_USER,
            password=settings.REDSHIFT_PASSWORD,
            port=settings.REDSHIFT_PORT
        )
        conn.autocommit = True
        return conn

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