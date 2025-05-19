# analytics/management/commands/optimize_redshift.py
import time
from django.core.management.base import BaseCommand
from django.conf import settings
import redshift_connector


class Command(BaseCommand):
    help = 'Optimizes Redshift for time series performance by creating necessary views and indexes'

    def add_arguments(self, parser):
        parser.add_argument('--test', action='store_true', help='Run performance tests after optimization')
        parser.add_argument('--refresh', action='store_true', help='Refresh materialized views')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Redshift optimization...'))

        # Create the connection
        conn = self._get_redshift_connection()
        cursor = conn.cursor()

        try:
            # Execute optimization SQL
            self.stdout.write('Creating or updating optimization views...')

            # Create sales_by_day view
            cursor.execute("""
                           CREATE OR REPLACE VIEW analytics.sales_by_day AS
                           SELECT DATE_TRUNC('day', sale_date)::DATE AS day,
                                  COUNT(*)                           AS num_sales,
                                  SUM(quantity)                      AS total_books_sold,
                                  SUM(sale_amount)                   AS total_revenue
                           FROM analytics.fact_sales
                           GROUP BY DATE_TRUNC('day', sale_date)::DATE
                           ORDER BY day;
                           """)
            self.stdout.write(self.style.SUCCESS('Created sales_by_day view'))

            # Create monthly_sales view
            cursor.execute("""
                           CREATE OR REPLACE VIEW analytics.monthly_sales AS
                           SELECT DATE_TRUNC('month', sale_date)::DATE AS month,
                                  COUNT(*)                             AS num_sales,
                                  SUM(quantity)                        AS total_books_sold,
                                  SUM(sale_amount)                     AS total_revenue
                           FROM analytics.fact_sales
                           GROUP BY DATE_TRUNC('month', sale_date)::DATE
                           ORDER BY month;
                           """)
            self.stdout.write(self.style.SUCCESS('Created monthly_sales view'))

            # Check if we should create materialized views
            try:
                # Test if materialized views are supported
                cursor.execute("SELECT 1 FROM pg_catalog.pg_matviews LIMIT 1")

                # Create materialized views if supported
                cursor.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.mv_sales_by_day
                AS
                SELECT 
                    DATE_TRUNC('day', sale_date)::DATE AS day,
                    COUNT(*) AS num_sales,
                    SUM(quantity) AS total_books_sold,
                    SUM(sale_amount) AS total_revenue
                FROM analytics.fact_sales
                GROUP BY DATE_TRUNC('day', sale_date)::DATE
                ORDER BY day;
                """)
                self.stdout.write(self.style.SUCCESS('Created materialized view mv_sales_by_day'))

                cursor.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.mv_monthly_sales
                AS
                SELECT
                    DATE_TRUNC('month', sale_date)::DATE AS month,
                    COUNT(*) AS num_sales,
                    SUM(quantity) AS total_books_sold,
                    SUM(sale_amount) AS total_revenue
                FROM analytics.fact_sales
                GROUP BY DATE_TRUNC('month', sale_date)::DATE
                ORDER BY month;
                """)
                self.stdout.write(self.style.SUCCESS('Created materialized view mv_monthly_sales'))

                # Refresh materialized views if requested
                if options['refresh']:
                    self.stdout.write('Refreshing materialized views...')
                    cursor.execute("REFRESH MATERIALIZED VIEW analytics.mv_sales_by_day")
                    cursor.execute("REFRESH MATERIALIZED VIEW analytics.mv_monthly_sales")
                    self.stdout.write(self.style.SUCCESS('Materialized views refreshed'))

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Materialized views not supported or error creating them: {str(e)}'))
                self.stdout.write(self.style.WARNING('Continuing with regular views only'))

            # Optimize table for query performance
            try:
                self.stdout.write('Setting distribution and sort keys...')
                cursor.execute("ALTER TABLE analytics.fact_sales ALTER DISTKEY sale_date")
                cursor.execute("ALTER TABLE analytics.fact_sales ALTER SORTKEY (sale_date, book_id)")
                self.stdout.write(self.style.SUCCESS('Distribution and sort keys set'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Unable to set distribution/sort keys: {str(e)}'))
                self.stdout.write(self.style.WARNING('This may be due to permissions or table being already optimized'))

            # Create stored procedure for view refresh
            cursor.execute("""
                           CREATE OR REPLACE PROCEDURE analytics.refresh_sales_views()
                           AS
                           $$
                           BEGIN
                               -- Refresh materialized views if they exist
                               BEGIN
                                   REFRESH MATERIALIZED VIEW analytics.mv_sales_by_day;
                                   REFRESH MATERIALIZED VIEW analytics.mv_monthly_sales;
                               EXCEPTION
                                   WHEN OTHERS THEN
                                       RAISE NOTICE 'Unable to refresh materialized views: %', SQLERRM;
                               END;

                               -- Always vacuum and analyze
                               VACUUM analytics.fact_sales;
                               ANALYZE analytics.fact_sales;
                           END;
                           $$ LANGUAGE plpgsql;
                           """)
            self.stdout.write(self.style.SUCCESS('Created refresh_sales_views procedure'))

            # Run performance tests if requested
            if options['test']:
                self._run_performance_tests(cursor)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during optimization: {str(e)}'))
        finally:
            cursor.close()
            conn.close()
            self.stdout.write(self.style.SUCCESS('Optimization complete'))

    def _get_redshift_connection(self):
        """Get connection to Redshift."""
        conn = redshift_connector.connect(
            host=settings.REDSHIFT_HOST,
            database=settings.REDSHIFT_DB,
            user=settings.REDSHIFT_USER,
            password=settings.REDSHIFT_PASSWORD,
            port=settings.REDSHIFT_PORT
        )
        conn.autocommit = True
        return conn

    def _run_performance_tests(self, cursor):
        """Run performance tests on various time ranges."""
        self.stdout.write(self.style.NOTICE('\nRunning performance tests...'))

        test_ranges = [
            ('30 days', 30),
            ('90 days', 90),
            ('180 days', 180),
            ('365 days', 365),
            ('730 days', 730)
        ]

        queries = [
            {
                'name': 'Direct fact_sales query',
                'sql': """
                       SELECT DATE_TRUNC('day', sale_date)::DATE AS period,
                              COUNT(*)                           AS num_sales,
                              SUM(quantity)                      AS books_sold,
                              SUM(sale_amount)                   AS revenue
                       FROM analytics.fact_sales
                       WHERE sale_date >= CURRENT_DATE - INTERVAL '%s days'
                       GROUP BY DATE_TRUNC('day', sale_date)::DATE
                       ORDER BY period
                       """
            },
            {
                'name': 'Using sales_by_day view',
                'sql': """
                       SELECT day              AS period,
                              num_sales,
                              total_books_sold AS books_sold,
                              total_revenue    AS revenue
                       FROM analytics.sales_by_day
                       WHERE day >= CURRENT_DATE - INTERVAL '%s days'
                       ORDER BY period
                       """
            },
            {
                'name': 'Using monthly_sales aggregation',
                'sql': """
                       SELECT DATE_TRUNC('month', month)::DATE AS period,
                              SUM(num_sales)                   AS num_sales,
                              SUM(total_books_sold)            AS books_sold,
                              SUM(total_revenue)               AS revenue
                       FROM analytics.monthly_sales
                       WHERE month >= CURRENT_DATE - INTERVAL '%s days'
                       GROUP BY DATE_TRUNC('month', month)::DATE
                       ORDER BY period
                       """
            }
        ]

        # Add materialized view queries if they exist
        try:
            cursor.execute("SELECT 1 FROM analytics.mv_sales_by_day LIMIT 1")
            # If this succeeds, materialized views exist
            queries.append({
                'name': 'Using mv_sales_by_day materialized view',
                'sql': """
                       SELECT day              AS period,
                              num_sales,
                              total_books_sold AS books_sold,
                              total_revenue    AS revenue
                       FROM analytics.mv_sales_by_day
                       WHERE day >= CURRENT_DATE - INTERVAL '%s days'
                       ORDER BY period
                       """
            })
        except Exception:
            pass

        # Results table
        results = []

        # Run the tests
        for time_range, days in test_ranges:
            self.stdout.write(f'\nTesting time range: {time_range}')
            range_results = {'range': time_range}

            for query in queries:
                start_time = time.time()

                try:
                    cursor.execute(query['sql'], [days])
                    rows = cursor.fetchall()
                    row_count = len(rows)

                    execution_time = time.time() - start_time

                    self.stdout.write(f"  {query['name']}: {execution_time:.2f} seconds ({row_count} rows)")
                    range_results[query['name']] = f"{execution_time:.2f}s"

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error executing {query['name']}: {str(e)}"))
                    range_results[query['name']] = "ERROR"

            results.append(range_results)

        # Print results table
        self.stdout.write('\nPerformance Test Results:')
        self.stdout.write('-' * 100)

        # Print header
        header = ['Time Range'] + [q['name'] for q in queries]
        self.stdout.write('| ' + ' | '.join(header) + ' |')
        self.stdout.write('|' + '|'.join(['-' * len(h) for h in header]) + '|')

        # Print results
        for result in results:
            row = [result['range']] + [result.get(q['name'], 'N/A') for q in queries]
            self.stdout.write('| ' + ' | '.join(row) + ' |')

        self.stdout.write('-' * 100)