import os
import pickle
import numpy as np
import pandas as pd
from django.conf import settings

ML_DIR   = os.path.join(settings.BASE_DIR, 'forecasting', 'ml')
DATA_DIR = os.path.join(ML_DIR, 'data')
FEATURES = ['hour', 'day_of_week', 'is_weekend', 'month', 'rolling_24h_avg']


def load_model():
    path = os.path.join(ML_DIR, 'load_forecast_model_best.pkl')
    if not os.path.exists(path):
        raise FileNotFoundError(
            "Model file not found. Run: py manage.py train_forecast_model"
        )
    with open(path, 'rb') as f:
        return pickle.load(f)


def get_recent_avg():
    """
    Get the rolling 24h average from the DB if available,
    otherwise fall back to the saved CSV.
    """
    try:
        from forecasting.models import LoadReading
        qs = LoadReading.objects.order_by('-datetime')[:24]
        if qs.exists():
            values = [r.load_kwh for r in qs]
            return float(np.mean(values))
    except Exception:
        pass

    # Fallback — read from CSV
    csv_path = os.path.join(DATA_DIR, 'real_load_data_hourly.csv')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return float(df['load_kwh'].tail(24).mean())

    return 1.0   # safe default


def predict_next_24_hours():
    """
    Load the trained model and return 24-hour predictions.
    Called directly by the Django ForecastView.
    """
    from datetime import datetime, timedelta

    model      = load_model()
    recent_avg = get_recent_avg()

    start       = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    future_dt   = pd.date_range(start=start, periods=24, freq='h')

    future = pd.DataFrame({
        'hour':            future_dt.hour,
        'day_of_week':     future_dt.dayofweek,
        'is_weekend':      (future_dt.dayofweek >= 5).astype(int),
        'month':           future_dt.month,
        'rolling_24h_avg': [recent_avg] * 24,
    })

    preds     = model.predict(future[FEATURES].values)
    threshold = float(np.percentile(preds, 85))

    return {
        'generated_at':  datetime.now().isoformat(),
        'peak_threshold': round(threshold, 4),
        'model_used':    'Random Forest',
        'forecast': [
            {
                'datetime':           future_dt[i].isoformat(),
                'hour':               int(future_dt[i].hour),
                'predicted_load_kwh': round(float(preds[i]), 4),
                'is_peak':            float(preds[i]) >= threshold,
            }
            for i in range(24)
        ]
    }