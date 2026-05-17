import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from forecasting.models import LoadReading


class Command(BaseCommand):
    help = 'Seeds simulated_load_data.csv into the LoadReading table'

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(
            settings.BASE_DIR, 'forecasting', 'ml', 'data', 'simulated_load_data.csv'
        )

        if not os.path.exists(csv_path):
            self.stderr.write(f"CSV not found at: {csv_path}")
            return

        self.stdout.write("Reading CSV...")
        df = pd.read_csv(csv_path)
        df['datetime'] = pd.to_datetime(df['datetime'])

        # Clear old data to avoid duplicates on re-run
        LoadReading.objects.all().delete()
        self.stdout.write("Cleared old records.")

        # Bulk insert for speed
        batch = [
            LoadReading(
                datetime    = row['datetime'],
                load_kw     = row['load_kw'],
                temperature = row['temperature'],
                hour        = row['hour'],
                day_of_week = row['day_of_week'],
                is_weekend  = bool(row['is_weekend']),
                month       = row['month'],
            )
            for _, row in df.iterrows()
        ]

        LoadReading.objects.bulk_create(batch, batch_size=500)
        self.stdout.write(self.style.SUCCESS(
            f"✓ Seeded {len(batch)} records from CSV."
        ))