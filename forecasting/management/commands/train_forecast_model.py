from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Train the forecast model from real LCL CSV data and save pkl files'

    def handle(self, *args, **kwargs):
        # Import inside handle() to avoid AppRegistryNotReady
        import django
        from forecasting.ml.forecaster import LoadForecaster

        self.stdout.write("Loading real smart meter data...")
        forecaster = LoadForecaster()

        try:
            forecaster.load_real_data()
        except FileNotFoundError as e:
            self.stderr.write(str(e))
            self.stderr.write(
                "Place household_1.csv to household_4.csv inside forecasting/ml/data/"
            )
            return

        self.stdout.write("Training models...")
        metrics = forecaster.train_models()

        for model_name, m in metrics.items():
            self.stdout.write(f"  {model_name}: R2={m['R2']}  MAE={m['MAE']} kWh")

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Training complete. Best model: {forecaster.best_model_name}"
        ))
        self.stdout.write("✓ Model saved to forecasting/ml/load_forecast_model_best.pkl")
        self.stdout.write("✓ Run 'py manage.py seed_forecast_data' to seed the DB")