from django.core.management.base import BaseCommand
from core.services.data_export import DataWarehouseExporter


class Command(BaseCommand):
    help = 'Export recent sales data to AWS S3'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=1)

    def handle(self, *args, **options):
        exporter = DataWarehouseExporter()
        days = options.get('days')
        file_key = exporter.export_recent_sales(days=days)

        if file_key:
            self.stdout.write(self.style.SUCCESS(f'Successfully exported data to {file_key}'))
        else:
            self.stdout.write(self.style.WARNING('No data to export'))