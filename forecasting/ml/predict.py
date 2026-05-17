# forecasting/ml/predict.py

import os
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.conf import settings

ML_DIR = os.path.join(settings.BASE_DIR, 'forecasting', 'ml')


def load_model():
    """Load the best saved model from disk."""
    model_path = os.path.join(ML_DIR, 'load_forecast_model_best.pkl')
    with open(model_path, 'rb') as f:
        return pickle.load(f)


def predict_next_24_hours():
    """
    Run 24-hour forecast using her trained model.
    Returns a list of dicts ready for the API response.
    """
    model = load_model()

    # Build next 24 hours of feature data
    start = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    future_dates = pd.date_range(start=start, periods=24, freq='h')

    future_df = pd.DataFrame({
        'hour':        future_dates.hour,
        'day_of_week': future_dates.dayofweek,
        'is_weekend':  (future_dates.dayofweek >= 5).astype(int),
        'day':         future_dates.day,
        'month':       future_dates.month,
        'temperature': 20 + np.random.normal(0, 2, 24),  # replace with real weather later
    })

    X = future_df[['hour', 'day_of_week', 'is_weekend', 'day', 'month', 'temperature']].values
    predictions = model.predict(X)

    # Peak threshold — 85th percentile of predictions
    threshold = float(np.percentile(predictions, 85))

    return {
        'generated_at': datetime.now().isoformat(),
        'peak_threshold': round(threshold, 2),
        'forecast': [
            {
                'datetime':     future_dates[i].isoformat(),
                'hour':         int(future_dates[i].hour),
                'predicted_kw': round(float(predictions[i]), 2),
                'is_peak':      float(predictions[i]) >= threshold,
            }
            for i in range(24)
        ]
    }