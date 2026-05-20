import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import json
import os
import pickle
import warnings
warnings.filterwarnings('ignore')

import django
from django.conf import settings

# All file paths now relative to forecasting/ml/
ML_DIR   = os.path.join(settings.BASE_DIR, 'forecasting', 'ml')
DATA_DIR = os.path.join(ML_DIR, 'data')

DATA_FILES = {
    'household1': os.path.join(DATA_DIR, 'household_1.csv'),
    'household2': os.path.join(DATA_DIR, 'household_2.csv'),
    'household3': os.path.join(DATA_DIR, 'household_3.csv'),
    'household4': os.path.join(DATA_DIR, 'household_4.csv'),
}

FEATURES = ['hour', 'day_of_week', 'is_weekend', 'month', 'rolling_24h_avg']


class LoadForecaster:
    """Main class for load forecasting using real smart meter data."""

    def __init__(self):
        self.data           = None
        self.train_data     = None
        self.test_data      = None
        self.lr_model       = None
        self.rf_model       = None
        self.best_model     = None
        self.best_model_name = None
        self.metrics        = {}
        self.forecast_df    = None
        self.peak_threshold = None
        self.peak_hours_df  = None
        self._peak_info     = {}

    def load_real_data(self):
        print("\n[PHASE 1] DATA LOADING AND PREPARATION")
        file_series = []

        for file_label, filepath in DATA_FILES.items():
            if not os.path.exists(filepath):
                print(f"  [SKIP] {filepath} not found")
                continue

            df = pd.read_csv(filepath)
            df.columns = df.columns.str.strip()
            df['DateTime'] = pd.to_datetime(df['DateTime'])
            df['load'] = pd.to_numeric(df['KWH/hh (per half hour)'], errors='coerce')
            df = df.dropna(subset=['load'])

            agg = df.groupby('DateTime')['load'].sum()
            file_series.append(agg)
            print(f"  [OK] {file_label}: {df['LCLid'].nunique()} households, {len(agg)} timestamps")

        if not file_series:
            raise FileNotFoundError("No CSV files found in forecasting/ml/data/")

        combined = pd.concat(file_series, axis=1).fillna(0)
        combined.columns = [f'file_{i}' for i in range(len(file_series))]
        combined['total_kwh_hh'] = combined.sum(axis=1)

        hourly = combined['total_kwh_hh'].resample('h').sum().reset_index()
        hourly.columns = ['datetime', 'load_kwh']
        hourly = hourly[hourly['load_kwh'] > 0].copy()

        hourly['hour']            = hourly['datetime'].dt.hour
        hourly['day_of_week']     = hourly['datetime'].dt.dayofweek
        hourly['is_weekend']      = (hourly['day_of_week'] >= 5).astype(int)
        hourly['month']           = hourly['datetime'].dt.month
        hourly['day']             = hourly['datetime'].dt.day
        hourly['rolling_24h_avg'] = hourly['load_kwh'].rolling(window=24, min_periods=1).mean()
        hourly = hourly.dropna().reset_index(drop=True)

        self.data = hourly
        print(f"  [OK] {len(hourly)} hourly records loaded")
        print(f"  Date range: {hourly['datetime'].min().date()} → {hourly['datetime'].max().date()}")

        # Save cleaned CSV for seeding into DB
        out_path = os.path.join(DATA_DIR, 'real_load_data_hourly.csv')
        hourly.to_csv(out_path, index=False)
        print(f"  [SAVED] real_load_data_hourly.csv")
        return hourly

    def train_models(self):
        print("\n[PHASE 2] MODEL TRAINING")
        df     = self.data.copy()
        X      = df[FEATURES].values
        y      = df['load_kwh'].values
        split  = int(len(df) * 0.8)

        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        self.train_data = df.iloc[:split]
        self.test_data  = df.iloc[split:]

        # Linear Regression
        self.lr_model = LinearRegression()
        self.lr_model.fit(X_train, y_train)
        lr_pred = self.lr_model.predict(X_test)
        lr_mae  = mean_absolute_error(y_test, lr_pred)
        lr_r2   = r2_score(y_test, lr_pred)
        self.metrics['Linear Regression'] = {'MAE': round(lr_mae, 4), 'R2': round(lr_r2, 4)}
        print(f"  LR  → R2: {lr_r2:.4f}  MAE: {lr_mae:.4f} kWh")

        # Random Forest
        self.rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        self.rf_model.fit(X_train, y_train)
        rf_pred = self.rf_model.predict(X_test)
        rf_mae  = mean_absolute_error(y_test, rf_pred)
        rf_r2   = r2_score(y_test, rf_pred)
        self.metrics['Random Forest'] = {'MAE': round(rf_mae, 4), 'R2': round(rf_r2, 4)}
        print(f"  RF  → R2: {rf_r2:.4f}  MAE: {rf_mae:.4f} kWh")

        self.best_model      = self.rf_model if rf_r2 >= lr_r2 else self.lr_model
        self.best_model_name = 'Random Forest' if rf_r2 >= lr_r2 else 'Linear Regression'
        print(f"  [OK] Best: {self.best_model_name}")

        # Save models
        for name, model, suffix in [
            (self.best_model_name, self.best_model,  'best'),
            ('Linear Regression',  self.lr_model,    'lr'),
            ('Random Forest',      self.rf_model,    'rf'),
        ]:
            path = os.path.join(ML_DIR, f'load_forecast_model_{suffix}.pkl')
            with open(path, 'wb') as f:
                pickle.dump(model, f)
        print("  [SAVED] model pkl files")

        # Save metrics JSON
        results = {
            'metadata':  {'best_model': self.best_model_name, 'data_source': 'LCL real data (4 households)'},
            'metrics':   self.metrics,
            'features':  FEATURES,
        }
        with open(os.path.join(ML_DIR, 'forecast_results.json'), 'w') as f:
            json.dump(results, f, indent=2)

        return self.metrics

    def predict_next_24_hours(self):
        """Run inference for the next 24 hours. Returns list of dicts."""
        last_dt      = self.data['datetime'].max()
        forecast_dt  = pd.date_range(start=last_dt + pd.Timedelta(hours=1), periods=24, freq='h')
        recent_avg   = float(self.data['load_kwh'].tail(24).mean())

        future = pd.DataFrame({
            'hour':            forecast_dt.hour,
            'day_of_week':     forecast_dt.dayofweek,
            'is_weekend':      (forecast_dt.dayofweek >= 5).astype(int),
            'month':           forecast_dt.month,
            'rolling_24h_avg': [recent_avg] * 24,
        })

        preds = self.best_model.predict(future[FEATURES].values)

        self.forecast_df = pd.DataFrame({
            'datetime':           forecast_dt,
            'hour':               forecast_dt.hour,
            'predicted_load_kwh': preds,
        })

        threshold = float(np.percentile(preds, 85))
        self.peak_threshold = threshold

        return [
            {
                'datetime':           dt.isoformat(),
                'hour':               int(h),
                'predicted_load_kwh': round(float(p), 4),
                'is_peak':            float(p) >= threshold,
            }
            for dt, h, p in zip(forecast_dt, forecast_dt.hour, preds)
        ]

    def get_peak_info(self):
        """Return peak summary dict for API response."""
        loads      = self.forecast_df['predicted_load_kwh'].values
        avg_load   = float(np.mean(loads))
        max_load   = float(np.max(loads))
        load_factor = round(avg_load / max_load * 100, 2)

        return {
            'threshold':    round(self.peak_threshold, 4),
            'max_load':     round(max_load, 4),
            'avg_load':     round(avg_load, 4),
            'load_factor':  load_factor,
            'peak_to_avg':  round(max_load / avg_load, 4),
        }